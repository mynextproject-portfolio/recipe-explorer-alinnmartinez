"""
Comprehensive API validation and error handling tests.
Tests all endpoints with various error scenarios and edge cases.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.storage import recipe_storage

@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)

@pytest.fixture
def clean_storage():
    """Clear storage before each test"""
    recipe_storage.clear_all()
    yield
    recipe_storage.clear_all()

@pytest.fixture
def valid_recipe_data():
    return {
        "title": "Test Recipe",
        "description": "A test recipe description",
        "cuisine": "Italian",
        "ingredients": ["ingredient 1", "ingredient 2"],
        "instructions": ["step 1", "step 2"],
        "tags": ["test", "sample"]
    }

@pytest.fixture
def created_recipe(client, clean_storage, valid_recipe_data):
    """Create a recipe for testing"""
    response = client.post("/api/recipes", json=valid_recipe_data)
    return response.json()

class TestHealthAndBasics:
    """Test basic functionality and health checks"""
    
    def test_health_check(self, client):
        """Health endpoint returns correct response"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

class TestGetRecipes:
    """Test GET /api/recipes endpoint"""
    
    def test_get_all_recipes_empty(self, client, clean_storage):
        """GET all recipes returns empty list when no recipes exist"""
        response = client.get("/api/recipes")
        assert response.status_code == 200
        data = response.json()
        assert "recipes" in data
        assert isinstance(data["recipes"], list)
        assert len(data["recipes"]) == 0

    def test_get_all_recipes_with_data(self, client, created_recipe):
        """GET all recipes returns correct data structure"""
        response = client.get("/api/recipes")
        assert response.status_code == 200
        data = response.json()
        assert "recipes" in data
        assert len(data["recipes"]) == 1
        
        recipe = data["recipes"][0]
        assert "id" in recipe
        assert "title" in recipe
        assert "cuisine" in recipe
        assert isinstance(recipe["ingredients"], list)
        assert isinstance(recipe["instructions"], list)

class TestGetSingleRecipe:
    """Test GET /api/recipes/{id} endpoint"""
    
    def test_get_recipe_success(self, client, created_recipe):
        """GET single recipe returns correct data"""
        recipe_id = created_recipe["id"]
        response = client.get(f"/api/recipes/{recipe_id}")
        assert response.status_code == 200
        
        recipe = response.json()
        assert recipe["id"] == recipe_id
        assert "title" in recipe
        assert "cuisine" in recipe

    def test_get_recipe_not_found(self, client, clean_storage):
        """GET non-existent recipe returns 404"""
        response = client.get("/api/recipes/non-existent-id")
        assert response.status_code == 404
        
        error = response.json()
        assert error["error"] is True
        assert "not found" in error["message"]

    def test_get_recipe_empty_id(self, client):
        """GET with empty ID returns 400"""
        response = client.get("/api/recipes/ ")
        assert response.status_code == 400

class TestCreateRecipe:
    """Test POST /api/recipes endpoint"""
    
    def test_create_recipe_success(self, client, clean_storage, valid_recipe_data):
        """POST valid recipe returns 201 and correct data"""
        response = client.post("/api/recipes", json=valid_recipe_data)
        assert response.status_code == 201
        
        recipe = response.json()
        assert "id" in recipe
        assert recipe["title"] == valid_recipe_data["title"]
        assert recipe["cuisine"] == valid_recipe_data["cuisine"]
        assert isinstance(recipe["ingredients"], list)
        assert isinstance(recipe["instructions"], list)

    def test_create_recipe_missing_title(self, client, clean_storage):
        """POST without title returns 422"""
        invalid_data = {
            "description": "Test description",
            "cuisine": "Italian",
            "ingredients": ["ingredient 1"],
            "instructions": ["step 1"]
        }
        response = client.post("/api/recipes", json=invalid_data)
        assert response.status_code == 422

    def test_create_recipe_empty_title(self, client, clean_storage):
        """POST with empty title returns 422"""
        invalid_data = {
            "title": "",
            "description": "Test description", 
            "cuisine": "Italian",
            "ingredients": ["ingredient 1"],
            "instructions": ["step 1"]
        }
        response = client.post("/api/recipes", json=invalid_data)
        assert response.status_code == 422
        
        error = response.json()
        assert error["error"] is True
        assert "validation" in error["message"].lower()

    def test_create_recipe_no_ingredients(self, client, clean_storage):
        """POST without ingredients returns 422"""
        invalid_data = {
            "title": "Test Recipe",
            "description": "Test description",
            "cuisine": "Italian", 
            "ingredients": [],
            "instructions": ["step 1"]
        }
        response = client.post("/api/recipes", json=invalid_data)
        assert response.status_code == 422

    def test_create_recipe_no_instructions(self, client, clean_storage):
        """POST without instructions returns 422"""
        invalid_data = {
            "title": "Test Recipe",
            "description": "Test description",
            "cuisine": "Italian",
            "ingredients": ["ingredient 1"],
            "instructions": []
        }
        response = client.post("/api/recipes", json=invalid_data)
        assert response.status_code == 422

    def test_create_recipe_duplicate_title(self, client, created_recipe, valid_recipe_data):
        """POST with duplicate title returns 409"""
        response = client.post("/api/recipes", json=valid_recipe_data)
        assert response.status_code == 409
        
        error = response.json()
        assert error["error"] is True
        assert "already exists" in error["message"]

    def test_create_recipe_title_too_long(self, client, clean_storage):
        """POST with title too long returns 422"""
        invalid_data = {
            "title": "x" * 201,  # Exceeds MAX_TITLE_LENGTH
            "description": "Test description",
            "cuisine": "Italian",
            "ingredients": ["ingredient 1"],
            "instructions": ["step 1"]
        }
        response = client.post("/api/recipes", json=invalid_data)
        assert response.status_code == 422

