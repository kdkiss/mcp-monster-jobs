#!/usr/bin/env python3
"""
Deployment Validation Script for Monster Jobs MCP Server
Tests all endpoints and configurations to ensure successful scanning
"""

import json
import requests
import sys
import time
from typing import Dict, Any, Tuple, List

class DeploymentValidator:
    def __init__(self, base_url: str = "http://localhost:8081"):
        self.base_url = base_url
        self.test_results = []
        self.failed_tests = []
        self.passed_tests = []
    
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result with details."""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": time.time(),
            "response": response_data
        }
        self.test_results.append(result)
        
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status} {test_name}: {details}")
        
        if success:
            self.passed_tests.append(test_name)
        else:
            self.failed_tests.append(test_name)
    
    def test_endpoint(self, path: str, method: str = 'GET', data: Dict = None, 
                     test_name: str = "", expected_keys: List[str] = None,
                     expected_status: int = 200) -> Tuple[bool, Dict]:
        """Test an endpoint with comprehensive validation."""
        try:
            if not test_name:
                test_name = f"{method} {path}"
            
            url = f"{self.base_url}{path}"
            
            if method == 'GET':
                response = requests.get(url, timeout=10)
            elif method == 'POST':
                headers = {'Content-Type': 'application/json'}
                response = requests.post(url, json=data, headers=headers, timeout=10)
            else:
                self.log_test(test_name, False, f"Unsupported method: {method}")
                return False, {}
            
            # Check status code
            if response.status_code != expected_status:
                self.log_test(test_name, False, f"HTTP {response.status_code}, expected {expected_status}")
                return False, {}
            
            # Try to parse JSON response
            try:
                response_data = response.json()
            except json.JSONDecodeError as e:
                self.log_test(test_name, False, f"Invalid JSON: {e}")
                return False, {}
            
            # Check for expected keys
            if expected_keys:
                missing_keys = [key for key in expected_keys if key not in response_data]
                if missing_keys:
                    self.log_test(test_name, False, f"Missing keys: {missing_keys}", response_data)
                    return False, response_data
            
            # Test JSON serialization
            try:
                json.dumps(response_data)
            except Exception as ser_error:
                self.log_test(test_name, False, f"JSON serialization failed: {ser_error}", response_data)
                return False, response_data
            
            self.log_test(test_name, True, f"HTTP {response.status_code}, valid JSON", response_data)
            return True, response_data
            
        except Exception as e:
            self.log_test(test_name, False, f"Exception: {e}")
            return False, {}
    
    def test_mcp_jsonrpc(self, method: str, params: Dict = None, test_name: str = "") -> Tuple[bool, Dict]:
        """Test MCP JSON-RPC methods."""
        try:
            if not test_name:
                test_name = f"MCP {method}"
            
            payload = {
                "jsonrpc": "2.0",
                "method": method,
                "params": params or {},
                "id": 1
            }
            
            success, response_data = self.test_endpoint("/mcp", "POST", payload, test_name)
            
            if not success:
                return False, {}
            
            # Validate JSON-RPC structure
            if "jsonrpc" not in response_data or response_data["jsonrpc"] != "2.0":
                self.log_test(test_name, False, "Invalid JSON-RPC response", response_data)
                return False, response_data
            
            if "error" in response_data:
                self.log_test(test_name, False, f"RPC Error: {response_data['error']}", response_data)
                return False, response_data
            
            if "result" not in response_data:
                self.log_test(test_name, False, "Missing result in response", response_data)
                return False, response_data
            
            return True, response_data
            
        except Exception as e:
            self.log_test(test_name, False, f"Exception: {e}")
            return False, {}
    
    def run_comprehensive_tests(self):
        """Run the complete test suite."""
        print("\\n" + "="*60)
        print("   MONSTER JOBS MCP SERVER DEPLOYMENT VALIDATION")
        print("="*60)
        print(f"Testing server at: {self.base_url}")
        print()
        
        # 1. Basic Connectivity Tests
        print("\\n📡 BASIC CONNECTIVITY TESTS")
        print("-" * 40)
        self.test_endpoint("/", test_name="Root endpoint", expected_keys=["name", "version"])
        self.test_endpoint("/health", test_name="Health check", expected_keys=["status"])
        self.test_endpoint("/ping", test_name="Ping test", expected_keys=["status"])
        self.test_endpoint("/ready", test_name="Ready check", expected_keys=["status"])
        self.test_endpoint("/status", test_name="Status check", expected_keys=["status"])
        
        # 2. Test Configuration Endpoints
        print("\\n🧪 TEST CONFIGURATION ENDPOINTS")
        print("-" * 40)
        self.test_endpoint("/metadata", test_name="Metadata endpoint", expected_keys=["server", "testing"])
        self.test_endpoint("/test-config", test_name="Test config endpoint", expected_keys=["tests"])
        self.test_endpoint("/.smithery-test", test_name="Smithery test config", expected_keys=["version", "tests"])
        
        # 3. MCP Service Discovery
        print("\\n🔍 MCP SERVICE DISCOVERY")
        print("-" * 40)
        self.test_endpoint("/.well-known/mcp-config", test_name="MCP Config", expected_keys=["serverInfo"])
        self.test_endpoint("/mcp/capabilities", test_name="MCP Capabilities", expected_keys=["protocolVersion"])
        self.test_endpoint("/mcp/server-info", test_name="MCP Server Info", expected_keys=["name", "version"])
        self.test_endpoint("/smithery", test_name="Smithery Info", expected_keys=["name", "type"])
        self.test_endpoint("/scan", test_name="Universal Scan", expected_keys=["server", "protocol"])
        self.test_endpoint("/mcp/scan", test_name="MCP Scan", expected_keys=["name", "capabilities"])
        
        # 4. MCP Protocol Compliance
        print("\\n🔧 MCP PROTOCOL COMPLIANCE")
        print("-" * 40)
        
        # Initialize
        success, init_data = self.test_mcp_jsonrpc(
            "initialize", 
            {"protocolVersion": "2024-11-05", "capabilities": {}},
            "MCP Initialize"
        )
        
        if success:
            result = init_data.get("result", {})
            if "protocolVersion" in result:
                self.log_test("Protocol Version Check", True, f"Version: {result['protocolVersion']}")
            else:
                self.log_test("Protocol Version Check", False, "Missing protocolVersion")
        
        # Tools list
        success, tools_data = self.test_mcp_jsonrpc("tools/list", {}, "MCP Tools List")
        if success:
            result = tools_data.get("result", {})
            tools = result.get("tools", [])
            if tools:
                self.log_test("Tools Available", True, f"Found {len(tools)} tools: {[t.get('name') for t in tools]}")
            else:
                self.log_test("Tools Available", False, "No tools found")
        
        # Resources list
        success, resources_data = self.test_mcp_jsonrpc("resources/list", {}, "MCP Resources List")
        if success:
            result = resources_data.get("result", {})
            resources = result.get("resources", [])
            if resources:
                self.log_test("Resources Available", True, f"Found {len(resources)} resources: {[r.get('uri') for r in resources]}")
            else:
                self.log_test("Resources Available", False, "No resources found")
        
        # 5. Error Handling Tests
        print("\\n⚠️  ERROR HANDLING TESTS")
        print("-" * 40)
        
        # Test unknown endpoint
        self.test_endpoint("/unknown-endpoint", test_name="Unknown endpoint handling", expected_status=404)
        
        # Test invalid JSON-RPC
        invalid_request = {"invalid": "request"}
        self.test_endpoint("/mcp", "POST", invalid_request, "Invalid JSON-RPC handling", expected_status=400)
        
        # Test empty request
        self.test_endpoint("/mcp", "POST", {}, "Empty JSON-RPC handling", expected_status=400)
        
        # 6. Generate Summary
        print("\\n" + "="*60)
        print("   VALIDATION SUMMARY")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_count = len(self.passed_tests)
        failed_count = len(self.failed_tests)
        success_rate = (passed_count / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 Total tests: {total_tests}")
        print(f"✅ Passed: {passed_count}")
        print(f"❌ Failed: {failed_count}")
        print(f"📈 Success rate: {success_rate:.1f}%")
        
        if self.failed_tests:
            print(f"\\n❌ Failed tests:")
            for test in self.failed_tests:
                print(f"   - {test}")
            print(f"\\n⚠️  Server deployment validation FAILED")
            print(f"🔧 Please fix the issues above before deployment")
            return False
        else:
            print(f"\\n🎉 ALL TESTS PASSED!")
            print(f"✅ Server is ready for production deployment")
            print(f"🚀 MCP scanning should complete successfully")
            return True

def main():
    """Main validation function."""
    print("🔄 Starting deployment validation...")
    print("⏳ Waiting for server to be ready...")
    time.sleep(3)  # Give server time to start
    
    validator = DeploymentValidator()
    success = validator.run_comprehensive_tests()
    
    if success:
        print(f"\\n✅ Validation completed successfully!")
        sys.exit(0)
    else:
        print(f"\\n❌ Validation failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()