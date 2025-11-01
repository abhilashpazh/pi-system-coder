"""
MCP Server for PI System Code Generation Pipeline

This module creates an MCP (Model Context Protocol) server that exposes
all five pipeline tools as MCP resources and tools.

Requirements: Expose pipeline tools via MCP protocol
"""

import sys
import os
from typing import Any, Dict, List, Optional
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)

# Import the five pipeline tools
from backend.src.tools.api_selection import api_selection
from backend.src.tools.logic_creation import logic_creation
from backend.src.tools.code_creation import code_creation
from backend.src.tools.test_run import test_run
from backend.src.tools.file_output import file_output, write_files_to_disk

# Create the MCP server instance
app = Server("pi-system-code-generator")


@app.list_resources()
async def list_resources() -> List[Resource]:
    """
    List available resources (pipeline stages).
    
    Returns:
        List of Resource objects representing the pipeline stages
    """
    return [
        Resource(
            uri="pi://pipeline/stage1",
            name="API Selection",
            description="Stage 1: Select the most appropriate PI System API",
            mimeType="application/json"
        ),
        Resource(
            uri="pi://pipeline/stage2",
            name="Logic Creation",
            description="Stage 2: Create step-by-step pseudo-code logic",
            mimeType="application/json"
        ),
        Resource(
            uri="pi://pipeline/stage3",
            name="Code Creation",
            description="Stage 3: Generate implementation code",
            mimeType="application/json"
        ),
        Resource(
            uri="pi://pipeline/stage4",
            name="Test Run",
            description="Stage 4: Validate and test generated code",
            mimeType="application/json"
        ),
        Resource(
            uri="pi://pipeline/stage5",
            name="File Output",
            description="Stage 5: Package code with documentation",
            mimeType="application/json"
        ),
    ]


