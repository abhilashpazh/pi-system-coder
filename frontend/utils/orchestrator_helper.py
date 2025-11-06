"""
Orchestrator helper for Streamlit UI

Wraps the orchestrator backend with error handling and UI-friendly interfaces.
"""

import sys
import os
from typing import Dict, Any, Optional, Callable

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

try:
    # Import and reload to ensure we have the latest version with iteration_callback
    import importlib
    import backend.agent.orchestrator
    importlib.reload(backend.agent.orchestrator)
    from backend.agent.orchestrator import orchestrator
except ImportError as e:
    # Handle import errors gracefully
    print(f"Warning: Could not import orchestrator: {e}")
    orchestrator = None


def execute_pipeline(
    user_prompt: str,
    max_iterations: int = 20,
    status_callback: Optional[Callable[[Dict[str, Any]], None]] = None
) -> Dict[str, Any]:
    """
    Execute the pipeline using the orchestrator.
    
    Args:
        user_prompt: User's natural language request
        max_iterations: Maximum number of iterations (default: 20)
        status_callback: Optional callback function called after each iteration.
                        Receives iteration_data dictionary as argument.
    
    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - final_answer: Final code output (if successful)
        - iterations: List of iteration details
        - error_msg: Error message (if failed)
        - execution_time: Time taken in seconds (if available)
    """
    if orchestrator is None:
        return {
            "status": "error",
            "error_msg": "Orchestrator backend not available. Please check backend installation.",
            "iterations": []
        }
    
    try:
        # Track iterations for real-time updates
        all_iterations = []
        
        # Define iteration callback for real-time updates
        def iteration_callback(iteration_info: Dict[str, Any]):
            """Callback called after each iteration completes."""
            all_iterations.append(iteration_info)
            
            # Create status info from current iterations
            if status_callback:
                status_info = {
                    "iterations": all_iterations.copy(),
                    "current_tool": get_current_tool_from_iterations(all_iterations),
                    "current_stage": get_pipeline_stage_from_tool(get_current_tool_from_iterations(all_iterations)),
                    "iteration_count": len(all_iterations),
                    "latest_iteration": iteration_info
                }
                # Call the status callback to update UI
                status_callback(status_info)
        
        # Execute the orchestrator with iteration callback for real-time updates
        result = orchestrator(
            user_prompt, 
            max_iterations=max_iterations,
            iteration_callback=iteration_callback
        )
        
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "error_msg": f"Pipeline execution failed: {str(e)}",
            "iterations": [],
            "exception_type": type(e).__name__
        }


def parse_final_answer(final_answer: str) -> Dict[str, Any]:
    """
    Parse the final answer from the orchestrator.
    The final answer may contain code, file structure, or other output.
    
    Args:
        final_answer: Raw final answer string from orchestrator
    
    Returns:
        Dictionary with parsed components:
        - raw: Original final answer
        - code: Extracted code (if any)
        - files: List of files (if any)
        - metadata: Any metadata found
    """
    if not final_answer:
        return {
            "raw": "",
            "code": "",
            "files": [],
            "metadata": {}
        }
    
    # For Phase 2, we'll do basic parsing
    # Phase 4 will enhance this with better parsing
    
    # Try to extract code blocks
    import re
    code_blocks = re.findall(r'```(?:python|javascript|typescript|csharp|java|powershell|cpp)?\n?(.*?)```', final_answer, re.DOTALL)
    
    parsed = {
        "raw": final_answer,
        "code": code_blocks[0] if code_blocks else final_answer,
        "files": [],
        "metadata": {}
    }
    
    # Try to extract file information if present
    if "file:" in final_answer.lower() or "filename:" in final_answer.lower():
        # Basic file extraction (will be enhanced in Phase 4)
        file_pattern = r'(?:file|filename)[:\s]+([^\n]+)'
        files = re.findall(file_pattern, final_answer, re.IGNORECASE)
        parsed["files"] = files
    
    return parsed


def get_current_tool_from_iterations(iterations: list) -> Optional[str]:
    """
    Get the current tool being executed from iteration history.
    
    Args:
        iterations: List of iteration dictionaries from orchestrator
    
    Returns:
        Name of the current tool, or None if no tool is executing
    """
    if not iterations:
        return None
    
    # Get the last iteration
    last_iteration = iterations[-1]
    
    if last_iteration.get('tool_call'):
        return last_iteration['tool_call'].get('function')
    
    if last_iteration.get('final_answer'):
        return "completed"
    
    return None


def get_pipeline_stage_from_tool(tool_name: Optional[str]) -> Optional[int]:
    """
    Map tool name to pipeline stage number (1-5).
    
    Args:
        tool_name: Name of the tool
    
    Returns:
        Stage number (1-5) or None if unknown
    """
    tool_to_stage = {
        "api_selection": 1,
        "logic_creation": 2,
        "code_creation": 3,
        "test_run": 4,
        "file_output": 5
    }
    
    if tool_name in tool_to_stage:
        return tool_to_stage[tool_name]
    
    return None

