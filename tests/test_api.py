"""
Basic smoke and contract tests for Recipe Explorer API.
These tests verify that endpoints exist and return expected status codes.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.storage import recipe_storage
from unittest.mock import patch, AsyncMock
from app.models import SearchResult, Recipe, RecipeSource
from unittest.mock import patch, AsyncMock
from app.models import SearchResult
from unittest.mock import patch, AsyncMock
from app.models import SearchResult
from unittest.mock import patch, AsyncMock
from unittest.mock import patch, AsyncMock
from app.models import SearchResult, Recipe, RecipeSource

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
def sample_recipe_data():
    return {
        "title": "Test Recipe",
        "description": "A test recipe",
        "cuisine": "Italian",
        "ingredients": ["ingredient 1", "ingredient 2"],
        "instructions": ["First, do step 1.", "Then, do step 2."],
        "tags": ["test", "sample"]
    }

def test_health_check(client):
    """Smoke test: API is running and responding"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_home_page_loads(client):
    """Smoke test: Home page renders without error"""
    response = client.get("/")
    assert response.status_code == 200
    assert "Recipe Explorer" in response.text

def test_get_all_recipes(client, clean_storage):
    """Contract test: GET /api/recipes returns correct structure"""
    response = client.get("/api/recipes")
    assert response.status_code == 200
    data = response.json()
    assert "recipes" in data
    assert isinstance(data["recipes"], list)

