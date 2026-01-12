from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from typing import List
from app.models import Recipe, RecipeCreate, RecipeUpdate
from app.services.storage import recipe_storage
from pydantic import ValidationError
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

class APIError(Exception):
    def __init__(self, status_code: int, message: str, details: dict = None):
        self.status_code = status_code
        self.message = message
        self.details = details or {}

def create_error_response(status_code: int, message: str, details: dict = None):
    """Create standardized error response"""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": True,
            "message": message,
            "details": details or {},
            "status_code": status_code
        }
    )

@router.get("/recipes")
def get_all_recipes():
    """Get all recipes with proper error handling"""
    try:
        recipes = recipe_storage.get_all_recipes()
        return {"recipes": recipes}
    except Exception as e:
        logger.error(f"Error fetching recipes: {str(e)}")
        return create_error_response(500, "Internal server error occurred")

@router.get("/recipes/{recipe_id}")
def get_recipe(recipe_id: str):
    """Get a specific recipe with validation"""
    try:
        if not recipe_id or not recipe_id.strip():
            return create_error_response(400, "Recipe ID cannot be empty")
        
        recipe = recipe_storage.get_recipe(recipe_id.strip())
        if not recipe:
            return create_error_response(404, f"Recipe with ID '{recipe_id}' not found")
        
        return recipe
    except Exception as e:
        logger.error(f"Error fetching recipe {recipe_id}: {str(e)}")
        return create_error_response(500, "Internal server error occurred")

@router.post("/recipes", status_code=status.HTTP_201_CREATED)
def create_recipe(recipe_data: RecipeCreate):
    """Create a new recipe with comprehensive validation"""
    try:
        # Additional business logic validation
        if len(recipe_data.ingredients) < 1:
            return create_error_response(422, "At least one ingredient is required")
        
        if len(recipe_data.instructions) < 1:
            return create_error_response(422, "At least one instruction step is required")
        
        # Check for duplicate titles (business rule)
        existing_recipes = recipe_storage.get_all_recipes()
        for existing in existing_recipes:
            if existing.title.lower() == recipe_data.title.lower():
                return create_error_response(409, f"Recipe with title '{recipe_data.title}' already exists")
        
        new_recipe = recipe_storage.create_recipe(recipe_data)
        return new_recipe
        
    except ValidationError as e:
        error_details = {}
        for error in e.errors():
            field = " -> ".join(str(x) for x in error["loc"])
            error_details[field] = error["msg"]
        
        return create_error_response(422, "Validation failed", error_details)
    
    except Exception as e:
        logger.error(f"Error creating recipe: {str(e)}")
        return create_error_response(500, "Internal server error occurred")

@router.put("/recipes/{recipe_id}")
def update_recipe(recipe_id: str, recipe_data: RecipeUpdate):
    """Update an existing recipe with validation"""
    try:
        if not recipe_id or not recipe_id.strip():
            return create_error_response(400, "Recipe ID cannot be empty")
        
        # Check if recipe exists
        existing_recipe = recipe_storage.get_recipe(recipe_id.strip())
        if not existing_recipe:
            return create_error_response(404, f"Recipe with ID '{recipe_id}' not found")
        
        # Check for duplicate titles (excluding current recipe)
        all_recipes = recipe_storage.get_all_recipes()
        for recipe in all_recipes:
            if recipe.id != recipe_id and recipe.title.lower() == recipe_data.title.lower():
                return create_error_response(409, f"Recipe with title '{recipe_data.title}' already exists")
        
        updated_recipe = recipe_storage.update_recipe(recipe_id.strip(), recipe_data)
        return updated_recipe
        
    except ValidationError as e:
        error_details = {}
        for error in e.errors():
            field = " -> ".join(str(x) for x in error["loc"])
            error_details[field] = error["msg"]
        
        return create_error_response(422, "Validation failed", error_details)
    
    except Exception as e:
        logger.error(f"Error updating recipe {recipe_id}: {str(e)}")
        return create_error_response(500, "Internal server error occurred")

@router.delete("/recipes/{recipe_id}")
def delete_recipe(recipe_id: str):
    """Delete a recipe with proper validation"""
    try:
        if not recipe_id or not recipe_id.strip():
            return create_error_response(400, "Recipe ID cannot be empty")
        
        success = recipe_storage.delete_recipe(recipe_id.strip())
        if not success:
            return create_error_response(404, f"Recipe with ID '{recipe_id}' not found")
        
        return {"message": "Recipe deleted successfully", "id": recipe_id}
    
    except Exception as e:
        logger.error(f"Error deleting recipe {recipe_id}: {str(e)}")
        return create_error_response(500, "Internal server error occurred")

@router.get("/recipes/search/{query}")
def search_recipes(query: str):
    """Search recipes with validation"""
    try:
        if not query or not query.strip():
            return create_error_response(400, "Search query cannot be empty")
        
        if len(query.strip()) < 2:
            return create_error_response(400, "Search query must be at least 2 characters long")
        
        results = recipe_storage.search_recipes(query.strip())
        return {"recipes": results, "query": query.strip(), "count": len(results)}
    
    except Exception as e:
        logger.error(f"Error searching recipes with query '{query}': {str(e)}")
        return create_error_response(500, "Internal server error occurred")
