import asyncio
import logging
from typing import List, Tuple
from app.models import Recipe, SearchResult
from app.services.storage import recipe_storage
from app.services.themealdb_adapter import themealdb_adapter

logger = logging.getLogger(__name__)

class SearchService:
    """Enhanced search service that combines internal and external results"""
    
    @staticmethod
    async def combined_search(query: str, limit: int = 20) -> SearchResult:
        """Search both internal and external sources"""
        try:
            # Search internal and external simultaneously
            internal_task = asyncio.create_task(
                SearchService._search_internal(query)
            )
            external_task = asyncio.create_task(
                SearchService._search_external(query)
            )
            
            # Wait for both searches to complete
            internal_recipes, external_recipes = await asyncio.gather(
                internal_task, external_task, return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(internal_recipes, Exception):
                logger.error(f"Internal search failed: {internal_recipes}")
                internal_recipes = []
            
            if isinstance(external_recipes, Exception):
                logger.error(f"External search failed: {external_recipes}")
                external_recipes = []
            
            # Combine results
            all_recipes = internal_recipes + external_recipes
            
            # Limit results
            if len(all_recipes) > limit:
                all_recipes = all_recipes[:limit]
            
            return SearchResult(
                recipes=all_recipes,
                total_count=len(all_recipes),
                internal_count=len(internal_recipes),
                external_count=len(external_recipes),
                query=query
            )
            
        except Exception as e:
            logger.error(f"Error in combined search: {e}")
            return SearchResult(
                recipes=[],
                total_count=0,
                internal_count=0,
                external_count=0,
                query=query
            )
    
    @staticmethod
    async def _search_internal(query: str) -> List[Recipe]:
        """Search internal recipe database"""
        try:
            # Use existing storage search functionality
            recipes = recipe_storage.search_recipes(query)
            logger.info(f"Found {len(recipes)} internal recipes for query: {query}")
            return recipes
        except Exception as e:
            logger.error(f"Error searching internal recipes: {e}")
            return []
    
    @staticmethod
    async def _search_external(query: str) -> List[Recipe]:
        """Search external TheMealDB API"""
        try:
            recipes = await themealdb_adapter.search_recipes(query)
            logger.info(f"Found {len(recipes)} external recipes for query: {query}")
            return recipes
        except Exception as e:
            logger.error(f"Error searching external recipes: {e}")
            return []
    
    @staticmethod
    async def get_internal_recipe(recipe_id: str) -> Recipe:
        """Get recipe from internal storage"""
        recipe = recipe_storage.get_recipe(recipe_id)
        if not recipe:
            raise ValueError(f"Internal recipe {recipe_id} not found")
        return recipe
    
    @staticmethod
    async def get_external_recipe(recipe_id: str) -> Recipe:
        """Get recipe from external API"""
        recipe = await themealdb_adapter.get_recipe_by_id(recipe_id)
        if not recipe:
            raise ValueError(f"External recipe {recipe_id} not found")
        return recipe

# Global instance
search_service = SearchService()