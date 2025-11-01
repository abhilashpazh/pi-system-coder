"""
Unit Tests for Logic Creation Tool

Tests the logic_creation.py module functionality including:
- Pseudo-code generation
- Data structure definitions
- Error handling
- Output formatting
"""

import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.tools.logic_creation import logic_creation, format_tool_output


class TestLogicCreation(unittest.TestCase):
    """Test cases for logic creation tool"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.valid_logic_response = {
            "pseudo_code": [
                "Step 1: Initialize PI SDK connection",
                "Step 2: Authenticate with credentials",
                "Step 3: Query tag by name",
                "Step 4: Retrieve current value",
                "Step 5: Handle errors and cleanup"
            ],
            "data_structures": [
                {
                    "name": "connection",
                    "type": "PISDK.Connection",
                    "description": "PI Data Archive connection object"
                },
                {
                    "name": "tag",
                    "type": "PISDK.PIPoint",
                    "description": "PI tag point reference"
                },
                {
                    "name": "value",
                    "type": "double",
                    "description": "Current tag value"
                }
            ],
            "error_handling_strategy": "Try-catch around connection and query operations, return None on error",
            "reasoning": "Follows standard PI SDK connection pattern with proper resource cleanup"
        }
    
    @patch('logic_creation.genai.GenerativeModel')
    def test_logic_creation_basic(self, mock_model):
        """Test basic logic creation functionality"""
        mock_response = MagicMock()
        mock_response.text = json.dumps(self.valid_logic_response)
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        request = "Read current PI tag value"
        api = "PI SDK"
        result = logic_creation(request, api)
        
        # Assertions
        self.assertEqual(result["status"], "success")
        self.assertIsInstance(result["pseudo_code"], list)
        self.assertGreater(len(result["pseudo_code"]), 0)
        self.assertIsInstance(result["data_structures"], list)
        self.assertIsNotNone(result["error_handling_strategy"])
        self.assertIsNotNone(result["reasoning"])
        self.assertEqual(result["reasoning_type"], "logical_decomposition")
        self.assertIsNone(result["error_msg"])
    
    @patch('logic_creation.genai.GenerativeModel')
    def test_logic_creation_pi_af_sdk(self, mock_model):
        """Test logic creation for PI AF SDK"""
        af_response = {
            "pseudo_code": [
                "Step 1: Connect to AF Server",
                "Step 2: Navigate to database",
                "Step 3: Query element hierarchy",
                "Step 4: Retrieve attributes"
            ],
            "data_structures": [
                {
                    "name": "server",
                    "type": "AFServer",
                    "description": "AF Server connection"
                }
            ],
            "error_handling_strategy": "Exception handling for network and query errors",
            "reasoning": "AF SDK requires hierarchical navigation approach"
        }
        
        mock_response = MagicMock()
        mock_response.text = json.dumps(af_response)
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        request = "Query AF element hierarchy"
        api = "PI AF SDK"
        result = logic_creation(request, api)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["reasoning_type"], "logical_decomposition")
        # Verify that the response was processed correctly
        self.assertGreater(len(result["pseudo_code"]), 0)
    
    @patch('logic_creation.genai.GenerativeModel')
    def test_logic_creation_pi_web_api(self, mock_model):
        """Test logic creation for PI Web API"""
        web_response = {
            "pseudo_code": [
                "Step 1: Construct base URL",
                "Step 2: Set up authentication headers",
                "Step 3: Make HTTP GET request",
                "Step 4: Parse JSON response",
                "Step 5: Extract value"
            ],
            "data_structures": [
                {
                    "name": "headers",
                    "type": "dict",
                    "description": "HTTP headers with credentials"
                }
            ],
            "error_handling_strategy": "Check HTTP status code, handle 401/404 errors",
            "reasoning": "RESTful API pattern with standard HTTP operations"
        }
        
        mock_response = MagicMock()
        mock_response.text = json.dumps(web_response)
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        request = "Get PI data via Web API"
        api = "PI Web API"
        result = logic_creation(request, api)
        
        self.assertEqual(result["status"], "success")
        self.assertIn("HTTP", result["pseudo_code"][2])
    
    @patch('logic_creation.genai.GenerativeModel')
    def test_logic_creation_with_context(self, mock_model):
        """Test logic creation with context"""
        mock_response = MagicMock()
        mock_response.text = json.dumps(self.valid_logic_response)
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        context = {
            "selected_language": "Python",
            "previous_operations": ["connection", "authentication"]
        }
        
        request = "Read PI tag"
        api = "PI SDK"
        result = logic_creation(request, api, context=context)
        
        self.assertEqual(result["status"], "success")
        mock_instance.generate_content.assert_called_once()
    
    @patch('logic_creation.genai.GenerativeModel')
    def test_logic_creation_invalid_json(self, mock_model):
        """Test handling of invalid JSON response"""
        mock_response = MagicMock()
        mock_response.text = "Invalid JSON text here"
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        result = logic_creation("Read tag", "PI SDK")
        
        self.assertEqual(result["status"], "error")
        self.assertIsNotNone(result["error_msg"])
        self.assertEqual(result["reasoning_type"], "error_recovery")
    
    @patch('logic_creation.genai.GenerativeModel')
    def test_logic_creation_missing_pseudo_code(self, mock_model):
        """Test handling of missing pseudo_code field"""
        incomplete_response = {
            "data_structures": [],
            "error_handling_strategy": "None",
            "reasoning": "Test"
        }
        
        mock_response = MagicMock()
        mock_response.text = json.dumps(incomplete_response)
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        result = logic_creation("Read tag", "PI SDK")
        
        self.assertEqual(result["status"], "error")
        self.assertIn("pseudo_code", result["error_msg"])
    
    @patch('logic_creation.genai.GenerativeModel')
    def test_logic_creation_empty_pseudo_code(self, mock_model):
        """Test handling of empty pseudo_code list"""
        empty_response = {
            "pseudo_code": [],
            "data_structures": [],
            "error_handling_strategy": "None",
            "reasoning": "Test"
        }
        
        mock_response = MagicMock()
        mock_response.text = json.dumps(empty_response)
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        result = logic_creation("Read tag", "PI SDK")
        
        self.assertEqual(result["status"], "error")
        self.assertIn("cannot be empty", result["error_msg"])
    
    @patch('logic_creation.genai.GenerativeModel')
    def test_logic_creation_invalid_pseudo_code_type(self, mock_model):
        """Test handling of invalid pseudo_code type"""
        invalid_response = {
            "pseudo_code": "not a list",
            "data_structures": [],
            "error_handling_strategy": "None",
            "reasoning": "Test"
        }
        
        mock_response = MagicMock()
        mock_response.text = json.dumps(invalid_response)
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        result = logic_creation("Read tag", "PI SDK")
        
        self.assertEqual(result["status"], "error")
        self.assertIn("must be a list", result["error_msg"])
    
    @patch('logic_creation.genai.GenerativeModel')
    def test_logic_creation_exception_handling(self, mock_model):
        """Test handling of exceptions during API call"""
        mock_instance = MagicMock()
        mock_instance.generate_content.side_effect = Exception("API timeout")
        mock_model.return_value = mock_instance
        
        result = logic_creation("Read tag", "PI SDK")
        
        self.assertEqual(result["status"], "error")
        self.assertIsNotNone(result["error_msg"])
        self.assertIn("timeout", result["error_msg"])
    
    def test_format_tool_output_success(self):
        """Test formatting successful logic creation result"""
        result = {
            "status": "success",
            "pseudo_code": ["Step 1: Do something", "Step 2: Do more"],
            "data_structures": [{"name": "var", "type": "string"}],
            "error_handling_strategy": "Try-catch",
            "reasoning": "Test reasoning",
            "reasoning_type": "logical_decomposition",
            "error_msg": None
        }
        
        output = format_tool_output(result)
        
        self.assertIn("TOOL_RESULT: logic_creation", output)
        self.assertIn("status=success", output)
        self.assertIn("Step 1", output)
        self.assertIn("Try-catch", output)
    
    def test_format_tool_output_error(self):
        """Test formatting error result"""
        result = {
            "status": "error",
            "pseudo_code": None,
            "data_structures": None,
            "error_handling_strategy": None,
            "reasoning": None,
            "reasoning_type": "error_recovery",
            "error_msg": "Test error"
        }
        
        output = format_tool_output(result)
        
        self.assertIn("TOOL_RESULT: logic_creation", output)
        self.assertIn("status=error", output)
        self.assertIn("Test error", output)
    
    @patch('logic_creation.genai.GenerativeModel')
    def test_logic_creation_complex_workflow(self, mock_model):
        """Test logic creation for complex multi-step workflow"""
        complex_response = {
            "pseudo_code": [
                "Step 1: Connect to PI Data Archive",
                "Step 2: Authenticate user credentials",
                "Step 3: Create data archive connection",
                "Step 4: Query multiple tags",
                "Step 5: Read historical data for each tag",
                "Step 6: Aggregate values",
                "Step 7: Calculate statistics",
                "Step 8: Format output",
                "Step 9: Cleanup resources",
                "Step 10: Return results"
            ],
            "data_structures": [
                {"name": "connection", "type": "Connection", "description": "PI connection"},
                {"name": "tags", "type": "List<PIPoint>", "description": "Tag list"},
                {"name": "values", "type": "List<double>", "description": "Historical values"},
                {"name": "stats", "type": "Statistics", "description": "Calculated stats"}
            ],
            "error_handling_strategy": "Comprehensive error handling with retry logic for network errors",
            "reasoning": "Complex workflow requires careful resource management and error recovery"
        }
        
        mock_response = MagicMock()
        mock_response.text = json.dumps(complex_response)
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        request = "Read historical data for multiple tags and calculate statistics"
        api = "PI SDK"
        result = logic_creation(request, api)
        
        self.assertEqual(result["status"], "success")
        self.assertGreaterEqual(len(result["pseudo_code"]), 5)
        self.assertGreaterEqual(len(result["data_structures"]), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)

