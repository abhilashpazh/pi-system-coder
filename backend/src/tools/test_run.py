"""
Test Run Tool for PI System Code Generation Pipeline

This tool performs quality checks, static analysis, and validation on generated code.
Uses Google Gemini 2.0 Flash API for intelligent code analysis.

Requirements: FR-004, FR-010, FR-032, FR-040
"""

import os
import json
import re
from typing import Dict, Any, Optional, List

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, rely on environment variables

try:
    from google import generativeai as genai
except ImportError:
    print("Warning: google-generativeai not installed. Using fallback.")
    genai = None

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
if GEMINI_API_KEY and genai:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"Warning: Failed to configure Gemini API: {e}")

# Test run prompt template
TEST_RUN_PROMPT = """You are an expert code quality analyst specializing in the PI System.

Generated Code:
```{target_language}
{code}
```

Language: {target_language}
Selected API: {selected_api}

Perform comprehensive code quality analysis and validation.

Your response MUST be a JSON object with the following structure:
{{
    "syntax_check": {{
        "passed": true/false,
        "issues": ["list of syntax errors if any"]
    }},
    "logic_consistency": {{
        "passed": true/false,
        "issues": ["list of logical inconsistencies if any"]
    }},
    "best_practices": {{
        "passed": true/false,
        "issues": ["list of best practice violations if any"]
    }},
    "error_handling": {{
        "passed": true/false,
        "issues": ["list of error handling issues if any"]
    }},
    "security": {{
        "passed": true/false,
        "issues": ["list of security issues if any"]
    }},
    "overall_result": "pass/fail",
    "recommendations": ["list of recommendations for improvement"],
    "reasoning": "Brief explanation of test results"
}}

Check for:
1. Syntax errors and basic code correctness
2. Logical consistency and proper flow
3. {selected_api} best practices compliance
4. Adequate error handling coverage
5. Security issues (hardcoded credentials, SQL injection, etc.)
6. Code quality issues
7. Resource management (connections, streams, etc.)

Return ONLY the JSON response, no additional text."""