def test_create_and_get_recipe(client, clean_storage, sample_recipe_data):
    """Contract test: Create recipe and verify response structure"""
    # Create recipe - expect 201 for created resource
    create_response = client.post("/api/recipes", json=sample_recipe_data)
    assert create_response.status_code == 201  # Changed from 200 to 201
    
    recipe = create_response.json()
    assert "id" in recipe
    assert "title" in recipe
    assert "created_at" in recipe
    assert recipe["title"] == sample_recipe_data["title"]
    
    # Get recipe
    get_response = client.get(f"/api/recipes/{recipe['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == recipe["id"]

def test_recipe_not_found(client, clean_storage):
    """Contract test: Non-existent recipe returns 404"""
    response = client.get("/api/recipes/non-existent-id")
    assert response.status_code == 404

def test_recipe_pages_load(client, clean_storage, sample_recipe_data):
    """Smoke test: Recipe HTML pages load without error"""
    # Create a recipe first
    create_response = client.post("/api/recipes", json=sample_recipe_data)
    recipe_id = create_response.json()["id"]
    
    # Test recipe detail page
    response = client.get(f"/recipes/{recipe_id}")
    assert response.status_code == 200
    
    # Test new recipe form
    response = client.get("/recipes/new")
    assert response.status_code == 200
    
    # Test import page
    response = client.get("/import")
    assert response.status_code == 200
    @pytest.mark.asyncio
    async def test_search_recipes_query_param_success(client, clean_storage):
        """Test successful search with query parameter"""
        # Mock the search service response
        
        mock_recipe = Recipe(
            id="test_id",
            title="Test Recipe",
            description="A test recipe",
            cuisine="Italian",
            ingredients=["ingredient 1"],
            instructions=["step 1"],
            tags=["test"],
            source=RecipeSource.INTERNAL
        )
        
        mock_result = SearchResult(
            recipes=[mock_recipe],
            total_count=1,
            internal_count=1,
            external_count=0,
            query="test"
        )
        
        with patch('app.services.search_service.search_service.combined_search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_result
            
            response = client.get("/api/recipes/search?q=test&limit=10")
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response structure
            assert "recipes" in data
            assert "total_count" in data
            assert "internal_count" in data
            assert "external_count" in data
            assert "query" in data
            assert "sources" in data
            
            # Verify values
            assert data["total_count"] == 1
            assert data["internal_count"] == 1
            assert data["external_count"] == 0
            assert data["query"] == "test"
            assert len(data["recipes"]) == 1
            assert data["recipes"][0]["title"] == "Test Recipe"
            
            # Verify search service was called with correct parameters
            mock_search.assert_called_once_with("test", 10)

    @pytest.mark.asyncio
    async def test_search_recipes_query_param_default_limit(client, clean_storage):
        """Test search with default limit when not specified"""
        
        mock_result = SearchResult(
            recipes=[],
            total_count=0,
            internal_count=0,
            external_count=0,
            query="test"
        )
        
        with patch('app.services.search_service.search_service.combined_search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_result
            
            response = client.get("/api/recipes/search?q=test")
            
            assert response.status_code == 200
            # Verify default limit of 20 was used
            mock_search.assert_called_once_with("test", 20)

    def test_search_recipes_query_param_empty_query(client, clean_storage):
        """Test search with empty query returns 400"""
        response = client.get("/api/recipes/search?q=")
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"] is True
        assert data["message"] == "Search query cannot be empty"
        assert data["status_code"] == 400

    def test_search_recipes_query_param_missing_query(client, clean_storage):
        """Test search without query parameter returns validation error"""
        response = client.get("/api/recipes/search")
        
        # FastAPI will return 422 for missing required parameter
        assert response.status_code == 422

    def test_search_recipes_query_param_whitespace_query(client, clean_storage):
        """Test search with whitespace-only query returns 400"""
        response = client.get("/api/recipes/search?q=   ")
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"] is True
        assert data["message"] == "Search query cannot be empty"

    def test_search_recipes_query_param_short_query(client, clean_storage):
        """Test search with query too short returns 400"""
        response = client.get("/api/recipes/search?q=x")
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"] is True
        assert data["message"] == "Search query must be at least 2 characters long"

    @pytest.mark.asyncio
    async def test_search_recipes_query_param_with_custom_limit(client, clean_storage):
        """Test search with custom limit parameter"""
        
        mock_result = SearchResult(
            recipes=[],
            total_count=0,
            internal_count=0,
            external_count=0,
            query="chicken"
        )
        
        with patch('app.services.search_service.search_service.combined_search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_result
            
            response = client.get("/api/recipes/search?q=chicken&limit=5")
            
            assert response.status_code == 200
            # Verify custom limit was passed to search service
            mock_search.assert_called_once_with("chicken", 5)

    @pytest.mark.asyncio
    async def test_search_recipes_query_param_search_service_exception(client, clean_storage):
        """Test search when search service raises exception returns 500"""
        
        with patch('app.services.search_service.search_service.combined_search', new_callable=AsyncMock) as mock_search:
            mock_search.side_effect = Exception("Search service error")
            
            response = client.get("/api/recipes/search?q=test")
            
            assert response.status_code == 500
            data = response.json()
            assert data["error"] is True
            assert data["message"] == "Internal server error occurred"
            assert data["status_code"] == 500

    @pytest.mark.asyncio
    async def test_search_recipes_query_param_mixed_results(client, clean_storage):
        """Test search with both internal and external results"""
        
        internal_recipe = Recipe(
            id="internal_1",
            title="Internal Recipe",
            description="Internal recipe",
            cuisine="Italian",
            ingredients=["ingredient 1"],
            instructions=["step 1"],
            tags=["internal"],
            source=RecipeSource.INTERNAL
        )
        
        external_recipe = Recipe(
            id="ext_external_1",
            title="External Recipe",
            description="External recipe",
            cuisine="Mexican",
            ingredients=["ingredient 2"],
            instructions=["step 2"],
            tags=["external"],
            source=RecipeSource.EXTERNAL
        )
        
        mock_result = SearchResult(
            recipes=[internal_recipe, external_recipe],
            total_count=2,
            internal_count=1,
            external_count=1,
            query="recipe"
        )
        
        with patch('app.services.search_service.search_service.combined_search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_result
            
            response = client.get("/api/recipes/search?q=recipe")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["total_count"] == 2
            assert data["internal_count"] == 1
            assert data["external_count"] == 1
            assert data["sources"]["internal"] == 1
            assert data["sources"]["external"] == 1
            assert len(data["recipes"]) == 2

    def test_search_recipes_query_param_invalid_limit_type(client, clean_storage):
        """Test search with non-integer limit parameter"""
        response = client.get("/api/recipes/search?q=test&limit=abc")
        
        # FastAPI will return 422 for invalid parameter type
        assert response.status_code == 422
        class TestDeleteRecipe:
            """Test delete recipe endpoint"""
            
            def test_delete_recipe_success(self, client):
                """Test successful recipe deletion"""
                recipe_id = "test-recipe-123"
                
                with patch('app.services.storage.recipe_storage.delete_recipe', return_value=True) as mock_delete:
                    response = client.delete(f"/api/recipes/{recipe_id}")
                    
                    assert response.status_code == 200
                    data = response.json()
                    
                    # Verify response structure
                    assert "message" in data
                    assert "id" in data
                    assert data["message"] == "Recipe deleted successfully"
                    assert data["id"] == recipe_id
                    
                    # Verify storage method was called correctly
                    mock_delete.assert_called_once_with(recipe_id)

            def test_delete_recipe_not_found(self, client):
                """Test deleting non-existent recipe returns 404"""
                recipe_id = "non-existent-recipe"
                
                with patch('app.services.storage.recipe_storage.delete_recipe', return_value=False) as mock_delete:
                    response = client.delete(f"/api/recipes/{recipe_id}")
                    
                    assert response.status_code == 404
                    data = response.json()
                    
                    # Verify error response structure
                    assert data["error"] is True
                    assert data["status_code"] == 404
                    assert f"Internal recipe with ID '{recipe_id}' not found" in data["message"]
                    
                    mock_delete.assert_called_once_with(recipe_id)

            def test_delete_recipe_empty_id(self, client):
                """Test delete with empty recipe ID returns 400"""
                response = client.delete("/api/recipes/")
                
                # FastAPI will return 404 for missing path parameter
                assert response.status_code == 404

            def test_delete_recipe_whitespace_id(self, client):
                """Test delete with whitespace-only recipe ID returns 400"""
                recipe_id = "   "
                
                response = client.delete(f"/api/recipes/{recipe_id}")
                
                assert response.status_code == 400
                data = response.json()
                assert data["error"] is True
                assert data["message"] == "Recipe ID cannot be empty"
                assert data["status_code"] == 400

            def test_delete_recipe_storage_exception(self, client):
                """Test delete when storage raises exception returns 500"""
                recipe_id = "test-recipe-123"
                
                with patch('app.services.storage.recipe_storage.delete_recipe', side_effect=Exception("Database error")):
                    response = client.delete(f"/api/recipes/{recipe_id}")
                    
                    assert response.status_code == 500
                    data = response.json()
                    assert data["error"] is True
                    assert data["message"] == "Internal server error occurred"
                    assert data["status_code"] == 500

            def test_delete_recipe_with_encoded_characters(self, client):
                """Test delete with URL-encoded characters in recipe ID"""
                recipe_id = "test%20recipe%20123"
                decoded_id = "test recipe 123"
                
                with patch('app.services.storage.recipe_storage.delete_recipe', return_value=True) as mock_delete:
                    response = client.delete(f"/api/recipes/{recipe_id}")
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data["id"] == decoded_id
                    
                    # Verify storage was called with decoded ID
                    mock_delete.assert_called_once_with(decoded_id)

            def test_delete_recipe_special_characters(self, client):
                """Test delete with special characters in recipe ID"""
                recipe_id = "recipe-with-dash_and_underscore.123"
                
                with patch('app.services.storage.recipe_storage.delete_recipe', return_value=True) as mock_delete:
                    response = client.delete(f"/api/recipes/{recipe_id}")
                    
                    assert response.status_code == 200
                    mock_delete.assert_called_once_with(recipe_id)

            def test_delete_recipe_very_long_id(self, client):
                """Test delete with very long recipe ID"""
                recipe_id = "very-long-recipe-id-" + "x" * 1000
                
                with patch('app.services.storage.recipe_storage.delete_recipe', return_value=False) as mock_delete:
                    response = client.delete(f"/api/recipes/{recipe_id}")
                    
                    # Should still process the request and call storage
                    assert response.status_code == 404  # Not found
                    mock_delete.assert_called_once_with(recipe_id)