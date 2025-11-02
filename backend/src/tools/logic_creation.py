"""
Logic Creation Tool for PI System Code Generation Pipeline

This tool converts user requests into explicit, ordered step-by-step pseudo-code.
Uses Google Gemini 2.0 Flash API for intelligent logical decomposition.

Requirements: FR-002, FR-010, FR-021, FR-030
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

# Logic creation prompt template
LOGIC_CREATION_PROMPT = """You are an expert software engineer specializing in the PI System.

Selected API: {selected_api}
User Request: {user_request}

Convert this request into detailed, step-by-step pseudo-code that can be implemented using the selected API.

Your response MUST be a JSON object with the following structure:
{{
    "pseudo_code": [
        "Step 1: Description of the first logical operation",
        "Step 2: Description of the second logical operation",
        "..."
    ],
    "data_structures": [
        {{
            "name": "variable_name",
            "type": "data_type",
            "description": "purpose of this structure"
        }}
    ],
    "error_handling_strategy": "Description of how errors will be handled",
    "reasoning": "Brief explanation of the logical flow"
}}

Guidelines:
- Break down the request into atomic, unambiguous operations
- Order steps in correct logical sequence
- Define all necessary data structures
- Specify error handling at critical points
- Use language-agnostic pseudo-code (no specific syntax)
- Consider PI API best practices for {selected_api}

Return ONLY the JSON response, no additional text."""


def logic_creation(
    user_request: str,
    selected_api: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create detailed pseudo-code from user request and selected API.
    
    Args:
        user_request: Natural language description of what the user wants to do
        selected_api: The PI API selected by api_selection tool
        context: Optional context from previous interactions
        
    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - pseudo_code: List of step descriptions
        - data_structures: List of data structure definitions
        - error_handling_strategy: Description of error handling approach
        - reasoning: Explanation of the logic
        - reasoning_type: "logical_decomposition"
        - error_msg: Error message if status is error
    """
    try:
        # Build complete prompt
        full_prompt = LOGIC_CREATION_PROMPT.format(
            selected_api=selected_api,
            user_request=user_request
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
                "temperature": 0.5,  # Balanced creativity for logical decomposition
                "max_output_tokens": 1000,
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
        required_fields = ["pseudo_code", "data_structures", "error_handling_strategy", "reasoning"]
        for field in required_fields:
            if field not in result:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate pseudo_code is a list
        if not isinstance(result["pseudo_code"], list):
            raise ValueError("pseudo_code must be a list")
        
        if len(result["pseudo_code"]) == 0:
            raise ValueError("pseudo_code list cannot be empty")
        
        # Validate data_structures is a list
        if not isinstance(result["data_structures"], list):
            raise ValueError("data_structures must be a list")
        
        # Return success result
        return {
            "status": "success",
            "pseudo_code": result["pseudo_code"],
            "data_structures": result["data_structures"],
            "error_handling_strategy": result["error_handling_strategy"],
            "reasoning": result["reasoning"],
            "reasoning_type": "logical_decomposition",
            "error_msg": None
        }
        
    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "pseudo_code": None,
            "data_structures": None,
            "error_handling_strategy": None,
            "reasoning": None,
            "reasoning_type": "error_recovery",
            "error_msg": f"Failed to parse JSON response: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "pseudo_code": None,
            "data_structures": None,
            "error_handling_strategy": None,
            "reasoning": None,
            "reasoning_type": "error_recovery",
            "error_msg": f"Logic creation failed: {str(e)}"
        }


def format_tool_output(logic_result: Dict[str, Any]) -> str:
    """
    Format the logic creation result according to TOOL_RESULT specification.
    
    Args:
        logic_result: Result from logic_creation function
        
    Returns:
        Formatted JSON in TOOL_RESULT format
    """
    if logic_result["status"] == "success":
        # Format as JSON for structured data
        data_json = json.dumps({
            "pseudo_code": logic_result["pseudo_code"],
            "data_structures": logic_result["data_structures"],
            "error_handling_strategy": logic_result["error_handling_strategy"],
            "reasoning": logic_result["reasoning"]
        })
        return f"TOOL_RESULT: logic_creation|status=success|data={data_json}"
    else:
        return f"TOOL_RESULT: logic_creation|status=error|data=|error_msg={logic_result['error_msg']}"
