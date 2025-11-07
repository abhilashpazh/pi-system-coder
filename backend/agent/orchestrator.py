"""
Orchestrator for PI System Code Generation Pipeline

This module orchestrates the agentic LLM calls to Gemini 2.0 Flash API or OpenAI API,
coordinating the five-stage pipeline through iterative function calling.

Requirements: Agentic orchestration of pipeline tools via LLM APIs
"""

import os
import sys
import json
import re
import logging
from typing import Dict, Any, Optional, List, Callable

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, rely on environment variables

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress OpenAI SDK debug logs
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("openai._base_client").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# Import LLM configuration
from backend.src.config.llm_config import get_llm_config

# Get global LLM config instance
llm_config = get_llm_config()

# Import the five pipeline tools
from backend.src.tools.api_selection import api_selection, format_tool_output as format_api_output
from backend.src.tools.logic_creation import logic_creation, format_tool_output as format_logic_output
from backend.src.tools.code_creation import code_creation, format_tool_output as format_code_output
from backend.src.tools.test_run import test_run, format_tool_output as format_test_output
from backend.src.tools.file_output import file_output, format_tool_output as format_file_output

# Load system prompt from file
def load_system_prompt() -> str:
    """Load system prompt from system_prompt.md file"""
    try:
        prompt_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'system_prompt.md'
        )
        with open(prompt_path, 'r', encoding='utf-8') as f:
            logger.info("Successfully loaded system_prompt.md")
            return f.read()
    except Exception as e:
        logger.warning(f"Could not load system_prompt.md: {e}")
        return "You are a code-generation assistant for the AVEVA PI system."


def parse_function_call(response_text: str) -> Optional[Dict[str, Any]]:
    """
    Parse FUNCTION_CALL format from LLM response.
    
    Args:
        response_text: LLM response text
        
    Returns:
        Dictionary with function name and arguments, or None if not found
    """
    # Pattern: FUNCTION_CALL: function_name|arg1=val1|arg2=val2|...
    # Match the full function call line
    pattern = r'FUNCTION_CALL:\s*([^|\n]+)(.*)'
    match = re.search(pattern, response_text, re.DOTALL)
    
    if not match:
        return None
    
    function_name = match.group(1).strip()
    args_part = match.group(2).strip() if match.group(2) else ""
    
    # Parse arguments
    arguments = {}
    if args_part:
        # Split by | and parse key=value pairs
        for arg in args_part.split('|'):
            arg = arg.strip()
            if not arg:
                continue
                
            if '=' in arg:
                key, value = arg.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Try to parse JSON values (arrays, objects, booleans, null)
                parsed_value = try_parse_json(value)
                arguments[key] = parsed_value
    
    return {
        "function": function_name,
        "arguments": arguments
    }


def try_parse_json(value: str) -> Any:
    """
    Try to parse a value as JSON. If it fails, return the original string.
    Handles unquoted strings, JSON arrays, objects, booleans, null, etc.
    
    Args:
        value: String value to parse
        
    Returns:
        Parsed JSON object/list or original string
    """
    if not value:
        return value
        
    value = value.strip()
    
    # If it looks like a JSON array or object, try to parse it
    if (value.startswith('[') and value.endswith(']')) or \
       (value.startswith('{') and value.endswith('}')):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            pass
    
    # If it's a quoted string, unquote it
    if (value.startswith('"') and value.endswith('"')) or \
       (value.startswith("'") and value.endswith("'")):
        # Remove quotes but keep escaped quotes inside
        if value.startswith('"'):
            try:
                # Use JSON decoding to handle escape sequences properly
                return json.loads(value)
            except (json.JSONDecodeError, ValueError):
                # Fallback: just remove surrounding quotes
                return value[1:-1]
        else:
            # Single quotes - just remove them
            return value[1:-1]
    
    # Check for boolean/null values
    if value.lower() == 'true':
        return True
    if value.lower() == 'false':
        return False
    if value.lower() == 'null' or value.lower() == 'none':
        return None
    
    # Try parsing as JSON (might be an unquoted JSON value)
    try:
        return json.loads(value)
    except (json.JSONDecodeError, ValueError):
        # Not valid JSON, return as-is
        return value


