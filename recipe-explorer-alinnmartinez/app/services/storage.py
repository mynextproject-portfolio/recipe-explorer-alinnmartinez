class RecipeStorage:
    def __init__(self):
        self.recipes = []

    def clear_all(self):
        self.recipes.clear()

    # Other methods for RecipeStorage... 

import pytest
from app.services.storage import RecipeStorage

@pytest.fixture
def clean_storage():
    recipe_storage = RecipeStorage()
    recipe_storage.clear_all()
    return recipe_storage