@app.list_tools()
async def list_tools() -> List[Tool]:
    """
    List available tools (pipeline functions).
    
    Returns:
        List of Tool objects for each pipeline function
    """
    return [
        Tool(
            name="api_selection",
            description="Select the most appropriate PI System API based on user request. Available APIs: PI SDK, PI AF SDK, PI Web API, PI SQL Client.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_request": {
                        "type": "string",
                        "description": "Natural language description of what the user wants to do with PI System"
                    },
                    "context": {
                        "type": "object",
                        "description": "Optional context from previous interactions",
                        "properties": {}
                    }
                },
                "required": ["user_request"]
            }
        ),
        Tool(
            name="logic_creation",
            description="Convert user request into explicit, ordered step-by-step pseudo-code with data structures and error handling strategy.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_request": {
                        "type": "string",
                        "description": "Natural language description of the task"
                    },
                    "selected_api": {
                        "type": "string",
                        "description": "The PI API selected by api_selection tool",
                        "enum": ["PI SDK", "PI AF SDK", "PI Web API", "PI SQL Client"]
                    },
                    "context": {
                        "type": "object",
                        "description": "Optional context from previous interactions",
                        "properties": {}
                    }
                },
                "required": ["user_request", "selected_api"]
            }
        ),
        Tool(
            name="code_creation",
            description="Generate implementation code from pseudo-code in the requested programming language (Python, C#, JavaScript, etc.).",
            inputSchema={
                "type": "object",
                "properties": {
                    "pseudo_code": {
                        "type": "array",
                        "description": "List of step descriptions from logic_creation",
                        "items": {"type": "string"}
                    },
                    "data_structures": {
                        "type": "array",
                        "description": "List of data structure definitions",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "type": {"type": "string"},
                                "description": {"type": "string"}
                            }
                        }
                    },
                    "error_handling_strategy": {
                        "type": "string",
                        "description": "Error handling approach description"
                    },
                    "selected_api": {
                        "type": "string",
                        "enum": ["PI SDK", "PI AF SDK", "PI Web API", "PI SQL Client"]
                    },
                    "target_language": {
                        "type": "string",
                        "description": "Programming language for output",
                        "enum": ["Python", "C#", "VB.NET", "JavaScript", "TypeScript", "Java", "PowerShell", "C++"],
                        "default": "Python"
                    },
                    "context": {
                        "type": "object",
                        "description": "Optional context from previous interactions"
                    }
                },
                "required": ["pseudo_code", "data_structures", "error_handling_strategy", "selected_api"]
            }
        ),
        Tool(
            name="test_run",
            description="Perform quality checks, static analysis, and validation on generated code. Returns comprehensive test results.",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Generated implementation code to test"
                    },
                    "target_language": {
                        "type": "string",
                        "enum": ["Python", "C#", "VB.NET", "JavaScript", "TypeScript", "Java", "PowerShell", "C++"]
                    },
                    "selected_api": {
                        "type": "string",
                        "enum": ["PI SDK", "PI AF SDK", "PI Web API", "PI SQL Client"]
                    },
                    "context": {
                        "type": "object",
                        "description": "Optional context from previous interactions"
                    }
                },
                "required": ["code", "target_language", "selected_api"]
            }
        ),
        Tool(
            name="file_output",
            description="Package and deliver final code with metadata, documentation, and helper files. Creates complete ready-to-use module.",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Generated implementation code"
                    },
                    "target_language": {
                        "type": "string",
                        "enum": ["Python", "C#", "VB.NET", "JavaScript", "TypeScript", "Java", "PowerShell", "C++"]
                    },
                    "selected_api": {
                        "type": "string",
                        "enum": ["PI SDK", "PI AF SDK", "PI Web API", "PI SQL Client"]
                    },
                    "dependencies": {
                        "type": "array",
                        "description": "List of required dependencies/packages",
                        "items": {"type": "string"}
                    },
                    "test_results": {
                        "type": "object",
                        "description": "Results from test_run tool (optional)",
                        "properties": {}
                    },
                    "context": {
                        "type": "object",
                        "description": "Optional context from previous interactions"
                    }
                },
                "required": ["code", "target_language", "selected_api", "dependencies"]
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Execute a pipeline tool based on the tool name and arguments.
    
    Args:
        name: Name of the tool to call
        arguments: Tool arguments
        
    Returns:
        List of TextContent with tool results
    """
    try:
        if name == "api_selection":
            result = api_selection(
                user_request=arguments.get("user_request"),
                context=arguments.get("context")
            )
            
        elif name == "logic_creation":
            result = logic_creation(
                user_request=arguments.get("user_request"),
                selected_api=arguments.get("selected_api"),
                context=arguments.get("context")
            )
            
        elif name == "code_creation":
            result = code_creation(
                pseudo_code=arguments.get("pseudo_code"),
                data_structures=arguments.get("data_structures"),
                error_handling_strategy=arguments.get("error_handling_strategy"),
                selected_api=arguments.get("selected_api"),
                target_language=arguments.get("target_language", "Python"),
                context=arguments.get("context")
            )
            
        elif name == "test_run":
            result = test_run(
                code=arguments.get("code"),
                target_language=arguments.get("target_language"),
                selected_api=arguments.get("selected_api"),
                context=arguments.get("context")
            )
            
        elif name == "file_output":
            result = file_output(
                code=arguments.get("code"),
                target_language=arguments.get("target_language"),
                selected_api=arguments.get("selected_api"),
                dependencies=arguments.get("dependencies"),
                test_results=arguments.get("test_results"),
                context=arguments.get("context")
            )
            
        else:
            result = {
                "status": "error",
                "error_msg": f"Unknown tool: {name}"
            }
        
        # Format result as JSON string
        result_json = json.dumps(result, indent=2, default=str)
        
        return [TextContent(
            type="text",
            text=result_json
        )]
        
    except Exception as e:
        error_result = {
            "status": "error",
            "error_msg": f"Tool execution failed: {str(e)}",
            "tool_name": name
        }
        return [TextContent(
            type="text",
            text=json.dumps(error_result, indent=2)
        )]


async def main():
    """
    Main entry point for the MCP server.
    Runs the server using stdio transport.
    """
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

