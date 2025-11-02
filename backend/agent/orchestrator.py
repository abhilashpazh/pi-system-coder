"""
Orchestrator for PI System Code Generation Pipeline

This module orchestrates the agentic LLM calls to Gemini 2.0 Flash API,
coordinating the five-stage pipeline through iterative function calling.

Requirements: Agentic orchestration of pipeline tools via Gemini API
"""

import os
import sys
import json
import re
import logging
from typing import Dict, Any, Optional, List

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

try:
    from google import generativeai as genai
except ImportError:
    logger.warning("google-generativeai not installed. Using fallback.")
    genai = None

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
if GEMINI_API_KEY and genai:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e:
        logger.warning(f"Failed to configure Gemini API: {e}")

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
    pattern = r'FUNCTION_CALL:\s*([^|\n]+)(?:\|([^|\n]+=.*))*'
    match = re.search(pattern, response_text)
    
    if not match:
        return None
    
    function_name = match.group(1).strip()
    arguments_str = match.group(2) if match.group(2) else ""
    
    # Parse arguments
    arguments = {}
    if arguments_str:
        # Split by | and parse key=value pairs
        for arg in arguments_str.split('|'):
            if '=' in arg:
                key, value = arg.split('=', 1)
                arguments[key.strip()] = value.strip()
    
    return {
        "function": function_name,
        "arguments": arguments
    }


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


def orchestrator(user_prompt: str, max_iterations: int = 10) -> Dict[str, Any]:
    """
    Orchestrate agentic LLM calls to execute the five-stage pipeline.
    
    Args:
        user_prompt: User's natural language request
        max_iterations: Maximum number of iterations (default: 10)
        
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
        
        # Call Gemini API
        if not genai:
            logger.error("Gemini API not configured")
            return {
                "status": "error",
                "error_msg": "Gemini API not configured",
                "iterations": iterations
            }
        
        try:
            logger.debug(f"Calling Gemini API for iteration {iteration_num}")
            model = genai.GenerativeModel(GEMINI_MODEL)
            response = model.generate_content(
                full_prompt,
                generation_config={
                    "temperature": 0.7,  # Balanced for reasoning
                    "max_output_tokens": 2000,
                }
            )
            
            last_llm_response = response.text.strip()
            logger.info(f"LLM Response received for iteration {iteration_num}")
            logger.debug(f"LLM Response: {last_llm_response[:500]}...")  # Log first 500 chars
            
        except Exception as e:
            logger.error(f"Gemini API call failed for iteration {iteration_num}: {e}")
            return {
                "status": "error",
                "error_msg": f"Gemini API call failed: {str(e)}",
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
            
            # Execute the tool
            logger.debug(f"Executing tool: {function_call['function']} with args: {function_call['arguments']}")
            tool_result = call_tool(
                function_call["function"],
                function_call["arguments"]
            )
            last_tool_result = tool_result
            iteration_info["tool_result"] = tool_result
            logger.info(f"Tool result received for iteration {iteration_num}")
            logger.debug(f"Tool Result: {tool_result[:500]}...")  # Log first 500 chars
            
            iterations.append(iteration_info)
            
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
        "Write a simple powershell script to connect to a PI server using Powershell Tools for PI."
    )
    
    logger.info("Orchestrator - PI System Code Generation Pipeline")
    logger.info("=" * 70)
    logger.info(f"User Request: {user_prompt}")
    
    result = orchestrator(user_prompt, max_iterations=10)
    
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

