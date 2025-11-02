"""
API Selection Tool for PI System Code Generation Pipeline
 
This tool automatically selects the most appropriate PI System API based on user request.
Uses Google Gemini 2.0 Flash API for intelligent API selection.

Requirements: FR-001, FR-010, FR-030
"""

import os
import sys
import json
from typing import Dict, Any, Optional

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, rely on environment variables

# Import LLM configuration
from backend.src.config.llm_config import get_llm_config

# Get global LLM config instance
llm_config = get_llm_config()

# Available PI APIs
AVAILABLE_APIS = [
    "PI SDK",
    "PI AF SDK", 
    "PI Web API",
    "PI SQL Client"
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
        
        # Call LLM API
        response_text = llm_config.generate_content(
            full_prompt,
            temperature=0.3,
            max_tokens=500
        )
        
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
        # Format as JSON for structured data
        data_json = json.dumps({
            "selected_api": selection_result["selected_api"],
            "reasoning": selection_result["reasoning"]
        })
        return f"TOOL_RESULT: api_selection|status=success|data={data_json}"
    else:
        return f"TOOL_RESULT: api_selection|status=error|data=|error_msg={selection_result['error_msg']}"




