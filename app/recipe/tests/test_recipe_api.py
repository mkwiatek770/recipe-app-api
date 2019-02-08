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