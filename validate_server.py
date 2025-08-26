#!/usr/bin/env python3
"""
Comprehensive MCP Server Validation Script
Tests all endpoints and MCP protocol compliance
"""

import json
import requests
import sys
import time
from typing import Dict, Any, Tuple

class MCPServerValidator:
    def __init__(self, base_url: str = "http://localhost:8081"):
        self.base_url = base_url
        self.test_results = []
        self.failed_tests = []
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result."""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": time.time()
        }
        self.test_results.append(result)
        
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status} {test_name}: {details}")
        
        if not success:
            self.failed_tests.append(test_name)
    
    def test_get_endpoint(self, path: str, test_name: str, expected_keys: list = None) -> Tuple[bool, Dict]:
        """Test a GET endpoint."""
        try:
            url = f"{self.base_url}{path}"
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                self.log_test(test_name, False, f"HTTP {response.status_code}")
                return False, {}
            
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                self.log_test(test_name, False, f"Invalid JSON: {e}")
                return False, {}
            
            if expected_keys:
                missing_keys = [key for key in expected_keys if key not in data]
                if missing_keys:
                    self.log_test(test_name, False, f"Missing keys: {missing_keys}")
                    return False, data
            
            self.log_test(test_name, True, f"HTTP 200, valid JSON")
            return True, data
            
        except Exception as e:
            self.log_test(test_name, False, f"Exception: {e}")
            return False, {}
    
    def test_mcp_rpc(self, method: str, params: Dict = None, test_name: str = "") -> Tuple[bool, Dict]:
        """Test an MCP JSON-RPC method."""
        try:
            if not test_name:
                test_name = f"MCP {method}"
            
            payload = {
                "jsonrpc": "2.0",
                "method": method,
                "params": params or {},
                "id": 1
            }
            
            url = f"{self.base_url}/mcp"
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code != 200:
                self.log_test(test_name, False, f"HTTP {response.status_code}")
                return False, {}\n            
            try:\n                data = response.json()\n            except json.JSONDecodeError as e:\n                self.log_test(test_name, False, f\"Invalid JSON: {e}\")\n                return False, {}\n            \n            # Check JSON-RPC structure\n            if \"jsonrpc\" not in data or data[\"jsonrpc\"] != \"2.0\":\n                self.log_test(test_name, False, \"Invalid JSON-RPC response\")\n                return False, data\n            \n            if \"error\" in data:\n                self.log_test(test_name, False, f\"RPC Error: {data['error']}\")\n                return False, data\n            \n            if \"result\" not in data:\n                self.log_test(test_name, False, \"Missing result in response\")\n                return False, data\n            \n            self.log_test(test_name, True, \"Valid JSON-RPC response\")\n            return True, data\n            \n        except Exception as e:\n            self.log_test(test_name, False, f\"Exception: {e}\")\n            return False, {}\n    \n    def run_all_tests(self):\n        \"\"\"Run comprehensive test suite.\"\"\"\n        print(\"\\n=== MCP Server Validation Tests ===\")\n        print(f\"Testing server at: {self.base_url}\")\n        print()\n        \n        # Basic connectivity tests\n        print(\"--- Basic Connectivity ---\")\n        self.test_get_endpoint(\"/\", \"Root endpoint\", [\"name\", \"version\"])\n        self.test_get_endpoint(\"/health\", \"Health check\", [\"status\"])\n        self.test_get_endpoint(\"/ping\", \"Ping test\", [\"status\"])\n        self.test_get_endpoint(\"/ready\", \"Ready check\", [\"status\"])\n        self.test_get_endpoint(\"/status\", \"Status check\", [\"status\"])\n        \n        # MCP-specific endpoints\n        print(\"\\n--- MCP Service Discovery ---\")\n        self.test_get_endpoint(\"/.well-known/mcp-config\", \"MCP Config\", [\"serverInfo\"])\n        self.test_get_endpoint(\"/mcp/capabilities\", \"MCP Capabilities\", [\"protocolVersion\"])\n        self.test_get_endpoint(\"/mcp/server-info\", \"MCP Server Info\", [\"name\", \"version\"])\n        self.test_get_endpoint(\"/smithery\", \"Smithery Info\", [\"name\", \"type\"])\n        self.test_get_endpoint(\"/scan\", \"Universal Scan\", [\"server\", \"protocol\"])\n        self.test_get_endpoint(\"/mcp/scan\", \"MCP Scan\", [\"name\", \"capabilities\"])\n        \n        # MCP Protocol tests\n        print(\"\\n--- MCP Protocol Compliance ---\")\n        \n        # Initialize\n        success, init_data = self.test_mcp_rpc(\n            \"initialize\", \n            {\"protocolVersion\": \"2024-11-05\", \"capabilities\": {}},\n            \"MCP Initialize\"\n        )\n        \n        if success:\n            result = init_data.get(\"result\", {})\n            if \"protocolVersion\" not in result:\n                self.log_test(\"Initialize Protocol Version\", False, \"Missing protocolVersion\")\n            else:\n                self.log_test(\"Initialize Protocol Version\", True, f\"Version: {result['protocolVersion']}\")\n        \n        # Tools list\n        success, tools_data = self.test_mcp_rpc(\"tools/list\", {}, \"MCP Tools List\")\n        if success:\n            result = tools_data.get(\"result\", {})\n            tools = result.get(\"tools\", [])\n            if not tools:\n                self.log_test(\"Tools Available\", False, \"No tools found\")\n            else:\n                self.log_test(\"Tools Available\", True, f\"Found {len(tools)} tools\")\n        \n        # Resources list\n        success, resources_data = self.test_mcp_rpc(\"resources/list\", {}, \"MCP Resources List\")\n        if success:\n            result = resources_data.get(\"result\", {})\n            resources = result.get(\"resources\", [])\n            if not resources:\n                self.log_test(\"Resources Available\", False, \"No resources found\")\n            else:\n                self.log_test(\"Resources Available\", True, f\"Found {len(resources)} resources\")\n        \n        # Summary\n        print(\"\\n=== Test Summary ===\")\n        total_tests = len(self.test_results)\n        failed_count = len(self.failed_tests)\n        passed_count = total_tests - failed_count\n        \n        print(f\"Total tests: {total_tests}\")\n        print(f\"Passed: {passed_count}\")\n        print(f\"Failed: {failed_count}\")\n        \n        if self.failed_tests:\n            print(f\"\\nFailed tests: {', '.join(self.failed_tests)}\")\n            return False\n        else:\n            print(\"\\n🎉 All tests passed! Server is ready for deployment.\")\n            return True\n\ndef main():\n    validator = MCPServerValidator()\n    \n    # Wait a moment for server to be ready\n    print(\"Waiting for server to be ready...\")\n    time.sleep(2)\n    \n    success = validator.run_all_tests()\n    \n    if not success:\n        print(\"\\n❌ Validation failed. Please fix issues before deployment.\")\n        sys.exit(1)\n    else:\n        print(\"\\n✅ Validation successful. Server is ready!\")\n        sys.exit(0)\n\nif __name__ == '__main__':\n    main()