def parse_final_answer(response_text: str) -> Optional[str]:
    """
    Parse FINAL_ANSWER format from LLM response.
    
    Args:
        response_text: LLM response text
    
    Returns:
        Final answer string, or None if not found
    """
    # Pattern: FINAL_ANSWER: <content>
    pattern = r'FINAL_ANSWER:\s*(.*)'
    match = re.search(pattern, response_text, re.DOTALL)
    
    if match:
        return match.group(1).strip()
    
    return None


def parse_tool_result_data(tool_result: str) -> Optional[Dict[str, Any]]:
    """
    Parse data from TOOL_RESULT format string.
    
    Args:
        tool_result: Tool result string in format: TOOL_RESULT: tool_name|status=success|data={json}
    
    Returns:
        Parsed data dictionary, or None if parsing fails
    """
    if not tool_result or not tool_result.startswith('TOOL_RESULT:'):
        return None
    
    try:
        # Extract data part: data={json}
        data_start = tool_result.find('data=') + 5
        if data_start == 4:  # Not found
            return None
        
        # Find the end of data (either | or end of string)
        data_end = tool_result.find('|', data_start)
        if data_end == -1:
            data_end = len(tool_result)
        
        data_json_str = tool_result[data_start:data_end]
        if not data_json_str:
            return None
        
        # Parse JSON
        return json.loads(data_json_str)
    except (json.JSONDecodeError, ValueError, IndexError) as e:
        logger.warning(f"Failed to parse tool result data: {e}")
        return None


def call_tool(function_name: str, arguments: Dict[str, Any]) -> str:
    """
    Execute a pipeline tool based on function name and arguments.
    
    Args:
        function_name: Name of the tool to call
        arguments: Tool arguments
        
    Returns:
        Formatted tool result string
    """
    try:
        if function_name == "api_selection":
            result = api_selection(
                user_request=arguments.get("user_prompt", ""),
                context=arguments.get("context")
            )
            return format_api_output(result)
            
        elif function_name == "logic_creation":
            result = logic_creation(
                user_request=arguments.get("user_prompt", ""),
                selected_api=arguments.get("selected_api", ""),
                context=arguments.get("context")
            )
            return format_logic_output(result)
            
        elif function_name == "code_creation":
            result = code_creation(
                pseudo_code=arguments.get("pseudo_code", []),
                data_structures=arguments.get("data_structures", []),
                error_handling_strategy=arguments.get("error_handling_strategy", ""),
                selected_api=arguments.get("selected_api", ""),
                target_language=arguments.get("target_language", arguments.get("language", "Python")),
                context=arguments.get("context")
            )
            return format_code_output(result)
            
        elif function_name == "test_run":
            result = test_run(
                code=arguments.get("code", ""),
                target_language=arguments.get("target_language", arguments.get("language", "Python")),
                selected_api=arguments.get("selected_api", ""),
                user_request=arguments.get("user_prompt", ""),
                context=arguments.get("context")
            )
            return format_test_output(result)
            
        elif function_name == "file_output":
            result = file_output(
                code=arguments.get("code", arguments.get("tested_code", "")),
                target_language=arguments.get("target_language", arguments.get("language", "Python")),
                selected_api=arguments.get("selected_api", ""),
                dependencies=arguments.get("dependencies", []),
                test_results=arguments.get("test_results"),
                context=arguments.get("context")
            )
            return format_file_output(result)
            
        else:
            return f"TOOL_RESULT: {function_name}|status=error|data=|error_msg=Unknown function: {function_name}"
            
    except Exception as e:
        return f"TOOL_RESULT: {function_name}|status=error|data=|error_msg=Tool execution failed: {str(e)}"


