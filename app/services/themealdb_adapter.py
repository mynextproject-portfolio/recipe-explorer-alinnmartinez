import aiohttp
import asyncio
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models import Recipe, ExternalRecipe, RecipeSource

logger = logging.getLogger(__name__)

class TheMealDBAdapter:
    """Adapter for TheMealDB API integration"""
    
    BASE_URL = "https://www.themealdb.com/api/json/v1/1"
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=10)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def close(self):
        """Close HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def _make_request(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Make HTTP request to TheMealDB API with error handling"""
        try:
            session = await self._get_session()
            url = f"{self.BASE_URL}/{endpoint}"
            logger.info(f"Making request to TheMealDB: {url}")
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Successfully received data from TheMealDB")
                    return data
                else:
                    logger.warning(f"TheMealDB API returned status {response.status}")
                    return None
                    
        except asyncio.TimeoutError:
            logger.error("Timeout while connecting to TheMealDB API")
            return None
        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error calling TheMealDB API: {e}")
            return None
    
    def _parse_ingredients(self, meal: Dict[str, Any]) -> List[str]:
        """Extract ingredients from TheMealDB meal object"""
        ingredients = []
        for i in range(1, 21):  # TheMealDB has up to 20 ingredients
            ingredient = meal.get(f'strIngredient{i}')
            measure = meal.get(f'strMeasure{i}')
            
            if ingredient and ingredient.strip():
                if measure and measure.strip():
                    ingredients.append(f"{measure.strip()} {ingredient.strip()}")
                else:
                    ingredients.append(ingredient.strip())
        
        return ingredients
    
    def _parse_instructions(self, instructions_text: str) -> List[str]:
        """Parse instructions text into list of steps"""
        MAX_STEP_LENGTH = 500  # Match Recipe model validation limit

        if not instructions_text:
            return ["No instructions available"]

        # Split by common delimiters
        steps = []

        # Try splitting by numbered steps first
        if any(char.isdigit() for char in instructions_text[:10]):
            # Split by step numbers (1., 2., etc.)
            import re
            step_pattern = r'\d+\.\s*'
            parts = re.split(step_pattern, instructions_text)
            steps = [step.strip() for step in parts if step.strip()]
        else:
            # Split by sentences or line breaks
            sentences = instructions_text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
            steps = []
            for sentence in sentences:
                if sentence.strip() and len(sentence.strip()) > 10:
                    steps.append(sentence.strip())

        if not steps:
            steps = [instructions_text.strip()]

        # Split any steps that exceed the max length
        final_steps = []
        for step in steps:
            if len(step) <= MAX_STEP_LENGTH:
                final_steps.append(step)
            else:
                # Split long steps by sentence boundaries or at max length
                remaining = step
                while remaining:
                    if len(remaining) <= MAX_STEP_LENGTH:
                        final_steps.append(remaining)
                        break
                    # Try to split at a sentence boundary (. ! ?)
                    split_pos = -1
                    for i in range(MAX_STEP_LENGTH - 1, max(0, MAX_STEP_LENGTH - 100), -1):
                        if remaining[i] in '.!?' and (i + 1 >= len(remaining) or remaining[i + 1] == ' '):
                            split_pos = i + 1
                            break
                    if split_pos == -1:
                        # No sentence boundary found, split at last space
                        split_pos = remaining.rfind(' ', 0, MAX_STEP_LENGTH)
                    if split_pos <= 0:
                        # No space found, hard split at max length
                        split_pos = MAX_STEP_LENGTH
                    final_steps.append(remaining[:split_pos].strip())
                    remaining = remaining[split_pos:].strip()

        return final_steps if final_steps else ["No instructions available"]
    
    def _transform_meal_to_recipe(self, meal: Dict[str, Any]) -> Recipe:
        """Transform TheMealDB meal format to internal Recipe format"""
        # Parse ingredients with measurements
        ingredients = self._parse_ingredients(meal)
        
        # Parse instructions into steps
        instructions = self._parse_instructions(meal.get('strInstructions', ''))
        
        # Extract tags
        tags = []
        if meal.get('strCategory'):
            tags.append(meal['strCategory'])
        if meal.get('strTags'):
            # Tags are comma-separated in TheMealDB
            meal_tags = [tag.strip() for tag in meal['strTags'].split(',') if tag.strip()]
            tags.extend(meal_tags)
        
        # Create recipe object
        return Recipe(
            id=f"ext_{meal['idMeal']}",  # Prefix with 'ext_' to distinguish external IDs
            title=meal.get('strMeal', 'Unknown Recipe'),
            description=f"Delicious {meal.get('strMeal', 'recipe')} from {meal.get('strArea', 'Unknown')} cuisine.",
            ingredients=ingredients,
            instructions=instructions,
            tags=tags,
            cuisine=meal.get('strArea', 'International'),
            source=RecipeSource.EXTERNAL,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            external_image=meal.get('strMealThumb'),
            external_video=meal.get('strYoutube'),
            external_area=meal.get('strArea'),
            external_category=meal.get('strCategory')
        )
    
    async def search_recipes(self, query: str) -> List[Recipe]:
        """Search for recipes by name"""
        try:
            data = await self._make_request(f"search.php?s={query}")
            
            if not data or not data.get('meals'):
                logger.info(f"No meals found for query: {query}")
                return []
            
            recipes = []
            for meal in data['meals']:
                try:
                    recipe = self._transform_meal_to_recipe(meal)
                    recipes.append(recipe)
                except Exception as e:
                    logger.warning(f"Error transforming meal {meal.get('idMeal')}: {e}")
                    continue
            
            logger.info(f"Successfully transformed {len(recipes)} recipes from TheMealDB")
            return recipes
            
        except Exception as e:
            logger.error(f"Error searching TheMealDB recipes: {e}")
            return []
    
    async def get_recipe_by_id(self, meal_id: str) -> Optional[Recipe]:
        """Get a specific recipe by TheMealDB ID"""
        try:
            # Remove 'ext_' prefix if present
            if meal_id.startswith('ext_'):
                meal_id = meal_id[4:]
            
            data = await self._make_request(f"lookup.php?i={meal_id}")
            
            if not data or not data.get('meals'):
                logger.info(f"No meal found for ID: {meal_id}")
                return None
            
            meal = data['meals'][0]
            recipe = self._transform_meal_to_recipe(meal)
            
            logger.info(f"Successfully retrieved recipe {meal_id} from TheMealDB")
            return recipe
            
        except Exception as e:
            logger.error(f"Error getting TheMealDB recipe {meal_id}: {e}")
            return None
    
    async def get_random_recipes(self, count: int = 5) -> List[Recipe]:
        """Get random recipes from TheMealDB"""
        try:
            recipes = []
            tasks = [self._make_request("random.php") for _ in range(count)]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            for response in responses:
                if isinstance(response, dict) and response.get('meals'):
                    try:
                        recipe = self._transform_meal_to_recipe(response['meals'][0])
                        recipes.append(recipe)
                    except Exception as e:
                        logger.warning(f"Error transforming random meal: {e}")
                        continue
            
            logger.info(f"Retrieved {len(recipes)} random recipes from TheMealDB")
            return recipes
            
        except Exception as e:
            logger.error(f"Error getting random TheMealDB recipes: {e}")
            return []

# Global instance
themealdb_adapter = TheMealDBAdapter()