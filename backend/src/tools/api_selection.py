"""
API Selection Tool for PI System Code Generation Pipeline

This tool automatically selects the most appropriate PI System API based on user request.
Uses Google Gemini 2.0 Flash API for intelligent API selection.

Requirements: FR-001, FR-010, FR-030
"""

import os
import json
from typing import Dict, Any, Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, rely on environment variables

# Configure Gemini API
try:
    from google import generativeai as genai
except ImportError:
    print("Warning: google-generativeai not installed. Using fallback.")
    genai = None

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
if GEMINI_API_KEY and genai:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"Warning: Failed to configure Gemini API: {e}")

# Available PI APIs
AVAILABLE_APIS = [
    "PI SDK",
    "PI AF SDK", 
    "PI Web API",
    "PI SQL Client",
    "Powershell Tools for PI"
]

# API selection prompt template
API_SELECTION_PROMPT = """You are an expert PI System API selection assistant.

Available PI System APIs:
1. PI SDK - Server-side, high performance data access, reads/writes to PI Data Archive
2. PI AF SDK - Asset Framework operations, hierarchical data navigation, asset-centric access
3. PI Web API - RESTful, cross-platform, web/mobile applications, microservices
4. PI SQL Client - Direct database queries, custom reporting, data mining

User Request: {user_request}

Select the MOST APPROPRIATE API based on the user's request.

Your response MUST be a JSON object with the following structure:
{{
    "selected_api": "API_NAME",
    "reasoning": "Brief explanation of why this API is the best choice"
}}

Consider:
- Performance requirements
- Platform compatibility needs
- Type of operations needed (read, write, query, etc.)
- Deployment environment
- Integration requirements

Return ONLY the JSON response, no additional text."""


def api_selection(user_request: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Select the most appropriate PI System API based on user request.
    
    Args:
        user_request: Natural language description of what the user wants to do
        context: Optional context from previous interactions
        
    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - selected_api: Name of selected API
        - reasoning: Explanation of selection
        - reasoning_type: "api_selection"
        - error_msg: Error message if status is error
    """
    try:
        # Prepare context if available
        context_str = ""
        if context:
            context_str = f"\nPrevious context: {json.dumps(context, indent=2)}"
        
        # Build complete prompt
        full_prompt = API_SELECTION_PROMPT.format(
            user_request=user_request + context_str
        )
        
        # Call Gemini API
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(
            full_prompt,
            generation_config={
                "temperature": 0.3,  # Lower temperature for more deterministic selection
                "max_output_tokens": 500,
            }
        )
        
        # Parse response
        response_text = response.text.strip()
        
        # Extract JSON from response (in case there's extra text)
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start == -1 or json_end == 0:
            raise ValueError("No JSON found in response")
        
        result = json.loads(response_text[json_start:json_end])
        
        # Validate result
        if "selected_api" not in result or "reasoning" not in result:
            raise ValueError("Invalid response structure")
        
        selected_api = result["selected_api"]
        
        # Verify API is in available list
        if selected_api not in AVAILABLE_APIS:
            raise ValueError(f"Unknown API selected: {selected_api}")
        
        # Return success result
        return {
            "status": "success",
            "selected_api": selected_api,
            "reasoning": result["reasoning"],
            "reasoning_type": "api_selection",
            "error_msg": None
        }
        
    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "selected_api": None,
            "reasoning": None,
            "reasoning_type": "error_recovery",
            "error_msg": f"Failed to parse JSON response: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "selected_api": None,
            "reasoning": None,
            "reasoning_type": "error_recovery",
            "error_msg": f"API selection failed: {str(e)}"
        }


def format_tool_output(selection_result: Dict[str, Any]) -> str:
    """
    Format the API selection result according to TOOL_RESULT specification.
    
    Args:
        selection_result: Result from api_selection function
        
    Returns:
        Formatted string in TOOL_RESULT format
    """
    if selection_result["status"] == "success":
        data_str = f"{selection_result['selected_api']}||reasoning={selection_result['reasoning']}"
        return f"TOOL_RESULT: api_selection|status=success|data={data_str}"
    else:
        return f"TOOL_RESULT: api_selection|status=error|data=|error_msg={selection_result['error_msg']}"


if __name__ == "__main__":
    # Example usage
    test_requests = [
        "Create a function to read PI tag values for the last 24 hours",
        "I need to query asset hierarchies and navigate through AF databases",
        "Build a web dashboard that displays PI data to users",
        "Generate custom SQL reports from PI database",
    ]
    
    print("API Selection Tool - Test Run")
    print("=" * 60)
    
    for request in test_requests:
        print(f"\nUser Request: {request}")
        result = api_selection(request)
        print(f"Selected API: {result['selected_api']}")
        print(f"Reasoning: {result['reasoning']}")
        print(f"Status: {result['status']}")
        print("-" * 60)

