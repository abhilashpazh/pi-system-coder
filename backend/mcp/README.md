# MCP Server for PI System Code Generation Pipeline

This directory contains the Model Context Protocol (MCP) server that exposes all five pipeline tools as MCP resources and tools.

## Overview

The MCP server allows AI assistants and other MCP clients to access and use the PI System Code Generation Pipeline tools through the standardized MCP protocol.

## Files

- `server.py` - Main MCP server implementation
- `__init__.py` - Package initialization

## Exposed Tools

The server exposes the following five pipeline tools:

1. **api_selection** - Select appropriate PI System API
2. **logic_creation** - Create step-by-step pseudo-code logic
3. **code_creation** - Generate implementation code
4. **test_run** - Validate and test generated code
5. **file_output** - Package code with documentation

## Usage

### Running the MCP Server

```bash
python -m backend.mcp.server
```

### MCP Client Integration

The server uses stdio transport and can be connected to any MCP-compatible client:

```python
from mcp.client.stdio import stdio_client

# Connect to the server
async with stdio_client("python", ["-m", "backend.mcp.server"]) as (read, write):
    # Use the server
    ...
```

## Resources

The server exposes the following resources:
- `pi://pipeline/stage1` - API Selection stage
- `pi://pipeline/stage2` - Logic Creation stage
- `pi://pipeline/stage3` - Code Creation stage
- `pi://pipeline/stage4` - Test Run stage
- `pi://pipeline/stage5` - File Output stage

## Dependencies

- `mcp>=0.9.0` - MCP protocol library
- `google-generativeai>=0.3.0` - Gemini API for AI operations
- All backend pipeline tools

## Configuration

The server requires the `GEMINI_API_KEY` environment variable to be set for AI operations.

```bash
export GEMINI_API_KEY="your-api-key-here"
```

## Example Usage

```python
import json
from mcp.client.stdio import stdio_client

async def run_pipeline():
    async with stdio_client("python", ["-m", "backend.mcp.server"]) as (read, write):
        # Call api_selection tool
        result = await write.call_tool("api_selection", {
            "user_request": "Read PI tag values for the last 24 hours"
        })
        api_result = json.loads(result[0].text)
        
        # Continue with other pipeline stages...
```

