import json
import uuid
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.models import Recipe, RecipeCreate, RecipeUpdate, RecipeSource

class RecipeStorage:
    def __init__(self, data_file: str = "data/recipes.json"):
        self.data_file = Path(data_file)
        self.data_file.parent.mkdir(exist_ok=True)
        self._recipes: Dict[str, Recipe] = {}
        self._load_data()

    def _load_data(self):
        """Load recipes from JSON file"""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    for recipe_dict in data:
                        # Ensure source field exists for backward compatibility
                        if 'source' not in recipe_dict:
                            recipe_dict['source'] = RecipeSource.INTERNAL
                        recipe = Recipe(**recipe_dict)
                        self._recipes[recipe.id] = recipe
            except Exception as e:
                print(f"Error loading recipes: {e}")

    def _save_data(self):
        """Save recipes to JSON file"""
        try:
            data = [recipe.model_dump() for recipe in self._recipes.values()]
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving recipes: {e}")

    def get_all_recipes(self) -> List[Recipe]:
        """Get all internal recipes"""
        return [recipe for recipe in self._recipes.values() if recipe.source == RecipeSource.INTERNAL]

    def get_recipe(self, recipe_id: str) -> Optional[Recipe]:
        """Get a specific internal recipe by ID"""
        recipe = self._recipes.get(recipe_id)
        if recipe and recipe.source == RecipeSource.INTERNAL:
            return recipe
        return None

    def create_recipe(self, recipe_data: RecipeCreate) -> Recipe:
        """Create a new internal recipe"""
        recipe_id = str(uuid.uuid4())
        now = datetime.now()
        
        recipe = Recipe(
            id=recipe_id,
            title=recipe_data.title,
            description=recipe_data.description,
            ingredients=recipe_data.ingredients,
            instructions=recipe_data.instructions,
            tags=recipe_data.tags,
            cuisine=recipe_data.cuisine,
            source=RecipeSource.INTERNAL,  # Always internal for created recipes
            created_at=now,
            updated_at=now
        )
        
        self._recipes[recipe_id] = recipe
        self._save_data()
        return recipe

    def update_recipe(self, recipe_id: str, recipe_data: RecipeUpdate) -> Optional[Recipe]:
        """Update an existing internal recipe"""
        recipe = self._recipes.get(recipe_id)
        if not recipe or recipe.source != RecipeSource.INTERNAL:
            return None

        # Update fields
        recipe.title = recipe_data.title
        recipe.description = recipe_data.description
        recipe.ingredients = recipe_data.ingredients
        recipe.instructions = recipe_data.instructions
        recipe.tags = recipe_data.tags
        recipe.cuisine = recipe_data.cuisine
        recipe.updated_at = datetime.now()

        self._save_data()
        return recipe

    def delete_recipe(self, recipe_id: str) -> bool:
        """Delete an internal recipe"""
        recipe = self._recipes.get(recipe_id)
        if recipe and recipe.source == RecipeSource.INTERNAL:
            del self._recipes[recipe_id]
            self._save_data()
            return True
        return False

    def search_recipes(self, query: str) -> List[Recipe]:
        """Search internal recipes by title, ingredients, or tags"""
        query_lower = query.lower()
        results = []
        
        for recipe in self._recipes.values():
            if recipe.source != RecipeSource.INTERNAL:
                continue
                
            if (query_lower in recipe.title.lower() or
                query_lower in recipe.description.lower() or
                any(query_lower in ingredient.lower() for ingredient in recipe.ingredients) or
                any(query_lower in tag.lower() for tag in recipe.tags) or
                query_lower in recipe.cuisine.lower()):
                results.append(recipe)
        
        return results

# Global instance
recipe_storage = RecipeStorage()
