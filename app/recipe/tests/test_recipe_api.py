from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from core.models import Recipe, Tag, Ingredient
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


RECIPES_URL = reverse("recipe:recipe-list")


def detail_url(recipe_id):
    """Return recipe detail url"""
    return reverse("recipe:recipe-detail", args=[recipe_id])


def sample_tag(user, name='Main tag'):
    """Create and retrurns a sample tag"""
    return Tag.objects.create(
        user=user,
        name=name
    )


def sample_ingredient(user, name="Sample ingredient"):
    """Create and retrurns a sample tag"""
    return Ingredient.objects.create(
        user=user,
        name=name
    )


def sample_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {
        'title': 'Default Title',
        'time_minutes': 10,
        'price': 10.00
    }
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeAPITests(TestCase):
    """Test publicly available recipes"""

    def setUp(self):
        self.client = APIClient()

    def test_unauth_retrieve_recipes(self):
        """Test that unauthicated user can get acces to recipes"""
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    """Test privatly available recipes """

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            'testmail@o2.pl',
            'haslo123'
        )

        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_recipe_list(self):
        """test"""
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_limit_recipes_to_user(self):
        """Test that recipes are only created by those user"""
        user2 = get_user_model().objects.\
            create_user("someuser@o2.pl", "pass123")

        sample_recipe(user=user2)
        sample_recipe(user=self.user)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)

    def test_view_recipe_detail(self):
        """Test viewing a recipe dettail"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.data, serializer.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_basic_recipe(self):
        """Test creating recipe"""
        payload = {
            'title': 'Some Tile',
            'price': 5.20,
            'time_minutes': 10,
        }

        res = self.client.post(RECIPES_URL, payload)

        recipe = Recipe.objects.get(id=res.data['id'])

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        """Test creating recipe with tags"""

        t1 = sample_tag(self.user)
        t2 = sample_tag(self.user, name="Another")

        payload = {
            'title': 'Some Title',
            'time_minutes': 10,
            'price': 20,
            'tags': [t1.id, t2.id]
        }

        res = self.client.post(RECIPES_URL, payload)
        recipe = Recipe.objects.get(id=res.data['id'])
        tags = recipe.tags.all()

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(tags.count(), 2)
        self.assertIn(t1, tags)
        self.assertIn(t2, tags)

    def test_create_recipe_with_ingredients(self):
        """Test creating recipe with ingredients"""
        ig1 = sample_ingredient(self.user)
        ig2 = sample_ingredient(self.user, "Chocolate")

        payload = {
            'title': 'Some title',
            'price': 20.2,
            'time_minutes': 10,
            'ingredients': [ig1.id, ig2.id]
        }

        res = self.client.post(RECIPES_URL, payload)
        recipe = Recipe.objects.get(id=res.data['id'])
        ingredients = recipe.ingredients.all()

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn(ig1, ingredients)
        self.assertIn(ig2, ingredients)
        self.assertEqual(ingredients.count(), 2)

    def test_partial_update_with_recipe(self):
        """Test updating a recipe with patch"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        new_tag = sample_tag(user=self.user, name="Some name")

        payload = {
            'title': 'Chicken',
            'tags': [new_tag.id]
        }

        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()

        self.assertEqual(recipe.title, payload['title'])
        tags = recipe.tags.all()
        self.assertEqual(len(tags), 1)
        self.assertIn(new_tag, tags)

    def test_full_update_recipe_self(self):
        """Test updating a recipe with put"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(self.user))

        payload = {
            'title': 'New title',
            'time_minutes': 25,
            'price': 12.22
        }
        url = detail_url(recipe.id)
        self.client.put(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.price, payload['price'])
        self.assertEqual(recipe.time_minutes, payload['time_minutes'])
        tags = recipe.tags.all()
        self.assertEqual(len(tags), 0)
