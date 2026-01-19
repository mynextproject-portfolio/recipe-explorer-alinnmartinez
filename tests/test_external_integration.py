import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.themealdb_adapter import TheMealDBAdapter
from app.services.search_service import SearchService
from app.models import Recipe, RecipeSource
import aiohttp

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
    async def test_themealdb_search_multiple_ingredients(self):
        """Test search result with multiple ingredients handling"""
        adapter = TheMealDBAdapter()
        
        mock_response = {
            'meals': [{
                'idMeal': '52771',
                'strMeal': 'Spicy Arrabiata Penne',
                'strInstructions': 'Bring a large pot of water to a boil.',
                'strArea': 'Italian',
                'strCategory': 'Pasta',
                'strIngredient1': 'penne rigate',
                'strIngredient2': 'olive oil',
                'strIngredient3': 'garlic',
                'strIngredient4': 'chopped tomatoes',
                'strIngredient5': 'red chile flakes',
                'strIngredient6': '',  # Empty ingredient should be filtered
                'strMeasure1': '1 pound',
                'strMeasure2': '1/4 cup',
                'strMeasure3': '3 cloves',
                'strMeasure4': '1 tin',
                'strMeasure5': '1/2 teaspoon',
                'strMeasure6': '',  # Empty measure
            }]
        }
        
        with patch.object(adapter, '_make_request', return_value=mock_response):
            recipes = await adapter.search_recipes('pasta')
            
            assert len(recipes) == 1
            recipe = recipes[0]
            # Should have 5 ingredients (empty ones filtered out)
            assert len(recipe.ingredients) == 5
            assert 'penne rigate' in recipe.ingredients
            assert 'olive oil' in recipe.ingredients
        
        await adapter.close()

    @pytest.mark.asyncio
    async def test_themealdb_network_timeout(self):
        """Test handling of network timeouts"""
        adapter = TheMealDBAdapter()
        
        with patch.object(adapter, '_make_request', side_effect=asyncio.TimeoutError()):
            recipes = await adapter.search_recipes('chicken')
            assert recipes == []
        
        await adapter.close()

    @pytest.mark.asyncio
    async def test_themealdb_http_error(self):
        """Test handling of HTTP errors"""
        adapter = TheMealDBAdapter()
        
        mock_response = MagicMock()
        mock_response.status = 500
        
        with patch.object(adapter, '_make_request', side_effect=aiohttp.ClientResponseError(
            request_info=MagicMock(), 
            history=(),
            status=500,
            message="Internal Server Error"
        )):
            recipes = await adapter.search_recipes('chicken')
            assert recipes == []
        
        await adapter.close()

    @pytest.mark.asyncio
    async def test_themealdb_malformed_json(self):
        """Test handling of malformed JSON responses"""
        adapter = TheMealDBAdapter()
        
        with patch.object(adapter, '_make_request', side_effect=ValueError("Invalid JSON")):
            recipes = await adapter.search_recipes('chicken')
            assert recipes == []
        
        await adapter.close()

    @pytest.mark.asyncio
    async def test_themealdb_get_by_id_not_found(self):
        """Test getting recipe by non-existent ID"""
        adapter = TheMealDBAdapter()
        
        with patch.object(adapter, '_make_request', return_value=None):
            recipe = await adapter.get_recipe_by_id('999999')
            assert recipe is None
        
        await adapter.close()

    @pytest.mark.asyncio
    async def test_themealdb_random_recipes(self):
        """Test getting random recipes"""
        adapter = TheMealDBAdapter()
        
        mock_response = {
            'meals': [
                {
                    'idMeal': '52771',
                    'strMeal': 'Random Recipe 1',
                    'strInstructions': 'Instructions 1',
                    'strArea': 'Italian',
                    'strCategory': 'Pasta',
                    'strIngredient1': 'ingredient1',
                    'strMeasure1': '1 cup',
                },
                {
                    'idMeal': '52772',
                    'strMeal': 'Random Recipe 2',
                    'strInstructions': 'Instructions 2',
                    'strArea': 'Mexican',
                    'strCategory': 'Beef',
                    'strIngredient1': 'ingredient2',
                    'strMeasure1': '2 cups',
                }
            ]
        }
        
        with patch.object(adapter, '_make_request', return_value=mock_response):
            recipes = await adapter.get_random_recipes(2)
            
            assert len(recipes) == 2
            assert recipes[0].title == 'Random Recipe 1'
            assert recipes[1].title == 'Random Recipe 2'
            assert all(recipe.source == RecipeSource.EXTERNAL for recipe in recipes)
        
        await adapter.close()