def orchestrator(user_prompt: str, max_iterations: int = 20, iteration_callback: Optional[Callable[[Dict[str, Any]], None]] = None) -> Dict[str, Any]:
    """
    Orchestrate agentic LLM calls to execute the five-stage pipeline.
    
    Args:
        user_prompt: User's natural language request
        max_iterations: Maximum number of iterations (default: 20)
        iteration_callback: Optional callback function called after each iteration.
                          Receives iteration_info dictionary as argument.
        
    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - final_answer: Final code output (if successful)
        - iterations: List of iteration details
        - error_msg: Error message (if failed)
    """
    # Load system prompt
    system_prompt = load_system_prompt()
    
    # Initialize conversation history
    iterations = []
    last_llm_response = ""
    last_tool_result = ""
    
    # Track language and API from previous steps
    tracked_language = None
    tracked_api = None
    
    # Iterate up to max_iterations times
    for i in range(max_iterations):
        iteration_num = i + 1
        logger.info(f"Starting iteration {iteration_num}/{max_iterations}")
        
        # Build the prompt for this iteration
        prompt_parts = [
            system_prompt,
            f"\n\nUser Request: {user_prompt}",
        ]
        
        if last_llm_response:
            prompt_parts.append(f"\n\nLast LLM Response:\n{last_llm_response}")
        
        if last_tool_result:
            prompt_parts.append(f"\n\nLast Tool Result:\n{last_tool_result}")
        
        prompt_parts.append("\n\nRespond with FUNCTION_CALL or FINAL_ANSWER.")
        
        full_prompt = "\n".join(prompt_parts)
        
        # Call LLM API (Gemini or OpenAI based on configuration)
        try:
            logger.debug(f"Calling {llm_config.provider.value.upper()} API for iteration {iteration_num}")
            last_llm_response = llm_config.generate_content(
                full_prompt,
                temperature=0.7,
                max_tokens=2000
            )
            logger.info(f"LLM Response received for iteration {iteration_num}")
            logger.debug(f"LLM Response: {last_llm_response[:500]}...")  # Log first 500 chars
            
        except Exception as e:
            logger.error(f"LLM API call failed for iteration {iteration_num}: {e}")
            return {
                "status": "error",
                "error_msg": f"LLM API call failed: {str(e)}",
                "iterations": iterations
            }
        
        # Parse the response
        iteration_info = {
            "iteration": iteration_num,
            "llm_response": last_llm_response,
            "tool_call": None,
            "tool_result": None
        }
        
        # Check if it's a final answer
        final_answer = parse_final_answer(last_llm_response)
        if final_answer:
            logger.info(f"Iteration {iteration_num}: FINAL_ANSWER received")
            iteration_info["final_answer"] = final_answer
            iterations.append(iteration_info)
            
            # Call iteration callback for final answer
            if iteration_callback:
                try:
                    iteration_callback(iteration_info)
                except Exception as e:
                    logger.warning(f"Error in iteration callback: {e}")
            
            return {
                "status": "success",
                "final_answer": final_answer,
                "iterations": iterations
            }
        
        # Check if it's a function call
        function_call = parse_function_call(last_llm_response)
        if function_call:
            logger.info(f"Iteration {iteration_num}: FUNCTION_CALL parsed: {function_call['function']}")
            iteration_info["tool_call"] = function_call
            
            # Extract language and API from code_creation results
            if function_call['function'] == 'code_creation':
                # Parse language from arguments
                lang_arg = function_call['arguments'].get('language') or function_call['arguments'].get('target_language')
                if lang_arg:
                    tracked_language = lang_arg
            
            # For test_run, use tracked language if not provided
            if function_call['function'] == 'test_run':
                if not function_call['arguments'].get('language') and not function_call['arguments'].get('target_language'):
                    if tracked_language:
                        function_call['arguments']['language'] = tracked_language
                        logger.info(f"Using tracked language '{tracked_language}' for test_run")
            
            # Execute the tool
            # Get context from last tool result (if available)
            context = None
            if last_tool_result:
                context = parse_tool_result_data(last_tool_result)
                if context:
                    logger.debug(f"Extracted context from last tool result: {list(context.keys())}")
            
            # Add user_prompt to arguments if not already present
            if 'user_prompt' not in function_call['arguments']:
                function_call['arguments']['user_prompt'] = user_prompt
            
            # Automatically inject context from last tool result if not already provided
            if context and ('context' not in function_call['arguments'] or function_call['arguments']['context'] is None):
                function_call['arguments']['context'] = context
                logger.debug(f"Injecting context from last tool result into {function_call['function']}")
            
            logger.debug(f"Executing tool: {function_call['function']} with args: {function_call['arguments']}")
            tool_result = call_tool(
                function_call["function"],
                function_call["arguments"]
            )
            
            # Extract language from code_creation tool result
            if function_call['function'] == 'code_creation' and tool_result.startswith('TOOL_RESULT: code_creation|status=success'):
                try:
                    # Parse the JSON data from tool result
                    import json
                    data_start = tool_result.find('data=') + 5
                    data_end = tool_result.find('|', data_start)
                    if data_end == -1:
                        data_end = len(tool_result)
                    data_json_str = tool_result[data_start:data_end]
                    data = json.loads(data_json_str)
                    # Look for language in the code context or extract from previous arguments
                    # We'll rely on the language from arguments since it's stored there
                except:
                    pass
            
            last_tool_result = tool_result
            iteration_info["tool_result"] = tool_result
            logger.info(f"Tool result received for iteration {iteration_num}")
            logger.debug(f"Tool Result: {tool_result[:500]}...")  # Log first 500 chars
            
            iterations.append(iteration_info)
            
            # Call iteration callback if provided (for real-time status updates)
            if iteration_callback:
                try:
                    iteration_callback(iteration_info)
                except Exception as e:
                    logger.warning(f"Error in iteration callback: {e}")
            
            # Continue to next iteration
            continue
        
        # If neither FINAL_ANSWER nor FUNCTION_CALL found
        logger.warning(f"Iteration {iteration_num}: Invalid response format. Expected FUNCTION_CALL or FINAL_ANSWER.")
        iterations.append(iteration_info)
        
        return {
            "status": "error",
            "error_msg": f"Iteration {iteration_num}: Invalid response format. Expected FUNCTION_CALL or FINAL_ANSWER.",
            "iterations": iterations
        }
    
    # Max iterations reached
    logger.error(f"Maximum iterations ({max_iterations}) reached without completing the pipeline")
    return {
        "status": "error",
        "error_msg": f"Maximum iterations ({max_iterations}) reached without completing the pipeline",
        "iterations": iterations
    }


