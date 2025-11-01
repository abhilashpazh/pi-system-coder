"""
Unit Tests for File Output Tool

Tests the file_output.py module functionality including:
- File generation
- Documentation creation
- Manifest generation
- File integrity hashing
"""

import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import json
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.tools.file_output import file_output, write_files_to_disk, format_tool_output


class TestFileOutput(unittest.TestCase):
    """Test cases for file output tool"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.valid_doc_response = {
            "readme_content": """# PI System Code

## Description
This module provides functionality to interact with PI System.

## Installation
Install dependencies: pip install requests

## Usage
```python
result = read_pi_tag_value('https://server', 'user', 'pass', 'TAG001')
```

## Dependencies
- requests
""",
            "manifest_content": {
                "author": "PI System Code Generator",
                "version": "1.0.0",
                "description": "Read PI tag values via Web API",
                "language": "Python",
                "api": "PI Web API",
                "dependencies": ["requests"],
                "requirements": "Python 3.6+",
                "usage": "Call function with required parameters"
            }
        }
        
        self.test_code = """import requests
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
        return None"""
        
        self.test_dependencies = ["requests"]
    
    @patch('file_output.genai.GenerativeModel')
    def test_file_output_basic(self, mock_model):
        """Test basic file output generation"""
        mock_response = MagicMock()
        mock_response.text = json.dumps(self.valid_doc_response)
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        result = file_output(
            code=self.test_code,
            target_language="Python",
            selected_api="PI Web API",
            dependencies=self.test_dependencies
        )
        
        self.assertEqual(result["status"], "success")
        self.assertIsNotNone(result["files"])
        self.assertIn("main_code", result["files"])
        self.assertIn("readme", result["files"])
        self.assertIn("manifest", result["files"])
        self.assertIsNotNone(result["file_hashes"])
        self.assertEqual(result["reasoning_type"], "finalization")
    
    @patch('file_output.genai.GenerativeModel')
    def test_file_output_all_files(self, mock_model):
        """Test that all required files are generated"""
        mock_response = MagicMock()
        mock_response.text = json.dumps(self.valid_doc_response)
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        result = file_output(
            code=self.test_code,
            target_language="Python",
            selected_api="PI Web API",
            dependencies=self.test_dependencies
        )
        
        # Check main code file
        self.assertEqual(result["files"]["main_code"]["filename"], "pi_code.py")
        self.assertEqual(result["files"]["main_code"]["content"], self.test_code)
        
        # Check readme file
        self.assertEqual(result["files"]["readme"]["filename"], "README.md")
        self.assertIn("#", result["files"]["readme"]["content"])  # Should have markdown
        
        # Check manifest file
        self.assertEqual(result["files"]["manifest"]["filename"], "manifest.json")
        manifest = json.loads(result["files"]["manifest"]["content"])
        self.assertIn("timestamp", manifest)
        self.assertIn("code_size_bytes", manifest)
        self.assertIn("language", manifest)
    
    @patch('file_output.genai.GenerativeModel')
    def test_file_output_different_languages(self, mock_model):
        """Test file output for different programming languages"""
        languages = ["C#", "JavaScript", "Java", "PowerShell"]
        
        for lang in languages:
            with self.subTest(language=lang):
                mock_response = MagicMock()
                mock_response.text = json.dumps(self.valid_doc_response)
                
                mock_instance = MagicMock()
                mock_instance.generate_content.return_value = mock_response
                mock_model.return_value = mock_instance
                
                result = file_output(
                    code=self.test_code,
                    target_language=lang,
                    selected_api="PI SDK",
                    dependencies=self.test_dependencies
                )
                
                self.assertEqual(result["status"], "success")
                # Verify correct file extension
                if lang == "C#":
                    self.assertIn(".cs", result["files"]["main_code"]["filename"])
                elif lang == "JavaScript":
                    self.assertIn(".js", result["files"]["main_code"]["filename"])
    
    @patch('file_output.genai.GenerativeModel')
    def test_file_output_with_test_results(self, mock_model):
        """Test file output with test results"""
        mock_response = MagicMock()
        mock_response.text = json.dumps(self.valid_doc_response)
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        test_results = {
            "overall_result": "pass",
            "syntax_check": {"passed": True, "issues": []},
            "logic_consistency": {"passed": True, "issues": []},
            "best_practices": {"passed": True, "issues": []},
            "error_handling": {"passed": True, "issues": []},
            "security": {"passed": True, "issues": []}
        }
        
        result = file_output(
            code=self.test_code,
            target_language="Python",
            selected_api="PI Web API",
            dependencies=self.test_dependencies,
            test_results=test_results
        )
        
        self.assertEqual(result["status"], "success")
        manifest = json.loads(result["files"]["manifest"]["content"])
        self.assertEqual(manifest["test_status"], "pass")
        self.assertIn("quality_metrics", manifest)
        self.assertTrue(manifest["quality_metrics"]["syntax_check_passed"])
    
    @patch('file_output.genai.GenerativeModel')
    def test_file_output_invalid_json(self, mock_model):
        """Test handling of invalid JSON response"""
        mock_response = MagicMock()
        mock_response.text = "Not valid JSON"
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        result = file_output(
            code=self.test_code,
            target_language="Python",
            selected_api="PI Web API",
            dependencies=self.test_dependencies
        )
        
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["reasoning_type"], "error_recovery")
    
    @patch('file_output.genai.GenerativeModel')
    def test_file_output_missing_fields(self, mock_model):
        """Test handling of missing required fields"""
        incomplete_response = {"readme_content": "Some content"}
        
        mock_response = MagicMock()
        mock_response.text = json.dumps(incomplete_response)
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        result = file_output(
            code=self.test_code,
            target_language="Python",
            selected_api="PI Web API",
            dependencies=self.test_dependencies
        )
        
        self.assertEqual(result["status"], "error")
        self.assertIsNotNone(result["error_msg"])
    
    @patch('file_output.genai.GenerativeModel')
    def test_file_output_exception_handling(self, mock_model):
        """Test handling of exceptions during API call"""
        mock_instance = MagicMock()
        mock_instance.generate_content.side_effect = Exception("Documentation API error")
        mock_model.return_value = mock_instance
        
        result = file_output(
            code=self.test_code,
            target_language="Python",
            selected_api="PI Web API",
            dependencies=self.test_dependencies
        )
        
        self.assertEqual(result["status"], "error")
        self.assertIn("Documentation API", result["error_msg"])
    
    def test_file_hashes_generation(self):
        """Test that file hashes are properly generated"""
        with patch('file_output.genai.GenerativeModel') as mock_model:
            mock_response = MagicMock()
            mock_response.text = json.dumps(self.valid_doc_response)
            
            mock_instance = MagicMock()
            mock_instance.generate_content.return_value = mock_response
            mock_model.return_value = mock_instance
            
            result = file_output(
                code=self.test_code,
                target_language="Python",
                selected_api="PI Web API",
                dependencies=self.test_dependencies
            )
            
            self.assertEqual(result["status"], "success")
            self.assertIn("main_code", result["file_hashes"])
            self.assertIn("readme", result["file_hashes"])
            self.assertIn("manifest", result["file_hashes"])
            
            # Verify hash length (SHA256 produces 64 char hex)
            for file_name, file_hash in result["file_hashes"].items():
                self.assertEqual(len(file_hash), 64)
    
    @patch('file_output.genai.GenerativeModel')
    def test_write_files_to_disk_success(self, mock_model):
        """Test writing files to disk successfully"""
        mock_response = MagicMock()
        mock_response.text = json.dumps(self.valid_doc_response)
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        result = file_output(
            code=self.test_code,
            target_language="Python",
            selected_api="PI Web API",
            dependencies=self.test_dependencies
        )
        
        # Create temporary directory for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            written_files = write_files_to_disk(result, tmpdir)
            
            self.assertEqual(len(written_files), 3)
            self.assertTrue(os.path.exists(written_files[0]))
            
            # Verify file contents
            with open(written_files[0], 'r') as f:
                written_code = f.read()
                self.assertEqual(written_code, self.test_code)
    
    @patch('file_output.genai.GenerativeModel')
    def test_write_files_to_disk_create_directory(self, mock_model):
        """Test that directory is created if it doesn't exist"""
        mock_response = MagicMock()
        mock_response.text = json.dumps(self.valid_doc_response)
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        result = file_output(
            code=self.test_code,
            target_language="Python",
            selected_api="PI Web API",
            dependencies=self.test_dependencies
        )
        
        new_dir = os.path.join(tempfile.gettempdir(), "test_output_new")
        
        try:
            written_files = write_files_to_disk(result, new_dir)
            self.assertTrue(os.path.exists(new_dir))
            self.assertEqual(len(written_files), 3)
        finally:
            if os.path.exists(new_dir):
                shutil.rmtree(new_dir)
    
    @patch('file_output.genai.GenerativeModel')
    def test_write_files_to_disk_failure(self, mock_model):
        """Test that writing fails if file_output status is error"""
        fail_result = {
            "status": "error",
            "error_msg": "Test error"
        }
        
        with self.assertRaises(ValueError):
            write_files_to_disk(fail_result, "/tmp")
    
    @patch('file_output.genai.GenerativeModel')
    def test_format_tool_output_success(self, mock_model):
        """Test formatting successful file output result"""
        mock_response = MagicMock()
        mock_response.text = json.dumps(self.valid_doc_response)
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        result = file_output(
            code=self.test_code,
            target_language="Python",
            selected_api="PI Web API",
            dependencies=self.test_dependencies
        )
        
        output = format_tool_output(result)
        
        self.assertIn("FINAL_ANSWER:", output)
        self.assertIn("Python", output)
        self.assertIn("PI Web API", output)
        self.assertIn(self.test_code, output)
        self.assertIn("Documentation", output)
    
    @patch('file_output.genai.GenerativeModel')
    def test_format_tool_output_with_test_results(self, mock_model):
        """Test formatting with test results"""
        mock_response = MagicMock()
        mock_response.text = json.dumps(self.valid_doc_response)
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        test_results = {
            "overall_result": "pass",
            "syntax_check": {"passed": True, "issues": []},
            "logic_consistency": {"passed": True, "issues": []},
            "best_practices": {"passed": True, "issues": []},
            "error_handling": {"passed": True, "issues": []},
            "security": {"passed": True, "issues": []}
        }
        
        result = file_output(
            code=self.test_code,
            target_language="Python",
            selected_api="PI Web API",
            dependencies=self.test_dependencies,
            test_results=test_results
        )
        
        output = format_tool_output(result)
        
        self.assertIn("FINAL_ANSWER:", output)
        self.assertIn("Quality Checks", output)
        self.assertIn("PASS", output)
    
    def test_format_tool_output_error(self):
        """Test formatting error result"""
        result = {
            "status": "error",
            "files": None,
            "file_hashes": None,
            "reasoning": None,
            "reasoning_type": "error_recovery",
            "error_msg": "Test error"
        }
        
        output = format_tool_output(result)
        
        self.assertIn("TOOL_RESULT: file_output", output)
        self.assertIn("status=error", output)
        self.assertIn("Test error", output)
    
    @patch('file_output.genai.GenerativeModel')
    def test_manifest_includes_metadata(self, mock_model):
        """Test that manifest includes all required metadata"""
        mock_response = MagicMock()
        mock_response.text = json.dumps(self.valid_doc_response)
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        result = file_output(
            code=self.test_code,
            target_language="Python",
            selected_api="PI Web API",
            dependencies=self.test_dependencies
        )
        
        manifest = json.loads(result["files"]["manifest"]["content"])
        
        # Check required fields
        self.assertIn("author", manifest)
        self.assertIn("version", manifest)
        self.assertIn("description", manifest)
        self.assertIn("language", manifest)
        self.assertIn("api", manifest)
        self.assertIn("dependencies", manifest)
        self.assertIn("timestamp", manifest)
        self.assertIn("code_size_bytes", manifest)
        self.assertIn("code_lines", manifest)


if __name__ == "__main__":
    unittest.main(verbosity=2)