def test_run(
    code: str,
    target_language: str,
    selected_api: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Perform quality checks and validation on generated code.
    
    Args:
        code: Generated implementation code
        target_language: Programming language of the code
        selected_api: The PI API used in the code
        context: Optional context from previous interactions
        
    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - syntax_check: Dictionary with passed flag and issues
        - logic_consistency: Dictionary with passed flag and issues
        - best_practices: Dictionary with passed flag and issues
        - error_handling: Dictionary with passed flag and issues
        - security: Dictionary with passed flag and issues
        - overall_result: "pass" or "fail"
        - recommendations: List of improvement recommendations
        - reasoning: Explanation of test results
        - reasoning_type: "validation_check"
        - error_msg: Error message if status is error
    """
    try:
        # Build complete prompt
        full_prompt = TEST_RUN_PROMPT.format(
            target_language=target_language,
            code=code,
            selected_api=selected_api
        )
        
        # Add context if available
        if context:
            context_str = json.dumps(context, indent=2)
            full_prompt += f"\n\nAdditional Context:\n{context_str}"
        
        # Call Gemini API
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(
            full_prompt,
            generation_config={
                "temperature": 0.2,  # Very low temperature for consistent analysis
                "max_output_tokens": 1500,
            }
        )
        
        # Parse response
        response_text = response.text.strip()
        
        # Extract JSON from response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start == -1 or json_end == 0:
            raise ValueError("No JSON found in response")
        
        result = json.loads(response_text[json_start:json_end])
        
        # Validate result structure
        required_sections = ["syntax_check", "logic_consistency", "best_practices", 
                           "error_handling", "security", "overall_result", "recommendations", "reasoning"]
        
        for section in required_sections:
            if section not in result:
                raise ValueError(f"Missing required section: {section}")
        
        # Validate check sections have passed flag
        check_sections = ["syntax_check", "logic_consistency", "best_practices", "error_handling", "security"]
        for section in check_sections:
            if "passed" not in result[section]:
                raise ValueError(f"Missing 'passed' field in {section}")
            if "issues" not in result[section]:
                raise ValueError(f"Missing 'issues' field in {section}")
        
        # Validate overall_result is pass or fail
        if result["overall_result"] not in ["pass", "fail"]:
            raise ValueError("overall_result must be 'pass' or 'fail'")
        
        # Perform additional local security checks
        local_security_issues = perform_local_security_checks(code)
        if local_security_issues:
            result["security"]["issues"].extend(local_security_issues)
            result["security"]["passed"] = False
            result["overall_result"] = "fail"
        
        # Return success result
        return {
            "status": "success",
            "syntax_check": result["syntax_check"],
            "logic_consistency": result["logic_consistency"],
            "best_practices": result["best_practices"],
            "error_handling": result["error_handling"],
            "security": result["security"],
            "overall_result": result["overall_result"],
            "recommendations": result["recommendations"],
            "reasoning": result["reasoning"],
            "reasoning_type": "validation_check",
            "error_msg": None
        }
        
    except json.JSONDecodeError as e:
        return {
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
            "error_msg": f"Failed to parse JSON response: {str(e)}"
        }
    except Exception as e:
        return {
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
            "error_msg": f"Test run failed: {str(e)}"
        }


def perform_local_security_checks(code: str) -> List[str]:
    """
    Perform local security checks on the code.
    
    Args:
        code: Code to check
        
    Returns:
        List of security issues found
    """
    issues = []
    
    # Check for hardcoded credentials
    credential_patterns = [
        r'password\s*=\s*["\'][^"\']+["\']',
        r'password\s*:\s*["\'][^"\']+["\']',
        r'api_key\s*=\s*["\'][^"\']+["\']',
        r'auth_token\s*=\s*["\'][^"\']+["\']',
        r'secret\s*=\s*["\'][^"\']+["\']',
    ]
    
    for pattern in credential_patterns:
        matches = re.finditer(pattern, code, re.IGNORECASE)
        for match in matches:
            issues.append(f"Potential hardcoded credential found: {match.group()[:50]}")
    
    # Check for SQL injection risks
    sql_patterns = [
        r'execute\(["\'][^"\']*%\s*\w+',
        r'query\(["\'][^"\']*%\s*\w+',
        r'execute\(["\'][^"\']+\+.*\)',
        r'query\(["\'][^"\']+\+.*\)',
    ]
    
    for pattern in sql_patterns:
        matches = re.finditer(pattern, code, re.IGNORECASE)
        for match in matches:
            issues.append(f"Potential SQL injection risk: string formatting in SQL query")
    
    # Check for eval/exec usage
    dangerous_patterns = [
        r'eval\s*\(',
        r'exec\s*\(',
        r'__import__\s*\(',
    ]
    
    for pattern in dangerous_patterns:
        matches = re.finditer(pattern, code, re.IGNORECASE)
        for match in matches:
            issues.append(f"Dangerous code execution pattern: {match.group()}")
    
    return issues


def format_tool_output(test_result: Dict[str, Any]) -> str:
    """
    Format the test run result according to TOOL_RESULT specification.
    
    Args:
        test_result: Result from test_run function
        
    Returns:
        Formatted string in TOOL_RESULT format
    """
    if test_result["status"] == "success":
        # Build comprehensive data string
        data_parts = [
            f"overall={test_result['overall_result']}",
            f"syntax={test_result['syntax_check']['passed']}",
            f"logic={test_result['logic_consistency']['passed']}",
            f"practices={test_result['best_practices']['passed']}",
            f"errors={test_result['error_handling']['passed']}",
            f"security={test_result['security']['passed']}",
            f"reasoning={test_result['reasoning']}"
        ]
        
        # Count total issues
        total_issues = (
            len(test_result["syntax_check"]["issues"]) +
            len(test_result["logic_consistency"]["issues"]) +
            len(test_result["best_practices"]["issues"]) +
            len(test_result["error_handling"]["issues"]) +
            len(test_result["security"]["issues"])
        )
        
        if total_issues > 0:
            issues_str = f"|total_issues={total_issues}"
        else:
            issues_str = ""
        
        data_str = "|".join(data_parts) + issues_str
        
        return f"TOOL_RESULT: test_run|status=success|data={data_str}"
    else:
        return f"TOOL_RESULT: test_run|status=error|data=|error_msg={test_result['error_msg']}"


if __name__ == "__main__":
    # Example usage
    test_code = """import requests
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

    print("Test Run Tool - Example")
    print("=" * 60)
    
    result = test_run(
        code=test_code,
        target_language="Python",
        selected_api="PI Web API"
    )
    
    if result["status"] == "success":
        print(f"\nOverall Result: {result['overall_result'].upper()}")
        print(f"\nSyntax Check: {'PASS' if result['syntax_check']['passed'] else 'FAIL'}")
        if result["syntax_check"]["issues"]:
            print("  Issues:")
            for issue in result["syntax_check"]["issues"]:
                print(f"    - {issue}")
        
        print(f"\nLogic Consistency: {'PASS' if result['logic_consistency']['passed'] else 'FAIL'}")
        print(f"\nBest Practices: {'PASS' if result['best_practices']['passed'] else 'FAIL'}")
        print(f"\nError Handling: {'PASS' if result['error_handling']['passed'] else 'FAIL'}")
        print(f"\nSecurity: {'PASS' if result['security']['passed'] else 'FAIL'}")
        
        if result["recommendations"]:
            print("\nRecommendations:")
            for rec in result["recommendations"]:
                print(f"  - {rec}")
        
        print(f"\nReasoning: {result['reasoning']}")
    else:
        print(f"\nError: {result['error_msg']}")
    
    print("-" * 60)

