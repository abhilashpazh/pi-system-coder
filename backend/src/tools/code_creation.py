"""
Code Creation Tool for PI System Code Generation Pipeline

This tool generates implementation code from pseudo-code in the requested language.
Uses Google Gemini 2.0 Flash API for intelligent code generation.

Requirements: FR-003, FR-010, FR-021, FR-050
"""

import os
import json
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

# Supported languages and their extensions
SUPPORTED_LANGUAGES = {
    "C#": ".cs",
    "Python": ".py",
    "VB.NET": ".vb",
    "JavaScript": ".js",
    "TypeScript": ".ts",
    "Java": ".java",
    "PowerShell": ".ps1",
    "C++": ".cpp"
}

# Code creation prompt template
CODE_CREATION_PROMPT = """You are an expert software engineer specializing in the PI System and {target_language} programming.

Selected API: {selected_api}
Target Language: {target_language}

Pseudo-Code Steps:
{formatted_steps}

Data Structures:
{formatted_data_structures}

Error Handling Strategy:
{error_handling_strategy}

Generate complete, production-ready implementation code in {target_language} that:
1. Implements ALL pseudo-code steps in order
2. Uses proper {target_language} syntax and conventions
3. Implements the error handling strategy described
4. Uses appropriate {selected_api} patterns and best practices
5. Includes proper imports/using statements
6. Adds code comments for clarity
7. NEVER includes hardcoded credentials or secrets
8. Uses configuration variables for server names, usernames, passwords

Your response MUST be a JSON object with the following structure:
{{
    "code": "Complete implementation code as a string",
    "dependencies": [
        "Required package/library 1",
        "Required package/library 2"
    ],
    "usage_example": "Brief example of how to use this code",
    "reasoning": "Brief explanation of implementation choices"
}}

Code Quality Requirements:
- Syntactically correct
- Follows language best practices
- Proper resource management (connections, streams, etc.)
- Secure credential handling
- Adequate error handling
- Clear variable naming
- Helpful comments

Return ONLY the JSON response, no additional text."""


def code_creation(
    pseudo_code: List[str],
    data_structures: List[Dict[str, Any]],
    error_handling_strategy: str,
    selected_api: str,
    target_language: str = "Python",
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate implementation code from pseudo-code in the target language.
    
    Args:
        pseudo_code: List of step descriptions from logic_creation
        data_structures: List of data structure definitions
        error_handling_strategy: Error handling approach description
        selected_api: The PI API to use
        target_language: Programming language for output (default: Python)
        context: Optional context from previous interactions
        
    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - code: Generated implementation code
        - dependencies: List of required dependencies
        - usage_example: Usage example
        - reasoning: Explanation of implementation
        - reasoning_type: "implementation"
        - error_msg: Error message if status is error
    """
    try:
        # Validate target language
        if target_language not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language: {target_language}")
        
        # Format pseudo-code steps
        formatted_steps = "\n".join([f"{i+1}. {step}" for i, step in enumerate(pseudo_code)])
        
        # Format data structures
        formatted_data_structures = json.dumps(data_structures, indent=2)
        
        # Build complete prompt
        full_prompt = CODE_CREATION_PROMPT.format(
            target_language=target_language,
            selected_api=selected_api,
            formatted_steps=formatted_steps,
            formatted_data_structures=formatted_data_structures,
            error_handling_strategy=error_handling_strategy
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
                "temperature": 0.3,  # Lower temperature for more deterministic, correct code
                "max_output_tokens": 2000,
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
        required_fields = ["code", "dependencies", "usage_example", "reasoning"]
        for field in required_fields:
            if field not in result:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate code is non-empty
        if not result["code"] or not result["code"].strip():
            raise ValueError("Generated code is empty")
        
        # Validate dependencies is a list
        if not isinstance(result["dependencies"], list):
            raise ValueError("dependencies must be a list")
        
        # Return success result
        return {
            "status": "success",
            "code": result["code"],
            "dependencies": result["dependencies"],
            "usage_example": result["usage_example"],
            "reasoning": result["reasoning"],
            "reasoning_type": "implementation",
            "error_msg": None
        }
        
    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "code": None,
            "dependencies": None,
            "usage_example": None,
            "reasoning": None,
            "reasoning_type": "error_recovery",
            "error_msg": f"Failed to parse JSON response: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "code": None,
            "dependencies": None,
            "usage_example": None,
            "reasoning": None,
            "reasoning_type": "error_recovery",
            "error_msg": f"Code creation failed: {str(e)}"
        }


def format_tool_output(code_result: Dict[str, Any]) -> str:
    """
    Format the code creation result according to TOOL_RESULT specification.
    
    Args:
        code_result: Result from code_creation function
        
    Returns:
        Formatted string in TOOL_RESULT format
    """
    if code_result["status"] == "success":
        # Escape the code for safe transmission
        code_escaped = code_result["code"].replace("|", "\\|").replace("\n", "\\n")
        
        # Format dependencies as JSON string
        dependencies_str = json.dumps(code_result["dependencies"])
        
        # Build data string
        data_str = f"code={code_escaped}|dependencies={dependencies_str}|usage={code_result['usage_example']}|reasoning={code_result['reasoning']}"
        
        return f"TOOL_RESULT: code_creation|status=success|data={data_str}"
    else:
        return f"TOOL_RESULT: code_creation|status=error|data=|error_msg={code_result['error_msg']}"


if __name__ == "__main__":
    # Example usage
    test_pseudo_code = [
        "Connect to PI Data Archive",
        "Authenticate with credentials",
        "Query tag by name",
        "Read current value",
        "Handle errors and cleanup"
    ]
    
    test_data_structures = [
        {
            "name": "server",
            "type": "PIServer",
            "description": "PI Data Archive server connection"
        }
    ]
    
    test_error_handling = "Try-catch around all operations, proper cleanup in finally block"
    
    test_cases = [
        {"language": "Python", "api": "PI Web API"},
        {"language": "C#", "api": "PI SDK"},
        {"language": "JavaScript", "api": "PI Web API"},
    ]
    
    print("Code Creation Tool - Test Run")
    print("=" * 60)
    
    for test in test_cases:
        print(f"\nTarget Language: {test['language']}")
        print(f"Selected API: {test['api']}")
        
        result = code_creation(
            pseudo_code=test_pseudo_code,
            data_structures=test_data_structures,
            error_handling_strategy=test_error_handling,
            selected_api=test["api"],
            target_language=test["language"]
        )
        
        if result["status"] == "success":
            print(f"\nDependencies ({len(result['dependencies'])}):")
            for dep in result["dependencies"]:
                print(f"  - {dep}")
            
            print(f"\nUsage Example: {result['usage_example']}")
            print(f"Reasoning: {result['reasoning']}")
            print(f"\nGenerated Code Preview (first 200 chars):")
            print(result["code"][:200] + "...")
        else:
            print(f"\nError: {result['error_msg']}")
        
        print("-" * 60)

