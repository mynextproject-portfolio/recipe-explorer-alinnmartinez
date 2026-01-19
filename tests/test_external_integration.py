import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from app.services.themealdb_adapter import TheMealDBAdapter
from app.services.search_service import SearchService
from app.models import Recipe, RecipeSource

class TestTheMealDBIntegration:
    
    @pytest.mark.asyncio
    async def test_themealdb_search_success(self):
        """Test successful search of TheMealDB API"""
        adapter = TheMealDBAdapter()
        
        # Mock response data
        mock_response = {
            'meals': [{
                'idMeal': '52772',
                'strMeal': 'Teriyaki Chicken Casserole',
                'strInstructions': 'Preheat oven to 180C/160C Fan/Gas 4.\r\n\r\nPut the noodles in a large microwave-proof bowl. Cover with boiling water and microwave for 2 mins or until soft. Drain and set aside.\r\n\r\nMix the cornflour with 2 tbsp cold water until smooth, then gradually stir in the teriyaki sauce.',
                'strMealThumb': 'https://www.themealdb.com/images/media/meals/wvpsxx1468256321.jpg',
                'strArea': 'Japanese',
                'strCategory': 'Chicken',
                'strIngredient1': 'egg noodles',
                'strIngredient2': 'cornflour',
                'strMeasure1': '200g',
                'strMeasure2': '3 tbsp',
            }]
        }
        
        with patch.object(adapter, '_make_request', return_value=mock_response):
            recipes = await adapter.search_recipes('chicken')
            
            assert len(recipes) == 1
            recipe = recipes[0]
            assert recipe.title == 'Teriyaki Chicken Casserole'
            assert recipe.source == RecipeSource.EXTERNAL
            assert recipe.cuisine == 'Japanese'
            assert len(recipe.ingredients) >= 2
            assert recipe.id.startswith('ext_')
        
        await adapter.close()
    
    @pytest.mark.asyncio
    async def test_themealdb_search_empty_result(self):
        """Test search with no results"""
        adapter = TheMealDBAdapter()
        
        with patch.object(adapter, '_make_request', return_value=None):
            recipes = await adapter.search_recipes('nonexistent')
            assert recipes == []
        
        await adapter.close()
    
    @pytest.mark.asyncio
    async def test_themealdb_get_by_id(self):
        """Test getting recipe by ID"""
        adapter = TheMealDBAdapter()
        
        mock_response = {
            'meals': [{
                'idMeal': '52772',
                'strMeal': 'Teriyaki Chicken Casserole',
                'strInstructions': 'Test instructions',
                'strArea': 'Japanese',
                'strCategory': 'Chicken',
                'strIngredient1': 'egg noodles',
                'strMeasure1': '200g',
            }]
        }
        
        with patch.object(adapter, '_make_request', return_value=mock_response):
            recipe = await adapter.get_recipe_by_id('52772')
            
            assert recipe is not None
            assert recipe.id == 'ext_52772'
            assert recipe.title == 'Teriyaki Chicken Casserole'
        
        await adapter.close()
    
    @pytest.mark.asyncio
    async def test_combined_search(self):
        """Test combined search functionality"""
        search_service = SearchService()
        
        # Mock internal search
        with patch.object(search_service, '_search_internal', return_value=[]):
            # Mock external search
            with patch.object(search_service, '_search_external', return_value=[]):
                result = await search_service.combined_search('test')
                
                assert result.total_count == 0
                assert result.internal_count == 0
                assert result.external_count == 0
                assert result.query == 'test'
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test API error handling"""
        adapter = TheMealDBAdapter()
        
        with patch.object(adapter, '_make_request', side_effect=Exception('API Error')):
            recipes = await adapter.search_recipes('test')
            assert recipes == []
        
        await adapter.close()

@pytest.mark.asyncio
async def test_api_endpoints_with_external_data():
    """Test API endpoints with external data integration"""
    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    
    # Test search endpoint
    response = client.get("/api/recipes/search/chicken")
    assert response.status_code == 200
    
    data = response.json()
    assert "recipes" in data
    assert "total_count" in data
    assert "internal_count" in data
    assert "external_count" in data
    
    # Test internal endpoint
    response = client.get("/api/recipes/search/internal/chicken")
    assert response.status_code == 200
    
    # Test external endpoint  
    response = client.get("/api/recipes/search/external/chicken")
    assert response.status_code == 200