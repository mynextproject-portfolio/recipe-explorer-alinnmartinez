from pydantic import BaseModel, ConfigDict, Field, field_serializer
from datetime import datetime
from typing import List, Optional
from enum import Enum
import uuid

# Constants
MAX_TITLE_LENGTH = 200
MAX_INGREDIENTS = 50

class Recipe(BaseModel):
    model_config = ConfigDict()
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str 
    description: str
    ingredients: List[str]
    instructions: List[str]  # Changed from str to List[str]
    tags: List[str] = Field(default_factory=list)
    cuisine: str  # New field for regional/cuisine types
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, dt: datetime, _info):
        return dt.isoformat()


class RecipeCreate(BaseModel):
    title: str
    description: str
    ingredients: List[str]
    instructions: List[str]  # Changed from str to List[str]
    tags: List[str] = Field(default_factory=list)
    cuisine: str  # New field


class RecipeUpdate(BaseModel):
    title: str
    description: str
    ingredients: List[str]
    instructions: List[str]  # Changed from str to List[str]
    tags: List[str]
    cuisine: str  # New field

# Test data - hardcoded recipe for testing
SAMPLE_RECIPE = Recipe(
    title="Classic Spaghetti Carbonara",
    description="A traditional Italian pasta dish with eggs, cheese, and pancetta",
    ingredients=[
        "400g spaghetti",
        "200g pancetta or guanciale, diced",
        "4 large eggs",
        "100g Pecorino Romano cheese, grated",
        "2 cloves garlic, minced",
        "Black pepper to taste",
        "Salt for pasta water"
    ],
    instructions=[
        "Bring a large pot of salted water to boil",
        "Cook spaghetti according to package directions until al dente",
        "While pasta cooks, fry pancetta in a large pan until crispy",
        "In a bowl, whisk together eggs, cheese, and black pepper",
        "Drain pasta, reserving 1 cup pasta water",
        "Add hot pasta to the pan with pancetta",
        "Remove from heat and quickly mix in egg mixture",
        "Add pasta water gradually until creamy",
        "Serve immediately with extra cheese and pepper"
    ],
    tags=["Italian", "pasta", "traditional"],
    cuisine="Italian"
)
