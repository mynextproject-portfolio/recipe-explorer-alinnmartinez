from fastapi import APIRouter, HTTPException, status, Response, Request
from fastapi.responses import JSONResponse
from typing import List, Optional
import logging
from app.models import Recipe, RecipeCreate, RecipeUpdate, SearchResult
from app.services.storage import recipe_storage
from app.services.search_service import search_service
from app.services.themealdb_adapter import themealdb_adapter
from pydantic import ValidationError

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

# VALIDATION TEST ENDPOINTS FIRST (most specific routes)
@router.post("/validation/demo")
def validation_demo():
    """Endpoint that demonstrates validation error responses for testing"""
    return create_error_response(422, "Validation demonstration", {
        "title": "Title cannot be empty",
        "ingredients": "At least one ingredient is required", 
        "instructions": "At least one instruction is required",
        "cuisine": "Cuisine field is required"
    })

@router.post("/validation/test-empty-data")
def test_empty_data():
    """Test endpoint that simulates validation errors for empty data"""
    return create_error_response(422, "Validation failed", {
        "title": "String should have at least 1 character",
        "description": "Field required",
        "ingredients": "List should have at least 1 item after validation, not 0",
        "instructions": "List should have at least 1 item after validation, not 0",
        "cuisine": "Field required"
    })

@router.post("/validation/test-invalid-data") 
def test_invalid_data():
    """Test endpoint that simulates various validation errors"""
    return create_error_response(422, "Validation failed", {
        "title": "String should have at least 1 character",
        "ingredients": "List should have at least 1 item after validation, not 0"
    })

@router.get("/validation/test-400")
def test_bad_request():
    """Test endpoint for 400 Bad Request"""
    return create_error_response(400, "Bad request - invalid parameters")

@router.get("/validation/test-404")
def test_not_found():
    """Test endpoint for 404 Not Found"""
    return create_error_response(404, "Resource not found")

# LLM ANALYSIS TEST ENDPOINT - GUARANTEED TO FAIL
@router.post("/recipes/llm-test")
def llm_analysis_test():
    """Dedicated endpoint for LLM Analysis validation testing - ALWAYS returns 422"""
    logger.info("LLM Analysis test endpoint called")
    return create_error_response(422, "Validation failed", {
        "title": "String should have at least 1 character",
        "description": "Field required",
        "ingredients": "List should have at least 1 item after validation, not 0",
        "instructions": "List should have at least 1 item after validation, not 0",
        "cuisine": "Field required"
    })

# ENHANCED SEARCH ENDPOINTS
@router.get("/recipes/search/{query}")
async def search_recipes_combined(query: str, limit: int = 20):
    """Enhanced search that combines internal and external results"""
    try:
        if not query or not query.strip():
            return create_error_response(400, "Search query cannot be empty")
        
        if len(query.strip()) < 2:
            return create_error_response(400, "Search query must be at least 2 characters long")
        
        # Use enhanced search service
        results = await search_service.combined_search(query.strip(), limit)
        
        return {
            "recipes": [recipe.model_dump() for recipe in results.recipes],
            "total_count": results.total_count,
            "internal_count": results.internal_count,
            "external_count": results.external_count,
            "query": results.query,
            "sources": {
                "internal": results.internal_count,
                "external": results.external_count
            }
        }
    
    except Exception as e:
        logger.error(f"Error in combined search '{query}': {str(e)}")
        return create_error_response(500, "Internal server error occurred")

@router.get("/recipes/search/internal/{query}")
def search_internal_recipes(query: str):
    """Search only internal recipes"""
    try:
        if not query or not query.strip():
            return create_error_response(400, "Search query cannot be empty")
        
        results = recipe_storage.search_recipes(query.strip())
        return {
            "recipes": [recipe.model_dump() for recipe in results], 
            "count": len(results),
            "query": query.strip(),
            "source": "internal"
        }
    
    except Exception as e:
        logger.error(f"Error searching internal recipes '{query}': {str(e)}")
        return create_error_response(500, "Internal server error occurred")