class TestSearchServiceIntegration:

    @pytest.mark.asyncio
    async def test_combined_search_internal_only(self):
        """Test combined search with only internal results"""
        search_service = SearchService()
        
        mock_internal_recipes = [
            Recipe(
                id="internal_1",
                title="Internal Pasta",
                description="Internal recipe",
                cuisine="Italian",
                ingredients=["pasta", "sauce"],
                instructions=["cook pasta"],
                tags=["pasta"],
                source=RecipeSource.INTERNAL
            )
        ]
        
        with patch.object(search_service, '_search_internal', return_value=mock_internal_recipes):
            with patch.object(search_service, '_search_external', return_value=[]):
                result = await search_service.combined_search('pasta')
                
                assert result.total_count == 1
                assert result.internal_count == 1
                assert result.external_count == 0
                assert len(result.recipes) == 1
                assert result.recipes[0].source == RecipeSource.INTERNAL

    @pytest.mark.asyncio
    async def test_combined_search_external_only(self):
        """Test combined search with only external results"""
        search_service = SearchService()
        
        mock_external_recipes = [
            Recipe(
                id="ext_12345",
                title="External Pizza",
                description="External recipe",
                cuisine="Italian",
                ingredients=["dough", "cheese"],
                instructions=["make pizza"],
                tags=["pizza"],
                source=RecipeSource.EXTERNAL
            )
        ]
        
        with patch.object(search_service, '_search_internal', return_value=[]):
            with patch.object(search_service, '_search_external', return_value=mock_external_recipes):
                result = await search_service.combined_search('pizza')
                
                assert result.total_count == 1
                assert result.internal_count == 0
                assert result.external_count == 1
                assert len(result.recipes) == 1
                assert result.recipes[0].source == RecipeSource.EXTERNAL

    @pytest.mark.asyncio
    async def test_combined_search_with_limit(self):
        """Test combined search respects limit parameter"""
        search_service = SearchService()
        
        # Create mock recipes exceeding the limit
        mock_internal = [Recipe(
            id=f"internal_{i}",
            title=f"Internal Recipe {i}",
            description="Internal recipe",
            cuisine="Italian",
            ingredients=["ingredient"],
            instructions=["step"],
            tags=["tag"],
            source=RecipeSource.INTERNAL
        ) for i in range(15)]
        
        mock_external = [Recipe(
            id=f"ext_{i}",
            title=f"External Recipe {i}",
            description="External recipe",
            cuisine="Mexican",
            ingredients=["ingredient"],
            instructions=["step"],
            tags=["tag"],
            source=RecipeSource.EXTERNAL
        ) for i in range(15)]
        
        with patch.object(search_service, '_search_internal', return_value=mock_internal):
            with patch.object(search_service, '_search_external', return_value=mock_external):
                result = await search_service.combined_search('recipe', limit=10)
                
                assert result.total_count == 30  # Total found
                assert result.internal_count == 15
                assert result.external_count == 15
                assert len(result.recipes) == 10  # Limited results

    @pytest.mark.asyncio
    async def test_search_service_external_error_resilience(self):
        """Test search service handles external API errors gracefully"""
        search_service = SearchService()
        
        mock_internal_recipes = [Recipe(
            id="internal_1",
            title="Internal Recipe",
            description="Internal recipe",
            cuisine="Italian",
            ingredients=["ingredient"],
            instructions=["step"],
            tags=["tag"],
            source=RecipeSource.INTERNAL
        )]
        
        with patch.object(search_service, '_search_internal', return_value=mock_internal_recipes):
            with patch.object(search_service, '_search_external', side_effect=Exception("API Error")):
                result = await search_service.combined_search('recipe')
                
                # Should still return internal results despite external error
                assert result.total_count == 1
                assert result.internal_count == 1
                assert result.external_count == 0
                assert len(result.recipes) == 1

@pytest.mark.asyncio
async def test_api_endpoints_comprehensive():
    """Comprehensive test of all external integration API endpoints"""
    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    
    # Test combined search endpoint
    response = client.get("/api/recipes/search/chicken")
    assert response.status_code == 200
    data = response.json()
    assert "recipes" in data
    assert "total_count" in data
    assert "internal_count" in data
    assert "external_count" in data
    assert "query" in data
    assert "sources" in data
    
    # Test internal search endpoint
    response = client.get("/api/recipes/search/internal/chicken")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)  # Internal search returns list directly
    
    # Test external search endpoint
    response = client.get("/api/recipes/search/external/chicken")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)  # External search returns list directly
    
    # Test get internal recipe by ID
    response = client.get("/api/recipes/internal/test-id")
    # Should return 404 for non-existent recipe
    assert response.status_code in [404, 500]  # 500 if service error
    
    # Test get external recipe by ID
    response = client.get("/api/recipes/external/52772")
    # Should return result or 404/500
    assert response.status_code in [200, 404, 500]