if __name__ == "__main__":
    # Example usage
    user_prompt = (
        "Write a simple powershell script to connect to a PI collective using Powershell Tools for PI. Read value of all tags for a given pointsource."
    )
    
    logger.info("Orchestrator - PI System Code Generation Pipeline")
    logger.info("=" * 70)
    logger.info(f"User Request: {user_prompt}")
    
    result = orchestrator(user_prompt, max_iterations=20)
    
    logger.info("=" * 70)
    logger.info(f"Status: {result['status'].upper()}")
    logger.info(f"Iterations: {len(result.get('iterations', []))}")
    
    if result["status"] == "success":
        logger.info("Final Answer:")
        logger.info(result["final_answer"])
    else:
        logger.error(f"Error: {result['error_msg']}")
        logger.info(f"Completed {len(result.get('iterations', []))} iterations")
        
        # Show last few iterations for debugging
        if result.get('iterations'):
            logger.debug("Last Iterations:")
            for iteration in result['iterations'][-3:]:
                logger.debug(f"Iteration {iteration['iteration']}:")
                if iteration.get('tool_call'):
                    logger.debug(f"Tool Call: {iteration['tool_call']['function']}")
                if iteration.get('final_answer'):
                    logger.debug(f"Final Answer: {iteration['final_answer'][:200]}...")

