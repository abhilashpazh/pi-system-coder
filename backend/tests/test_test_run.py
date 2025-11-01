"""
Unit Tests for Test Run Tool

Tests the test_run.py module functionality including:
- Code quality checks
- Security validation
- Output formatting
- Local security checks
"""

import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.tools.test_run import test_run, format_tool_output, perform_local_security_checks


class TestTestRun(unittest.TestCase):
    """Test cases for test run tool"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.valid_test_response = {
            "syntax_check": {
                "passed": True,
                "issues": []
            },
            "logic_consistency": {
                "passed": True,
                "issues": []
            },
            "best_practices": {
                "passed": True,
                "issues": []
            },
            "error_handling": {
                "passed": True,
                "issues": []
            },
            "security": {
                "passed": True,
                "issues": []
            },
            "overall_result": "pass",
            "recommendations": [],
            "reasoning": "Code meets all quality standards"
        }
        
        self.test_code_good = """import requests
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
        
        self.test_code_bad = """def read_tag():
    password = "hardcoded123"
    return password"""
    
    @patch('test_run.genai.GenerativeModel')
    def test_test_run_pass(self, mock_model):
        """Test successful test run with passing results"""
        mock_response = MagicMock()
        mock_response.text = json.dumps(self.valid_test_response)
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        result = test_run(
            code=self.test_code_good,
            target_language="Python",
            selected_api="PI Web API"
        )
        
        self.assertEqual(result["status"], "success")
        self.assertTrue(result["syntax_check"]["passed"])
        self.assertTrue(result["logic_consistency"]["passed"])
        self.assertTrue(result["security"]["passed"])
        self.assertEqual(result["overall_result"], "pass")
        self.assertEqual(result["reasoning_type"], "validation_check")
        self.assertIsInstance(result["recommendations"], list)
    
    @patch('test_run.genai.GenerativeModel')
    def test_test_run_fail(self, mock_model):
        """Test test run with failing results"""
        fail_response = {
            "syntax_check": {
                "passed": False,
                "issues": ["Indentation error on line 5"]
            },
            "logic_consistency": {
                "passed": True,
                "issues": []
            },
            "best_practices": {
                "passed": False,
                "issues": ["Missing docstring"]
            },
            "error_handling": {
                "passed": True,
                "issues": []
            },
            "security": {
                "passed": True,
                "issues": []
            },
            "overall_result": "fail",
            "recommendations": ["Add docstring", "Fix indentation"],
            "reasoning": "Syntax errors detected"
        }
        
        mock_response = MagicMock()
        mock_response.text = json.dumps(fail_response)
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        result = test_run(
            code=self.test_code_bad,
            target_language="Python",
            selected_api="PI SDK"
        )
        
        self.assertEqual(result["status"], "success")
        self.assertFalse(result["syntax_check"]["passed"])
        self.assertEqual(result["overall_result"], "fail")
        self.assertGreater(len(result["recommendations"]), 0)
    
    @patch('test_run.genai.GenerativeModel')
    def test_test_run_with_context(self, mock_model):
        """Test test run with context"""
        mock_response = MagicMock()
        mock_response.text = json.dumps(self.valid_test_response)
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        context = {
            "code_quality_threshold": "high",
            "strict_mode": True
        }
        
        result = test_run(
            code=self.test_code_good,
            target_language="Python",
            selected_api="PI Web API",
            context=context
        )
        
        self.assertEqual(result["status"], "success")
        mock_instance.generate_content.assert_called_once()
    
    @patch('test_run.genai.GenerativeModel')
    def test_test_run_invalid_json(self, mock_model):
        """Test handling of invalid JSON response"""
        mock_response = MagicMock()
        mock_response.text = "Not valid JSON"
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        result = test_run(
            code=self.test_code_good,
            target_language="Python",
            selected_api="PI SDK"
        )
        
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["reasoning_type"], "error_recovery")
    
    @patch('test_run.genai.GenerativeModel')
    def test_test_run_missing_sections(self, mock_model):
        """Test handling of missing required sections"""
        incomplete_response = {
            "syntax_check": {"passed": True, "issues": []},
            "overall_result": "pass"
        }
        
        mock_response = MagicMock()
        mock_response.text = json.dumps(incomplete_response)
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        result = test_run(
            code=self.test_code_good,
            target_language="Python",
            selected_api="PI SDK"
        )
        
        self.assertEqual(result["status"], "error")
        self.assertIsNotNone(result["error_msg"])
    
    @patch('test_run.genai.GenerativeModel')
    def test_test_run_exception_handling(self, mock_model):
        """Test handling of exceptions during API call"""
        mock_instance = MagicMock()
        mock_instance.generate_content.side_effect = Exception("API error")
        mock_model.return_value = mock_instance
        
        result = test_run(
            code=self.test_code_good,
            target_language="Python",
            selected_api="PI SDK"
        )
        
        self.assertEqual(result["status"], "error")
        self.assertIn("API error", result["error_msg"])
    
    def test_perform_local_security_checks_hardcoded_password(self):
        """Test detection of hardcoded passwords"""
        code = 'password = "secret123"'
        issues = perform_local_security_checks(code)
        
        self.assertGreater(len(issues), 0)
        self.assertTrue(any("password" in issue.lower() for issue in issues))
    
    def test_perform_local_security_checks_api_key(self):
        """Test detection of hardcoded API keys"""
        code = 'api_key = "sk-1234567890"'
        issues = perform_local_security_checks(code)
        
        self.assertGreater(len(issues), 0)
    
    def test_perform_local_security_checks_sql_injection(self):
        """Test detection of potential SQL injection"""
        code = 'execute("SELECT * FROM table WHERE id = %s" % user_id)'
        issues = perform_local_security_checks(code)
        
        self.assertGreater(len(issues), 0)
        self.assertTrue(any("SQL injection" in issue for issue in issues))
    
    def test_perform_local_security_checks_eval(self):
        """Test detection of eval usage"""
        code = "result = eval(user_input)"
        issues = perform_local_security_checks(code)
        
        self.assertGreater(len(issues), 0)
        self.assertTrue(any("eval" in issue.lower() for issue in issues))
    
    def test_perform_local_security_checks_clean_code(self):
        """Test that clean code passes local security checks"""
        code = """def read_data(url):
    try:
        response = requests.get(url)
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None"""
        
        issues = perform_local_security_checks(code)
        self.assertEqual(len(issues), 0)
    
    def test_format_tool_output_success_pass(self):
        """Test formatting successful test result with pass"""
        result = {
            "status": "success",
            "syntax_check": {"passed": True, "issues": []},
            "logic_consistency": {"passed": True, "issues": []},
            "best_practices": {"passed": True, "issues": []},
            "error_handling": {"passed": True, "issues": []},
            "security": {"passed": True, "issues": []},
            "overall_result": "pass",
            "recommendations": [],
            "reasoning": "All checks passed",
            "reasoning_type": "validation_check",
            "error_msg": None
        }
        
        output = format_tool_output(result)
        
        self.assertIn("TOOL_RESULT: test_run", output)
        self.assertIn("status=success", output)
        self.assertIn("overall=pass", output)
        self.assertIn("All checks passed", output)
    
    def test_format_tool_output_success_fail(self):
        """Test formatting successful test result with fail"""
        result = {
            "status": "success",
            "syntax_check": {"passed": False, "issues": ["Error"]},
            "logic_consistency": {"passed": True, "issues": []},
            "best_practices": {"passed": True, "issues": []},
            "error_handling": {"passed": True, "issues": []},
            "security": {"passed": True, "issues": []},
            "overall_result": "fail",
            "recommendations": ["Fix error"],
            "reasoning": "Syntax errors found",
            "reasoning_type": "validation_check",
            "error_msg": None
        }
        
        output = format_tool_output(result)
        
        self.assertIn("TOOL_RESULT: test_run", output)
        self.assertIn("status=success", output)
        self.assertIn("overall=fail", output)
        self.assertIn("total_issues=1", output)
    
    def test_format_tool_output_error(self):
        """Test formatting error result"""
        result = {
            "status": "error",
            "syntax_check": None,
            "logic_consistency": None,
            "best_practices": None,
            "error_handling": None,
            "security": None,
            "overall_result": None,
            "recommendations": None,
            "reasoning": None,
            "reasoning_type": "error_recovery",
            "error_msg": "Test failed"
        }
        
        output = format_tool_output(result)
        
        self.assertIn("TOOL_RESULT: test_run", output)
        self.assertIn("status=error", output)
        self.assertIn("Test failed", output)
    
    @patch('test_run.genai.GenerativeModel')
    def test_test_run_security_violation_detected(self, mock_model):
        """Test that local security checks override AI results"""
        # AI response says security is okay
        ai_response = {
            "syntax_check": {"passed": True, "issues": []},
            "logic_consistency": {"passed": True, "issues": []},
            "best_practices": {"passed": True, "issues": []},
            "error_handling": {"passed": True, "issues": []},
            "security": {"passed": True, "issues": []},
            "overall_result": "pass",
            "recommendations": [],
            "reasoning": "All good"
        }
        
        mock_response = MagicMock()
        mock_response.text = json.dumps(ai_response)
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        # But code has hardcoded password
        bad_code = 'password = "hardcoded123"'
        
        result = test_run(
            code=bad_code,
            target_language="Python",
            selected_api="PI SDK"
        )
        
        self.assertEqual(result["status"], "success")
        # Should fail overall due to local security check
        self.assertEqual(result["overall_result"], "fail")
        self.assertFalse(result["security"]["passed"])
        self.assertGreater(len(result["security"]["issues"]), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

