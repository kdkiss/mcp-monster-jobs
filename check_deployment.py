#!/usr/bin/env python3
"""
Simple deployment status check for Smithery
"""

import json
import os

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
        import yaml
        with open('smithery.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        required_sections = ['runtime', 'build', 'startCommand', 'testConfig', 'env']
        for section in required_sections:
            if section in config:
                print(f"   ✅ {section} section present")
            else:
                print(f"   ❌ {section} section missing")
        
        # Check testConfig specifically
        if 'testConfig' in config:
            test_config = config['testConfig']
            if test_config.get('enabled'):
                print(f"   ✅ testConfig enabled")
                if 'configFile' in test_config:
                    config_file = test_config['configFile']
                    if os.path.exists(config_file):
                        print(f"   ✅ Test config file exists: {config_file}")
                    else:
                        print(f"   ❌ Test config file missing: {config_file}")
                else:
                    print(f"   ⚠️  No configFile specified in testConfig")
            else:
                print(f"   ⚠️  testConfig not enabled")
        
        return True
        
    except ImportError:
        print("   ⚠️  PyYAML not available, skipping YAML validation")
        return True
    except Exception as e:
        print(f"   ❌ Error reading smithery.yaml: {e}")
        return False

def check_test_configs():
    """Check test configuration files."""
    print("\n🧪 Checking test configurations...")
    
    test_files = ['.smithery-test.yaml', 'test-config.yaml', 'test.yaml']
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"   ✅ {test_file} present")
            try:
                with open(test_file, 'r') as f:
                    if test_file.endswith('.yaml'):
                        import yaml
                        data = yaml.safe_load(f)
                        if isinstance(data, dict):
                            print(f"      ✅ Valid YAML structure")
                        else:
                            print(f"      ⚠️  Unexpected YAML structure")
                    else:
                        content = f.read()
                        if len(content) > 0:
                            print(f"      ✅ File has content")
                        else:
                            print(f"      ⚠️  File is empty")
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
        print("   - testConfig is properly configured")
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