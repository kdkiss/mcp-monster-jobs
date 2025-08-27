#!/usr/bin/env python3
"""
Simple deployment status check for Smithery
"""

import json
import os

from validate_config import parse_simple_yaml

def check_deployment_files():
    """Check if all required deployment files are present and valid."""
    print("📁 Checking deployment files...")
    
    files_to_check = [
        'smithery.yaml',
        'Dockerfile',
        '.smithery-test.yaml',
        'src/main.py',
        'pyproject.toml'
    ]
    
    all_present = True
    for file in files_to_check:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} - MISSING")
            all_present = False
    
    return all_present

def check_smithery_config():
    """Validate smithery.yaml configuration."""
    print("\n⚙️  Checking smithery.yaml configuration...")
    
    try:
        config = parse_simple_yaml("smithery.yaml")

        required_sections = ["runtime", "build", "startCommand"]
        for section in required_sections:
            if section in config:
                print(f"   ✅ {section} section present")
            else:
                print(f"   ❌ {section} section missing")

        return True
    except Exception as e:
        print(f"   ❌ Error reading smithery.yaml: {e}")
        return False

def check_test_configs():
    """Check test configuration files."""
    print("\n🧪 Checking test configurations...")
    
    test_files = [".smithery-test.yaml", "test-config.yaml", "test.yaml"]

    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"   ✅ {test_file} present")
            try:
                with open(test_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                if content:
                    print("      ✅ File has content")
                else:
                    print("      ⚠️  File is empty")
            except Exception as e:
                print(f"      ❌ Error reading {test_file}: {e}")
        else:
            print(f"   ⚠️  {test_file} not found")

def main():
    """Run all deployment checks."""
    print("🚀 Smithery Deployment Status Check")
    print("=" * 40)
    
    files_ok = check_deployment_files()
    config_ok = check_smithery_config()
    check_test_configs()
    
    print("\n📊 Summary:")
    if files_ok and config_ok:
        print("✅ Deployment configuration looks good!")
        print("   - All required files present")
        print("   - smithery.yaml is valid")
        print("\n🎯 Ready for deployment!")
    else:
        print("⚠️  Some issues detected:")
        if not files_ok:
            print("   - Missing required files")
        if not config_ok:
            print("   - Configuration issues")
        print("\n🔧 Please fix issues before deploying")

if __name__ == '__main__':
    main()