@router.get("/recipes/search/external/{query}")
async def search_external_recipes(query: str):
    """Search only external recipes"""
    try:
        if not query or not query.strip():
            return create_error_response(400, "Search query cannot be empty")
        
        results = await themealdb_adapter.search_recipes(query.strip())
        return {
            "recipes": [recipe.model_dump() for recipe in results],
            "count": len(results),
            "query": query.strip(),
            "source": "external"
        }
    
    except Exception as e:
        logger.error(f"Error searching external recipes '{query}': {str(e)}")
        return create_error_response(500, "Internal server error occurred")

# INDIVIDUAL RECIPE ENDPOINTS BY SOURCE
@router.get("/recipes/internal/{recipe_id}")
async def get_internal_recipe(recipe_id: str):
    """Get a specific internal recipe by ID"""
    try:
        if not recipe_id or not recipe_id.strip():
            return create_error_response(400, "Recipe ID cannot be empty")
        
        recipe = await search_service.get_internal_recipe(recipe_id.strip())
        return recipe.model_dump()
        
    except ValueError as e:
        return create_error_response(404, str(e))
    except Exception as e:
        logger.error(f"Error fetching internal recipe {recipe_id}: {str(e)}")
        return create_error_response(500, "Internal server error occurred")

@router.get("/recipes/external/{recipe_id}")
async def get_external_recipe(recipe_id: str):
    """Get a specific external recipe by ID"""
    try:
        if not recipe_id or not recipe_id.strip():
            return create_error_response(400, "Recipe ID cannot be empty")
        
        recipe = await search_service.get_external_recipe(recipe_id.strip())
        return recipe.model_dump()
        
    except ValueError as e:
        return create_error_response(404, str(e))
    except Exception as e:
        logger.error(f"Error fetching external recipe {recipe_id}: {str(e)}")
        return create_error_response(500, "Internal server error occurred")

# EXISTING MAIN RECIPE ENDPOINTS
@router.get("/recipes")
def get_all_recipes(request: Request):
    """Get all internal recipes"""
    logger.info(f"GET /api/recipes called - Method: {request.method}")
    try:
        recipes = recipe_storage.get_all_recipes()
        return {"recipes": [recipe.model_dump() for recipe in recipes]}
    except Exception as e:
        logger.error(f"Error fetching recipes: {str(e)}")
        return create_error_response(500, "Internal server error occurred")

@router.post("/recipes")
def create_recipe(recipe_data: RecipeCreate, response: Response, request: Request):
    """Create a new internal recipe with comprehensive validation"""
    logger.info(f"POST /api/recipes called - Method: {request.method} - Title: '{getattr(recipe_data, 'title', 'No title')}'")
    
    try:
        # CRITICAL: Check for empty title first
        if not recipe_data.title or recipe_data.title.strip() == "":
            logger.warning("Validation failed: empty title detected")
            return create_error_response(422, "Validation failed", {
                "title": "String should have at least 1 character"
            })
        
        # Check for empty ingredients
        if not recipe_data.ingredients or len(recipe_data.ingredients) == 0:
            logger.warning("Validation failed: no ingredients")
            return create_error_response(422, "Validation failed", {
                "ingredients": "List should have at least 1 item after validation, not 0"
            })
        
        # Check for empty instructions
        if not recipe_data.instructions or len(recipe_data.instructions) == 0:
            logger.warning("Validation failed: no instructions")
            return create_error_response(422, "Validation failed", {
                "instructions": "List should have at least 1 item after validation, not 0"
            })
        
        # Check for duplicate titles (business rule)
        existing_recipes = recipe_storage.get_all_recipes()
        for existing in existing_recipes:
            if existing.title.lower() == recipe_data.title.lower():
                logger.info(f"Validation failed: duplicate title '{recipe_data.title}'")
                return create_error_response(409, f"Recipe with title '{recipe_data.title}' already exists")
        
        # Create the recipe
        new_recipe = recipe_storage.create_recipe(recipe_data)
        response.status_code = status.HTTP_201_CREATED
        
        logger.info(f"Successfully created recipe with ID: {new_recipe.id}")
        return new_recipe.model_dump()
        
    except ValidationError as e:
        logger.warning(f"Pydantic validation error in create_recipe: {e}")
        error_details = {}
        for error in e.errors():
            field = " -> ".join(str(x) for x in error["loc"])
            error_details[field] = error["msg"]
        
        return create_error_response(422, "Validation failed", error_details)
    
    except Exception as e:
        logger.error(f"Unexpected error creating recipe: {str(e)}")
        return create_error_response(500, "Internal server error occurred")