class TestUpdateRecipe:
    """Test PUT /api/recipes/{id} endpoint"""
    
    def test_update_recipe_success(self, client, created_recipe):
        """PUT valid update returns 200 and updated data"""
        recipe_id = created_recipe["id"]
        update_data = {
            "title": "Updated Recipe",
            "description": "Updated description",
            "cuisine": "French",
            "ingredients": ["new ingredient"],
            "instructions": ["new step"],
            "tags": ["updated"]
        }
        
        response = client.put(f"/api/recipes/{recipe_id}", json=update_data)
        assert response.status_code == 200
        
        recipe = response.json()
        assert recipe["title"] == "Updated Recipe"
        assert recipe["cuisine"] == "French"

    def test_update_recipe_not_found(self, client, clean_storage):
        """PUT non-existent recipe returns 404"""
        update_data = {
            "title": "Updated Recipe",
            "description": "Updated description",
            "cuisine": "French",
            "ingredients": ["ingredient"],
            "instructions": ["step"]
        }
        
        response = client.put("/api/recipes/non-existent", json=update_data)
        assert response.status_code == 404

    def test_update_recipe_invalid_data(self, client, created_recipe):
        """PUT with invalid data returns 422"""
        recipe_id = created_recipe["id"]
        invalid_data = {
            "title": "",  # Empty title
            "description": "Updated description",
            "cuisine": "French",
            "ingredients": [],  # Empty ingredients
            "instructions": ["step"]
        }
        
        response = client.put(f"/api/recipes/{recipe_id}", json=invalid_data)
        assert response.status_code == 422

class TestDeleteRecipe:
    """Test DELETE /api/recipes/{id} endpoint"""
    
    def test_delete_recipe_success(self, client, created_recipe):
        """DELETE existing recipe returns 200"""
        recipe_id = created_recipe["id"]
        response = client.delete(f"/api/recipes/{recipe_id}")
        assert response.status_code == 200
        
        result = response.json()
        assert "message" in result
        assert recipe_id in result["id"]

    def test_delete_recipe_not_found(self, client, clean_storage):
        """DELETE non-existent recipe returns 404"""
        response = client.delete("/api/recipes/non-existent")
        assert response.status_code == 404

    def test_delete_recipe_empty_id(self, client):
        """DELETE with empty ID returns 400"""
        response = client.delete("/api/recipes/ ")
        assert response.status_code == 400

class TestSearchRecipes:
    """Test GET /api/recipes/search/{query} endpoint"""
    
    def test_search_recipes_success(self, client, created_recipe):
        """Search returns correct results"""
        response = client.get("/api/recipes/search/Test")
        assert response.status_code == 200

        data = response.json()
        assert "recipes" in data
        assert "query" in data
        assert "total_count" in data
        assert data["query"] == "Test"

    def test_search_recipes_empty_query(self, client):
        """Search with empty query returns 400"""
        response = client.get("/api/recipes/search/ ")
        assert response.status_code == 400

    def test_search_recipes_short_query(self, client):
        """Search with too short query returns 400"""
        response = client.get("/api/recipes/search/x")
        assert response.status_code == 400

class TestErrorResponseFormat:
    """Test error response format consistency"""
    
    def test_error_response_structure(self, client, clean_storage):
        """All error responses follow the same structure"""
        response = client.get("/api/recipes/non-existent")
        assert response.status_code == 404
        
        error = response.json()
        assert "error" in error
        assert "message" in error
        assert "status_code" in error
        assert error["error"] is True
        assert isinstance(error["message"], str)
        assert error["status_code"] == 404

    def test_validation_error_details(self, client, clean_storage):
        """Validation errors include field details"""
        invalid_data = {
            "title": "",
            "description": "Test",
            "cuisine": "Italian",
            "ingredients": [],
            "instructions": []
        }
        
        response = client.post("/api/recipes", json=invalid_data)
        assert response.status_code == 422
        
        error = response.json()
        assert "details" in error
        assert isinstance(error["details"], dict)