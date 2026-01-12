from typing import List, Optional
from app.models import Recipe, RecipeCreate, RecipeUpdate, SAMPLE_RECIPE
from datetime import datetime
import copy

class RecipeStorage:
    def __init__(self):
        # Initialize with the sample recipe
        self.recipes = [SAMPLE_RECIPE]

    def get_all_recipes(self) -> List[Recipe]:
        """Get all recipes"""
        return self.recipes.copy()

    def get_recipe(self, recipe_id: str) -> Optional[Recipe]:
        """Get a recipe by ID"""
        for recipe in self.recipes:
            if recipe.id == recipe_id:
                return recipe
        return None

    def create_recipe(self, recipe_data: RecipeCreate) -> Recipe:
        """Create a new recipe"""
        recipe = Recipe(
            title=recipe_data.title,
            description=recipe_data.description,
            cuisine=recipe_data.cuisine,
            ingredients=recipe_data.ingredients,
            instructions=recipe_data.instructions,
            tags=recipe_data.tags
        )
        self.recipes.append(recipe)
        return recipe

    def update_recipe(self, recipe_id: str, recipe_data: RecipeUpdate) -> Optional[Recipe]:
        """Update an existing recipe"""
        for i, recipe in enumerate(self.recipes):
            if recipe.id == recipe_id:
                # Update fields
                recipe.title = recipe_data.title
                recipe.description = recipe_data.description
                recipe.cuisine = recipe_data.cuisine
                recipe.ingredients = recipe_data.ingredients
                recipe.instructions = recipe_data.instructions
                recipe.tags = recipe_data.tags
                recipe.updated_at = datetime.now()
                return recipe
        return None

    def delete_recipe(self, recipe_id: str) -> bool:
        """Delete a recipe"""
        for i, recipe in enumerate(self.recipes):
            if recipe.id == recipe_id:
                del self.recipes[i]
                return True
        return False

    def search_recipes(self, query: str) -> List[Recipe]:
        """Search recipes by title, ingredients, or tags"""
        query = query.lower()
        results = []
        for recipe in self.recipes:
            if (query in recipe.title.lower() or
                any(query in ingredient.lower() for ingredient in recipe.ingredients) or
                any(query in tag.lower() for tag in recipe.tags) or
                query in recipe.cuisine.lower()):
                results.append(recipe)
        return results

    def clear_all(self):
        """Clear all recipes (for testing)"""
        self.recipes = []

# Global instance
recipe_storage = RecipeStorage()
