"""
Unit Tests for API Selection Tool

Tests the api_selection.py module functionality including:
- API selection logic
- Error handling
- Output formatting
- Gemini API integration
"""

import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.tools.api_selection import api_selection, format_tool_output, AVAILABLE_APIS


class TestAPISelection(unittest.TestCase):
    """Test cases for API selection tool"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.valid_api_response = {
            "selected_api": "PI SDK",
            "reasoning": "High performance server-side data access is needed for batch operations"
        }
    
    @patch('api_selection.genai.GenerativeModel')
    def test_api_selection_pi_sdk(self, mock_model):
        """Test API selection for PI SDK use case"""
        # Mock Gemini API response
        mock_response = MagicMock()
        mock_response.text = json.dumps(self.valid_api_response)
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        # Test with appropriate request
        request = "Read PI tag values for the last 24 hours with high performance"
        result = api_selection(request)
        
        # Assertions
        self.assertEqual(result["status"], "success")
        self.assertIn(result["selected_api"], AVAILABLE_APIS)
        self.assertIsNotNone(result["reasoning"])
        self.assertEqual(result["reasoning_type"], "api_selection")
        self.assertIsNone(result["error_msg"])
    
    @patch('api_selection.genai.GenerativeModel')
    def test_api_selection_pi_af_sdk(self, mock_model):
        """Test API selection for PI AF SDK use case"""
        af_response = {
            "selected_api": "PI AF SDK",
            "reasoning": "Asset Framework operations require hierarchical data navigation"
        }
        
        mock_response = MagicMock()
        mock_response.text = json.dumps(af_response)
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        request = "Query asset hierarchies and navigate through AF databases"
        result = api_selection(request)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["selected_api"], "PI AF SDK")
        self.assertEqual(result["reasoning_type"], "api_selection")
    
    @patch('api_selection.genai.GenerativeModel')
    def test_api_selection_pi_web_api(self, mock_model):
        """Test API selection for PI Web API use case"""
        web_response = {
            "selected_api": "PI Web API",
            "reasoning": "Cross-platform RESTful access needed for web application"
        }
        
        mock_response = MagicMock()
        mock_response.text = json.dumps(web_response)
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        request = "Build a web dashboard that displays PI data"
        result = api_selection(request)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["selected_api"], "PI Web API")
        self.assertEqual(result["reasoning_type"], "api_selection")
    
    @patch('api_selection.genai.GenerativeModel')
    def test_api_selection_with_context(self, mock_model):
        """Test API selection with context from previous interactions"""
        mock_response = MagicMock()
        mock_response.text = json.dumps(self.valid_api_response)
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        context = {
            "previous_api": "PI Web API",
            "user_language": "Python"
        }
        
        request = "Create function to read PI tags"
        result = api_selection(request, context=context)
        
        self.assertEqual(result["status"], "success")
        # Verify context was passed to model
        mock_instance.generate_content.assert_called_once()
    
    @patch('api_selection.genai.GenerativeModel')
    def test_api_selection_invalid_json(self, mock_model):
        """Test handling of invalid JSON response"""
        mock_response = MagicMock()
        mock_response.text = "This is not valid JSON"
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        request = "Read PI tags"
        result = api_selection(request)
        
        self.assertEqual(result["status"], "error")
        self.assertIsNotNone(result["error_msg"])
        self.assertEqual(result["reasoning_type"], "error_recovery")
    
    @patch('api_selection.genai.GenerativeModel')
    def test_api_selection_missing_fields(self, mock_model):
        """Test handling of JSON with missing required fields"""
        incomplete_response = {"selected_api": "PI SDK"}
        
        mock_response = MagicMock()
        mock_response.text = json.dumps(incomplete_response)
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        request = "Read PI tags"
        result = api_selection(request)
        
        self.assertEqual(result["status"], "error")
        self.assertIsNotNone(result["error_msg"])
    
    @patch('api_selection.genai.GenerativeModel')
    def test_api_selection_unknown_api(self, mock_model):
        """Test handling of unknown API selection"""
        unknown_response = {
            "selected_api": "Unknown API",
            "reasoning": "Some reasoning"
        }
        
        mock_response = MagicMock()
        mock_response.text = json.dumps(unknown_response)
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        request = "Read PI tags"
        result = api_selection(request)
        
        self.assertEqual(result["status"], "error")
        self.assertIsNotNone(result["error_msg"])
    
    @patch('api_selection.genai.GenerativeModel')
    def test_api_selection_exception_handling(self, mock_model):
        """Test handling of exceptions during API call"""
        mock_instance = MagicMock()
        mock_instance.generate_content.side_effect = Exception("Network error")
        mock_model.return_value = mock_instance
        
        request = "Read PI tags"
        result = api_selection(request)
        
        self.assertEqual(result["status"], "error")
        self.assertIsNotNone(result["error_msg"])
        self.assertIn("Network error", result["error_msg"])
    
    def test_format_tool_output_success(self):
        """Test formatting successful API selection result"""
        result = {
            "status": "success",
            "selected_api": "PI SDK",
            "reasoning": "Test reasoning",
            "reasoning_type": "api_selection",
            "error_msg": None
        }
        
        output = format_tool_output(result)
        
        self.assertIn("TOOL_RESULT: api_selection", output)
        self.assertIn("status=success", output)
        self.assertIn("PI SDK", output)
        self.assertIn("Test reasoning", output)
    
    def test_format_tool_output_error(self):
        """Test formatting error result"""
        result = {
            "status": "error",
            "selected_api": None,
            "reasoning": None,
            "reasoning_type": "error_recovery",
            "error_msg": "Test error message"
        }
        
        output = format_tool_output(result)
        
        self.assertIn("TOOL_RESULT: api_selection", output)
        self.assertIn("status=error", output)
        self.assertIn("Test error message", output)
    
    def test_available_apis_list(self):
        """Test that available APIs list is properly defined"""
        self.assertIsInstance(AVAILABLE_APIS, list)
        self.assertGreater(len(AVAILABLE_APIS), 0)
        self.assertIn("PI SDK", AVAILABLE_APIS)
        self.assertIn("PI AF SDK", AVAILABLE_APIS)
        self.assertIn("PI Web API", AVAILABLE_APIS)
        self.assertIn("PI SQL Client", AVAILABLE_APIS)


class TestAPISelectionIntegration(unittest.TestCase):
    """Integration tests for API selection (requires actual Gemini API key)"""
    
    @unittest.skipUnless(
        os.getenv("GEMINI_API_KEY"),
        "GEMINI_API_KEY not set, skipping integration tests"
    )
    def test_real_api_selection(self):
        """Test with real Gemini API (requires API key)"""
        request = "Create a function to read PI tag values for the last 24 hours"
        result = api_selection(request)
        
        self.assertEqual(result["status"], "success")
        self.assertIn(result["selected_api"], AVAILABLE_APIS)
        self.assertIsNotNone(result["reasoning"])


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)

