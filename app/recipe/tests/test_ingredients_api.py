from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from django.urls import reverse
from core.models import Ingredient, Recipe
from recipe.serializers import IngredientSerializer

INGREDIENT_URL = reverse("recipe:ingredient-list")


class PublicIngredientsAPITests(TestCase):
    """Test publicly available ingredients"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required to get ingredients"""
        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsAPITests(TestCase):
    """Test the private ingredients API"""

    def setUp(self):

        self.user = get_user_model().objects.create_user(
            email="test@o2.pl",
            password="haslo123",
            name="Mike"
        )

        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredient_list(self):
        """test retrieving ingredients"""
        Ingredient.objects.create(
            user=self.user,
            name="Cucumber"
        )
        Ingredient.objects.create(
            user=self.user,
            name="Tomato"
        )

        res = self.client.get(INGREDIENT_URL)
        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.data, serializer.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_limit_ingredients(self):
        """Test that single user retrieve only
         created by himself ingredients"""
        user2 = get_user_model().objects.create_user(
            email="other@o2.pl",
            password='pass12345'
        )
        Ingredient.objects.create(
            user=user2,
            name="Cucumber"
        )
        ingredient = Ingredient.objects.create(
            user=self.user,
            name='Tomato'
        )

        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data[0]['name'], ingredient.name)

    def test_creating_ingredient_successful(self):
        """Test creating a new ingredient"""
        payload = {
            "name": 'TestIngredient'
        }

        self.client.post(INGREDIENT_URL, payload)

        exists = Ingredient.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()

        self.assertTrue(exists)

    def test_creating_ingredients_invalid(self):
        """Test creating ingredient invalid fails"""
        payload = {
            "name": ''
        }

        res = self.client.post(INGREDIENT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieving_ingredient_assigned_to_recipes(self):
        """Test retrieving only ingredient assigned to recipes"""
        ingredient1 = Ingredient.objects.create(user=self.user, name='Ig1')
        ingredient2 = Ingredient.objects.create(user=self.user, name='Ig2')
        recipe = Recipe.objects.create(
            title='Title',
            time_minutes=10,
            price=9.99,
            user=self.user
        )
        recipe.ingredients.add(ingredient1)

        res = self.client.get(INGREDIENT_URL, {'assigned_only': 1})

        serializer1 = IngredientSerializer(ingredient1)
        serializer2 = IngredientSerializer(ingredient2)

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)