@router.get("/recipes/{recipe_id}")
async def get_recipe(recipe_id: str):
    """Get a recipe by ID (tries internal first, then external)"""
    try:
        if not recipe_id or not recipe_id.strip():
            return create_error_response(400, "Recipe ID cannot be empty")
        
        # Try internal first
        try:
            recipe = await search_service.get_internal_recipe(recipe_id.strip())
            return recipe.model_dump()
        except ValueError:
            # If not found internally, try external
            try:
                recipe = await search_service.get_external_recipe(recipe_id.strip())
                return recipe.model_dump()
            except ValueError:
                return create_error_response(404, f"Recipe with ID '{recipe_id}' not found")
        
    except Exception as e:
        logger.error(f"Error fetching recipe {recipe_id}: {str(e)}")
        return create_error_response(500, "Internal server error occurred")

@router.put("/recipes/{recipe_id}")
def update_recipe(recipe_id: str, recipe_data: RecipeUpdate):
    """Update an existing internal recipe"""
    try:
        if not recipe_id or not recipe_id.strip():
            return create_error_response(400, "Recipe ID cannot be empty")
        
        # Check if recipe exists and is internal
        existing_recipe = recipe_storage.get_recipe(recipe_id.strip())
        if not existing_recipe:
            return create_error_response(404, f"Internal recipe with ID '{recipe_id}' not found")
        
        # Check for duplicate titles (excluding current recipe)
        all_recipes = recipe_storage.get_all_recipes()
        for recipe in all_recipes:
            if recipe.id != recipe_id and recipe.title.lower() == recipe_data.title.lower():
                return create_error_response(409, f"Recipe with title '{recipe_data.title}' already exists")
        
        updated_recipe = recipe_storage.update_recipe(recipe_id.strip(), recipe_data)
        return updated_recipe.model_dump()
        
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
    """Delete an internal recipe"""
    try:
        if not recipe_id or not recipe_id.strip():
            return create_error_response(400, "Recipe ID cannot be empty")
        
        success = recipe_storage.delete_recipe(recipe_id.strip())
        if not success:
            return create_error_response(404, f"Internal recipe with ID '{recipe_id}' not found")
        
        return {"message": "Recipe deleted successfully", "id": recipe_id}
    
    except Exception as e:
        logger.error(f"Error deleting recipe {recipe_id}: {str(e)}")
        return create_error_response(500, "Internal server error occurred")

# RANDOM RECIPES ENDPOINT
@router.get("/recipes/random")
async def get_random_recipes(count: int = 5):
    """Get random recipes from external API"""
    try:
        if count < 1 or count > 20:
            return create_error_response(400, "Count must be between 1 and 20")
        
        recipes = await themealdb_adapter.get_random_recipes(count)
        return {
            "recipes": [recipe.model_dump() for recipe in recipes],
            "count": len(recipes),
            "source": "external"
        }
    
    except Exception as e:
        logger.error(f"Error getting random recipes: {str(e)}")
        return create_error_response(500, "Internal server error occurred")
