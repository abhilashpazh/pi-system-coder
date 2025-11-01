"""
Unit Tests for Code Creation Tool

Tests the code_creation.py module functionality including:
- Code generation from pseudo-code
- Multi-language support
- Dependency extraction
- Output formatting
"""

import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.tools.code_creation import code_creation, format_tool_output, SUPPORTED_LANGUAGES


class TestCodeCreation(unittest.TestCase):
    """Test cases for code creation tool"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.valid_code_response = {
            "code": """import requests
from requests.auth import HTTPBasicAuth

def read_pi_tag_value(base_url, username, password, tag_name):
    try:
        auth = HTTPBasicAuth(username, password)
        url = f"{base_url}/streams/{tag_name}/value"
        response = requests.get(url, auth=auth, timeout=30)
        response.raise_for_status()
        return response.json()['Value']['Value']
    except Exception as e:
        print(f"Error: {e}")
        return None""",
            "dependencies": ["requests"],
            "usage_example": "read_pi_tag_value('https://server', 'user', 'pass', 'TAG001')",
            "reasoning": "Uses PI Web API with HTTP Basic authentication, proper error handling"
        }
        
        self.test_pseudo_code = [
            "Connect to PI Web API",
            "Authenticate with credentials",
            "Query tag value",
            "Return result"
        ]
        
        self.test_data_structures = [
            {"name": "url", "type": "string", "description": "API endpoint"}
        ]
        
        self.test_error_handling = "Try-catch with proper exception handling"
    
    @patch('code_creation.genai.GenerativeModel')
    def test_code_creation_python(self, mock_model):
        """Test code generation for Python"""
        mock_response = MagicMock()
        mock_response.text = json.dumps(self.valid_code_response)
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        result = code_creation(
            pseudo_code=self.test_pseudo_code,
            data_structures=self.test_data_structures,
            error_handling_strategy=self.test_error_handling,
            selected_api="PI Web API",
            target_language="Python"
        )
        
        self.assertEqual(result["status"], "success")
        self.assertIsNotNone(result["code"])
        self.assertIsInstance(result["dependencies"], list)
        self.assertIsNotNone(result["usage_example"])
        self.assertEqual(result["reasoning_type"], "implementation")
        self.assertIn("import", result["code"])
    
    @patch('code_creation.genai.GenerativeModel')
    def test_code_creation_csharp(self, mock_model):
        """Test code generation for C#"""
        csharp_response = {
            "code": """using OSIsoft.AF;
using OSIsoft.AF.PI;

public class PITagReader
{
    public static object ReadTagValue(string server, string tagName)
    {
        try
        {
            PIServer piServer = new PIServer(server);
            piServer.Connect();
            PIPoint tag = PIPoint.FindPIPoint(piServer, tagName);
            var value = tag.Data.CurrentValue();
            piServer.Disconnect();
            return value;
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error: {ex.Message}");
            return null;
        }
    }
}""",
            "dependencies": ["OSIsoft.AFSDK"],
            "usage_example": "PITagReader.ReadTagValue('PIServer01', 'TAG001')",
            "reasoning": "Uses PI SDK with proper connection management and error handling"
        }
        
        mock_response = MagicMock()
        mock_response.text = json.dumps(csharp_response)
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        result = code_creation(
            pseudo_code=self.test_pseudo_code,
            data_structures=self.test_data_structures,
            error_handling_strategy=self.test_error_handling,
            selected_api="PI SDK",
            target_language="C#"
        )
        
        self.assertEqual(result["status"], "success")
        self.assertIn("using", result["code"])
        self.assertIn("class", result["code"])
    
    @patch('code_creation.genai.GenerativeModel')
    def test_code_creation_javascript(self, mock_model):
        """Test code generation for JavaScript"""
        js_response = {
            "code": """const axios = require('axios');

async function readPITagValue(baseUrl, username, password, tagName) {
    try {
        const response = await axios.get(
            `${baseUrl}/streams/${tagName}/value`,
            {
                auth: { username, password },
                timeout: 30000
            }
        );
        return response.data.Value.Value;
    } catch (error) {
        console.error(`Error: ${error.message}`);
        return null;
    }
}""",
            "dependencies": ["axios"],
            "usage_example": "await readPITagValue('https://server', 'user', 'pass', 'TAG001')",
            "reasoning": "Uses modern async/await pattern with axios for HTTP requests"
        }
        
        mock_response = MagicMock()
        mock_response.text = json.dumps(js_response)
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        result = code_creation(
            pseudo_code=self.test_pseudo_code,
            data_structures=self.test_data_structures,
            error_handling_strategy=self.test_error_handling,
            selected_api="PI Web API",
            target_language="JavaScript"
        )
        
        self.assertEqual(result["status"], "success")
        self.assertIn("function", result["code"])
        self.assertIn("axios", result["dependencies"][0])
    
    @patch('code_creation.genai.GenerativeModel')
    def test_code_creation_unsupported_language(self, mock_model):
        """Test handling of unsupported language"""
        result = code_creation(
            pseudo_code=self.test_pseudo_code,
            data_structures=self.test_data_structures,
            error_handling_strategy=self.test_error_handling,
            selected_api="PI SDK",
            target_language="Fortran"  # Unsupported
        )
        
        self.assertEqual(result["status"], "error")
        self.assertIn("Unsupported", result["error_msg"])
    
    @patch('code_creation.genai.GenerativeModel')
    def test_code_creation_with_context(self, mock_model):
        """Test code creation with context"""
        mock_response = MagicMock()
        mock_response.text = json.dumps(self.valid_code_response)
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        context = {
            "user_preferences": "async code preferred",
            "framework": "Django"
        }
        
        result = code_creation(
            pseudo_code=self.test_pseudo_code,
            data_structures=self.test_data_structures,
            error_handling_strategy=self.test_error_handling,
            selected_api="PI Web API",
            target_language="Python",
            context=context
        )
        
        self.assertEqual(result["status"], "success")
        mock_instance.generate_content.assert_called_once()
    
    @patch('code_creation.genai.GenerativeModel')
    def test_code_creation_invalid_json(self, mock_model):
        """Test handling of invalid JSON response"""
        mock_response = MagicMock()
        mock_response.text = "Not valid JSON here"
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        result = code_creation(
            pseudo_code=self.test_pseudo_code,
            data_structures=self.test_data_structures,
            error_handling_strategy=self.test_error_handling,
            selected_api="PI SDK",
            target_language="Python"
        )
        
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["reasoning_type"], "error_recovery")
    
    @patch('code_creation.genai.GenerativeModel')
    def test_code_creation_missing_fields(self, mock_model):
        """Test handling of missing required fields"""
        incomplete_response = {"code": "some code"}
        
        mock_response = MagicMock()
        mock_response.text = json.dumps(incomplete_response)
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        result = code_creation(
            pseudo_code=self.test_pseudo_code,
            data_structures=self.test_data_structures,
            error_handling_strategy=self.test_error_handling,
            selected_api="PI SDK",
            target_language="Python"
        )
        
        self.assertEqual(result["status"], "error")
        self.assertIsNotNone(result["error_msg"])
    
    @patch('code_creation.genai.GenerativeModel')
    def test_code_creation_empty_code(self, mock_model):
        """Test handling of empty generated code"""
        empty_response = {
            "code": "",
            "dependencies": [],
            "usage_example": "",
            "reasoning": "Test"
        }
        
        mock_response = MagicMock()
        mock_response.text = json.dumps(empty_response)
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        result = code_creation(
            pseudo_code=self.test_pseudo_code,
            data_structures=self.test_data_structures,
            error_handling_strategy=self.test_error_handling,
            selected_api="PI SDK",
            target_language="Python"
        )
        
        self.assertEqual(result["status"], "error")
        self.assertIn("empty", result["error_msg"])
    
    @patch('code_creation.genai.GenerativeModel')
    def test_code_creation_exception_handling(self, mock_model):
        """Test handling of exceptions during API call"""
        mock_instance = MagicMock()
        mock_instance.generate_content.side_effect = Exception("Rate limit exceeded")
        mock_model.return_value = mock_instance
        
        result = code_creation(
            pseudo_code=self.test_pseudo_code,
            data_structures=self.test_data_structures,
            error_handling_strategy=self.test_error_handling,
            selected_api="PI SDK",
            target_language="Python"
        )
        
        self.assertEqual(result["status"], "error")
        self.assertIn("Rate limit", result["error_msg"])
    
    def test_format_tool_output_success(self):
        """Test formatting successful code creation result"""
        result = {
            "status": "success",
            "code": "def test(): pass",
            "dependencies": ["requests", "json"],
            "usage_example": "test()",
            "reasoning": "Simple test",
            "reasoning_type": "implementation",
            "error_msg": None
        }
        
        output = format_tool_output(result)
        
        self.assertIn("TOOL_RESULT: code_creation", output)
        self.assertIn("status=success", output)
        self.assertIn("requests", output)
        self.assertIn("test()", output)
    
    def test_format_tool_output_error(self):
        """Test formatting error result"""
        result = {
            "status": "error",
            "code": None,
            "dependencies": None,
            "usage_example": None,
            "reasoning": None,
            "reasoning_type": "error_recovery",
            "error_msg": "Generation failed"
        }
        
        output = format_tool_output(result)
        
        self.assertIn("TOOL_RESULT: code_creation", output)
        self.assertIn("status=error", output)
        self.assertIn("Generation failed", output)
    
    @patch('code_creation.genai.GenerativeModel')
    def test_code_creation_all_languages(self, mock_model):
        """Test code generation for all supported languages"""
        languages_to_test = ["Python", "C#", "JavaScript", "TypeScript"]
        
        for lang in languages_to_test:
            with self.subTest(language=lang):
                mock_response = MagicMock()
                mock_response.text = json.dumps(self.valid_code_response)
                
                mock_instance = MagicMock()
                mock_instance.generate_content.return_value = mock_response
                mock_model.return_value = mock_instance
                
                result = code_creation(
                    pseudo_code=self.test_pseudo_code,
                    data_structures=self.test_data_structures,
                    error_handling_strategy=self.test_error_handling,
                    selected_api="PI Web API",
                    target_language=lang
                )
                
                self.assertEqual(result["status"], "success")
                self.assertIn(lang, SUPPORTED_LANGUAGES)


if __name__ == "__main__":
    unittest.main(verbosity=2)

