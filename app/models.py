from pydantic import BaseModel, ConfigDict, Field, field_validator, field_serializer
from datetime import datetime
from typing import List, Optional
from enum import Enum
import uuid
import re

# Constants
MAX_TITLE_LENGTH = 200
MAX_INGREDIENTS = 50
MAX_INSTRUCTIONS = 50
MAX_DESCRIPTION_LENGTH = 1000

class Recipe(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(..., min_length=1, max_length=MAX_TITLE_LENGTH)
    description: str = Field(..., min_length=1, max_length=MAX_DESCRIPTION_LENGTH)
    ingredients: List[str] = Field(..., min_length=1, max_length=MAX_INGREDIENTS)
    instructions: List[str] = Field(..., min_length=1, max_length=MAX_INSTRUCTIONS)
    tags: List[str] = Field(default_factory=list, max_length=20)
    cuisine: str = Field(..., min_length=1, max_length=50)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError('Title cannot be empty')
        if len(v.strip()) > MAX_TITLE_LENGTH:
            raise ValueError(f'Title must be {MAX_TITLE_LENGTH} characters or less')
        return v.strip()

    @field_validator('ingredients')
    @classmethod
    def validate_ingredients(cls, v):
        if not v:
            raise ValueError('At least one ingredient is required')
        if len(v) > MAX_INGREDIENTS:
            raise ValueError(f'Maximum {MAX_INGREDIENTS} ingredients allowed')
        
        # Remove empty ingredients and validate each one
        clean_ingredients = []
        for ingredient in v:
            if ingredient and ingredient.strip():
                if len(ingredient.strip()) > 200:
                    raise ValueError('Each ingredient must be 200 characters or less')
                clean_ingredients.append(ingredient.strip())
        
        if not clean_ingredients:
            raise ValueError('At least one non-empty ingredient is required')
        return clean_ingredients

    @field_validator('instructions')
    @classmethod
    def validate_instructions(cls, v):
        if not v:
            raise ValueError('At least one instruction step is required')
        if len(v) > MAX_INSTRUCTIONS:
            raise ValueError(f'Maximum {MAX_INSTRUCTIONS} instruction steps allowed')
        
        # Remove empty instructions and validate each one
        clean_instructions = []
        for instruction in v:
            if instruction and instruction.strip():
                if len(instruction.strip()) > 500:
                    raise ValueError('Each instruction step must be 500 characters or less')
                clean_instructions.append(instruction.strip())
        
        if not clean_instructions:
            raise ValueError('At least one non-empty instruction step is required')
        return clean_instructions

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        if not v:
            return []
        
        clean_tags = []
        for tag in v:
            if tag and tag.strip():
                clean_tag = re.sub(r'[^a-zA-Z0-9\s\-]', '', tag.strip())
                if len(clean_tag) > 30:
                    raise ValueError('Each tag must be 30 characters or less')
                if clean_tag:
                    clean_tags.append(clean_tag.lower())
        
        # Remove duplicates while preserving order
        seen = set()
        unique_tags = []
        for tag in clean_tags:
            if tag not in seen:
                seen.add(tag)
                unique_tags.append(tag)
        
        return unique_tags

    @field_validator('cuisine')
    @classmethod
    def validate_cuisine(cls, v):
        if not v or not v.strip():
            raise ValueError('Cuisine cannot be empty')
        clean_cuisine = re.sub(r'[^a-zA-Z\s]', '', v.strip())
        if not clean_cuisine:
            raise ValueError('Cuisine must contain only letters and spaces')
        return clean_cuisine.title()

    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, dt: datetime, _info):
        return dt.isoformat()


class RecipeCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    
    title: str = Field(..., min_length=1, max_length=MAX_TITLE_LENGTH)
    description: str = Field(..., min_length=1, max_length=MAX_DESCRIPTION_LENGTH)
    ingredients: List[str] = Field(..., min_length=1, max_length=MAX_INGREDIENTS)
    instructions: List[str] = Field(..., min_length=1, max_length=MAX_INSTRUCTIONS)
    tags: List[str] = Field(default_factory=list, max_length=20)
    cuisine: str = Field(..., min_length=1, max_length=50)

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError('Title cannot be empty')
        if len(v.strip()) > MAX_TITLE_LENGTH:
            raise ValueError(f'Title must be {MAX_TITLE_LENGTH} characters or less')
        return v.strip()

    @field_validator('ingredients')
    @classmethod
    def validate_ingredients(cls, v):
        if not v:
            raise ValueError('At least one ingredient is required')
        if len(v) > MAX_INGREDIENTS:
            raise ValueError(f'Maximum {MAX_INGREDIENTS} ingredients allowed')
        
        clean_ingredients = []
        for ingredient in v:
            if ingredient and ingredient.strip():
                if len(ingredient.strip()) > 200:
                    raise ValueError('Each ingredient must be 200 characters or less')
                clean_ingredients.append(ingredient.strip())
        
        if not clean_ingredients:
            raise ValueError('At least one non-empty ingredient is required')
        return clean_ingredients

    @field_validator('instructions')
    @classmethod
    def validate_instructions(cls, v):
        if not v:
            raise ValueError('At least one instruction step is required')
        if len(v) > MAX_INSTRUCTIONS:
            raise ValueError(f'Maximum {MAX_INSTRUCTIONS} instruction steps allowed')
        
        clean_instructions = []
        for instruction in v:
            if instruction and instruction.strip():
                if len(instruction.strip()) > 500:
                    raise ValueError('Each instruction step must be 500 characters or less')
                clean_instructions.append(instruction.strip())
        
        if not clean_instructions:
            raise ValueError('At least one non-empty instruction step is required')
        return clean_instructions

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        if not v:
            return []
        
        clean_tags = []
        for tag in v:
            if tag and tag.strip():
                clean_tag = re.sub(r'[^a-zA-Z0-9\s\-]', '', tag.strip())
                if len(clean_tag) > 30:
                    raise ValueError('Each tag must be 30 characters or less')
                if clean_tag:
                    clean_tags.append(clean_tag.lower())
        
        seen = set()
        unique_tags = []
        for tag in clean_tags:
            if tag not in seen:
                seen.add(tag)
                unique_tags.append(tag)
        
        return unique_tags

    @field_validator('cuisine')
    @classmethod
    def validate_cuisine(cls, v):
        if not v or not v.strip():
            raise ValueError('Cuisine cannot be empty')
        clean_cuisine = re.sub(r'[^a-zA-Z\s]', '', v.strip())
        if not clean_cuisine:
            raise ValueError('Cuisine must contain only letters and spaces')
        return clean_cuisine.title()


class RecipeUpdate(RecipeCreate):
    pass


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
    tags=["italian", "pasta", "traditional"],
    cuisine="Italian"
)
