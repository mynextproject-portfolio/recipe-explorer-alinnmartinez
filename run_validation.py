#!/usr/bin/env python3
"""
Simple validation runner that ensures we're in the right directory
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    # Make sure we're in the project root
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print("🚀 Running Recipe Explorer Validation Suite")
    print("=" * 50)
    
    # Run schema validation
    print("\n1. Running Schema Validation...")
    try:
        result = subprocess.run([
            sys.executable, "scripts/validate_schema.py"
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print(f"Stderr: {result.stderr}")
        
        schema_success = result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running schema validation: {e}")
        schema_success = False
    
    # Run API tests
    print("\n2. Running API Tests...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", "tests/test_api.py", "-v"
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print(f"Stderr: {result.stderr}")
        
        api_success = result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running API tests: {e}")
        api_success = False
    
    # Run validation tests
    print("\n3. Running Validation Tests...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", "tests/test_api_validation.py", "-v"
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print(f"Stderr: {result.stderr}")
        
        validation_success = result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running validation tests: {e}")
        validation_success = False
    
    # Summary
    print("\n📊 Validation Summary:")
    print(f"   Schema Validation: {'✅ PASS' if schema_success else '❌ FAIL'}")
    print(f"   API Tests: {'✅ PASS' if api_success else '❌ FAIL'}")
    print(f"   Validation Tests: {'✅ PASS' if validation_success else '❌ FAIL'}")
    
    if all([schema_success, api_success, validation_success]):
        print("\n🎉 All validations passed!")
        return 0
    else:
        print("\n💥 Some validations failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())