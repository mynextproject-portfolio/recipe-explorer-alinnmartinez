#!/usr/bin/env python3
"""
Schema validation script for Recipe Explorer API.
Validates that all recipes comply with the expected schema.
"""

import sys
import json
import os
from typing import List, Dict, Any
from pathlib import Path

# Add the parent directory to Python path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from pydantic import ValidationError
    from app.models import Recipe, RecipeCreate
    from app.services.storage import recipe_storage
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    print("Make sure you're running this script from the project root directory")
    sys.exit(1)

class SchemaValidator:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def validate_recipe_schema(self, recipe_data: Dict[str, Any]) -> bool:
        """Validate a single recipe against the schema"""
        try:
            Recipe(**recipe_data)
            return True
        except ValidationError as e:
            self.errors.append({
                "type": "validation_error",
                "recipe": recipe_data.get("title", "Unknown"),
                "errors": [{"field": " -> ".join(str(x) for x in err["loc"]), "message": err["msg"]} for err in e.errors()]
            })
            return False
        except Exception as e:
            self.errors.append({
                "type": "general_error", 
                "recipe": recipe_data.get("title", "Unknown"),
                "error": str(e)
            })
            return False

    def validate_all_stored_recipes(self) -> Dict[str, Any]:
        """Validate all recipes in storage"""
        recipes = recipe_storage.get_all_recipes()
        valid_count = 0
        
        for recipe in recipes:
            recipe_dict = recipe.model_dump()
            if self.validate_recipe_schema(recipe_dict):
                valid_count += 1
        
        return {
            "total_recipes": len(recipes),
            "valid_recipes": valid_count,
            "invalid_recipes": len(recipes) - valid_count,
            "errors": self.errors,
            "warnings": self.warnings
        }

    def validate_required_fields(self, recipe_data: Dict[str, Any]) -> bool:
        """Check for required fields"""
        required_fields = ["title", "description", "ingredients", "instructions", "cuisine"]
        missing_fields = []
        
        for field in required_fields:
            if field not in recipe_data:
                missing_fields.append(field)
        
        if missing_fields:
            self.errors.append({
                "type": "missing_fields",
                "recipe": recipe_data.get("title", "Unknown"),
                "missing_fields": missing_fields
            })
            return False
        
        return True

    def validate_schema_compliance(self, recipes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate multiple recipes for schema compliance"""
        results = {
            "total": len(recipes),
            "valid": 0,
            "invalid": 0,
            "errors": [],
            "warnings": []
        }
        
        # Reset errors for this validation run
        original_errors = self.errors.copy()
        self.errors = []
        
        for recipe_data in recipes:
            if self.validate_required_fields(recipe_data) and self.validate_recipe_schema(recipe_data):
                results["valid"] += 1
            else:
                results["invalid"] += 1
        
        results["errors"] = self.errors
        results["warnings"] = self.warnings
        
        # Restore original errors
        self.errors = original_errors + self.errors
        
        return results

    def check_schema_changes(self) -> Dict[str, Any]:
        """Check that schema changes are properly implemented"""
        results = {
            "instructions_is_array": False,
            "difficulty_removed": True,
            "cuisine_field_exists": False,
            "sample_recipe_loaded": False
        }
        
        recipes = recipe_storage.get_all_recipes()
        
        if recipes:
            results["sample_recipe_loaded"] = True
            sample_recipe = recipes[0]
            recipe_dict = sample_recipe.model_dump()
            
            # Check if instructions is an array
            if isinstance(recipe_dict.get("instructions"), list):
                results["instructions_is_array"] = True
            
            # Check if cuisine field exists
            if "cuisine" in recipe_dict and recipe_dict["cuisine"]:
                results["cuisine_field_exists"] = True
            
            # Check if difficulty field is removed
            if "difficulty" in recipe_dict:
                results["difficulty_removed"] = False
        
        return results

def main():
    """Run schema validation"""
    validator = SchemaValidator()
    
    print("🔍 Running Recipe Schema Validation...")
    print("=" * 50)
    
    # Check schema changes first
    schema_changes = validator.check_schema_changes()
    print(f"📋 Schema Change Verification:")
    print(f"   Instructions is array: {'✅' if schema_changes['instructions_is_array'] else '❌'}")
    print(f"   Difficulty removed: {'✅' if schema_changes['difficulty_removed'] else '❌'}")
    print(f"   Cuisine field exists: {'✅' if schema_changes['cuisine_field_exists'] else '❌'}")
    print(f"   Sample recipe loaded: {'✅' if schema_changes['sample_recipe_loaded'] else '❌'}")
    
    # Validate stored recipes
    stored_results = validator.validate_all_stored_recipes()
    
    print(f"\n📊 Validation Results:")
    print(f"   Total recipes: {stored_results['total_recipes']}")
    print(f"   Valid recipes: {stored_results['valid_recipes']}")
    print(f"   Invalid recipes: {stored_results['invalid_recipes']}")
    
    if stored_results['errors']:
        print(f"\n❌ Errors found:")
        for error in stored_results['errors']:
            print(f"   - {error}")
    
    if stored_results['warnings']:
        print(f"\n⚠️  Warnings:")
        for warning in stored_results['warnings']:
            print(f"   - {warning}")
    
    # Test sample data validation
    print(f"\n🧪 Testing Sample Data Validation:")
    test_cases = [
        {
            "title": "Valid Recipe",
            "description": "A valid test recipe",
            "cuisine": "Test",
            "ingredients": ["ingredient 1", "ingredient 2"],
            "instructions": ["step 1", "step 2"],
            "tags": ["test"]
        },
        {
            "title": "",  # Invalid: empty title
            "description": "Invalid recipe",
            "cuisine": "Test",
            "ingredients": ["ingredient 1"],
            "instructions": ["step 1"],
            "tags": []
        },
        {
            # Missing required fields
            "title": "Incomplete Recipe",
            "description": "Missing ingredients"
        }
    ]
    
    test_results = validator.validate_schema_compliance(test_cases)
    print(f"   Test cases: {test_results['total']}")
    print(f"   Valid: {test_results['valid']}")
    print(f"   Invalid: {test_results['invalid']}")
    
    # Check overall success
    schema_success = all([
        schema_changes['instructions_is_array'],
        schema_changes['difficulty_removed'],
        schema_changes['cuisine_field_exists'],
        schema_changes['sample_recipe_loaded']
    ])
    
    validation_success = stored_results['invalid_recipes'] == 0
    test_success = test_results['invalid'] == 2  # Expect 2 invalid test cases
    
    # Return appropriate exit code
    if schema_success and validation_success and test_success:
        print(f"\n✅ All schema validations passed!")
        return 0
    else:
        print(f"\n❌ Schema validation failed!")
        if not schema_success:
            print("   - Schema changes not properly implemented")
        if not validation_success:
            print("   - Invalid recipes found in storage")
        if not test_success:
            print("   - Test validation failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())