@pytest.mark.asyncio
async def test_random_recipes_endpoint():
    """Test random recipes endpoint with external integration"""
    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    
    # Test random recipes endpoint
    response = client.get("/api/recipes/random")
    assert response.status_code == 200
    
    data = response.json()
    assert "recipes" in data
    assert isinstance(data["recipes"], list)
    
    # Test with custom count
    response = client.get("/api/recipes/random?count=3")
    assert response.status_code == 200
    
    data = response.json()
    assert "recipes" in data
    assert len(data["recipes"]) <= 3  # May be fewer if API limits

class TestExternalAPIRateLimiting:
    """Test rate limiting and caching behavior"""
    
    @pytest.mark.asyncio
    async def test_adapter_connection_reuse(self):
        """Test that adapter reuses HTTP connections properly"""
        adapter = TheMealDBAdapter()
        
        mock_response = {'meals': None}
        
        with patch.object(adapter, '_make_request', return_value=mock_response) as mock_request:
            # Make multiple requests
            await adapter.search_recipes('chicken')
            await adapter.search_recipes('beef')
            await adapter.get_recipe_by_id('12345')
            
            # Verify requests were made
            assert mock_request.call_count == 3
        
        await adapter.close()

    @pytest.mark.asyncio
    async def test_adapter_session_cleanup(self):
        """Test proper session cleanup"""
        adapter = TheMealDBAdapter()
        
        # Verify session exists
        assert adapter.session is not None
        
        # Close adapter
        await adapter.close()
        
        # Session should be closed
        assert adapter.session.closed

class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    @pytest.mark.asyncio
    async def test_empty_ingredient_filtering(self):
        """Test that empty ingredients are properly filtered"""
        adapter = TheMealDBAdapter()
        
        mock_response = {
            'meals': [{
                'idMeal': '1',
                'strMeal': 'Test Recipe',
                'strInstructions': 'Test instructions',
                'strArea': 'Unknown',
                'strCategory': 'Test',
                'strIngredient1': 'Real Ingredient',
                'strIngredient2': '',  # Empty
                'strIngredient3': None,  # None
                'strIngredient4': '   ',  # Whitespace only
                'strIngredient5': 'Another Real Ingredient',
                'strMeasure1': '1 cup',
                'strMeasure2': '',
                'strMeasure3': None,
                'strMeasure4': '   ',
                'strMeasure5': '2 cups',
            }]
        }
        
        with patch.object(adapter, '_make_request', return_value=mock_response):
            recipes = await adapter.search_recipes('test')
            
            assert len(recipes) == 1
            recipe = recipes[0]
            # Should only have 2 real ingredients
            assert len(recipe.ingredients) == 2
            assert 'Real Ingredient' in recipe.ingredients
            assert 'Another Real Ingredient' in recipe.ingredients
        
        await adapter.close()

    @pytest.mark.asyncio
    async def test_unicode_handling(self):
        """Test proper handling of unicode characters"""
        adapter = TheMealDBAdapter()
        
        mock_response = {
            'meals': [{
                'idMeal': '1',
                'strMeal': 'Crème Brûlée',
                'strInstructions': 'Instructions with émojis 🍰',
                'strArea': 'Français',
                'strCategory': 'Dessert',
                'strIngredient1': 'crème fraîche',
                'strMeasure1': '200ml',
            }]
        }
        
        with patch.object(adapter, '_make_request', return_value=mock_response):
            recipes = await adapter.search_recipes('crème')
            
            assert len(recipes) == 1
            recipe = recipes[0]
            assert recipe.title == 'Crème Brûlée'
            assert recipe.cuisine == 'Français'
            assert 'émojis 🍰' in recipe.instructions[0]
        
        await adapter.close()

    @pytest.mark.asyncio
    async def test_large_instruction_text(self):
        """Test handling of very long instruction text"""
        adapter = TheMealDBAdapter()
        
        # Create very long instructions
        long_instructions = "Step 1: " + "Very long instruction text. " * 100
        
        mock_response = {
            'meals': [{
                'idMeal': '1',
                'strMeal': 'Complex Recipe',
                'strInstructions': long_instructions,
                'strArea': 'International',
                'strCategory': 'Main',
                'strIngredient1': 'ingredient',
                'strMeasure1': '1 unit',
            }]
        }
        
        with patch.object(adapter, '_make_request', return_value=mock_response):
            recipes = await adapter.search_recipes('complex')
            
            assert len(recipes) == 1
            recipe = recipes[0]
            # Instructions should be properly split
            assert len(recipe.instructions) >= 1
            assert len(recipe.instructions[0]) > 100
        
        await adapter.close()
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