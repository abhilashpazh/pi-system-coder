# PI System Code Generation Pipeline

AI-powered code generation assistant for the AVEVA PI System, built with Google Gemini 2.0 Flash API.

## Overview

This project implements a five-stage sequential pipeline for automatically generating production-ready code to interact with PI System components. The pipeline follows the specifications outlined in the User Requirements Document (URD).

## Pipeline Architecture

```
User Request → API Selection → Logic Creation → Code Creation → Test Run → File Output
```

### Stage 1: API Selection (`backend/src/tools/api_selection.py`)
- Automatically identifies the most appropriate PI System API
- Available APIs: PI SDK, PI AF SDK, PI Web API, PI SQL Client
- Uses Gemini 2.0 Flash for intelligent selection

### Stage 2: Logic Creation (`backend/src/tools/logic_creation.py`)
- Converts user requests into explicit pseudo-code
- Defines data structures and error handling strategies
- Creates step-by-step logical flow

### Stage 3: Code Creation (`backend/src/tools/code_creation.py`)
- Generates implementation code in target language
- Supports: Python, C#, JavaScript, TypeScript, Java, PowerShell, C++
- Follows PI API best practices

### Stage 4: Test Run (`backend/src/tools/test_run.py`)
- Performs static analysis and quality checks
- Validates syntax, logic, best practices, error handling, and security
- Provides recommendations for improvement

### Stage 5: File Output (`backend/src/tools/file_output.py`)
- Packages code with documentation and metadata
- Generates README, manifest, and code files
- Creates file integrity hashes

## Installation

### Prerequisites
- Python 3.7 or higher
- Google Gemini API key (set as environment variable)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd pi-system-coder
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:

**Option A: Using .env file (recommended)**
```bash
# Copy the example file
cp env.example .env

# Edit .env file with your API key
# GEMINI_API_KEY=your-api-key-here
# GEMINI_MODEL=gemini-2.0-flash-exp
# LOG_LEVEL=INFO
```

**Option B: Using environment variables directly**
```bash
# Linux/Mac
export GEMINI_API_KEY="your-api-key-here"

# Windows Command Prompt
set GEMINI_API_KEY=your-api-key-here

# Windows PowerShell
$env:GEMINI_API_KEY="your-api-key-here"
```

## Usage

### Running Individual Tools

Each tool can be run independently for testing:

```bash
# API Selection
python backend/src/tools/api_selection.py

# Logic Creation
python backend/src/tools/logic_creation.py

# Code Creation
python backend/src/tools/code_creation.py

# Test Run
python backend/src/tools/test_run.py

# File Output
python backend/src/tools/file_output.py
```

### Running Unit Tests

Run all tests:
```bash
python -m unittest discover -s backend/tests -p "test_*.py" -v
```

Run specific test file:
```bash
python backend/tests/test_api_selection.py
python backend/tests/test_logic_creation.py
python backend/tests/test_code_creation.py
python backend/tests/test_test_run.py
python backend/tests/test_file_output.py
```

### Running MCP Server

Run the MCP server to expose tools via Model Context Protocol:

```bash
python -m backend.mcp.server
```

### Integration Example

Complete pipeline workflow example:

```python
from backend.src.tools.api_selection import api_selection
from backend.src.tools.logic_creation import logic_creation
from backend.src.tools.code_creation import code_creation
from backend.src.tools.test_run import test_run
from backend.src.tools.file_output import file_output, write_files_to_disk

# Stage 1: API Selection
user_request = "Read PI tag values for the last 24 hours"
api_result = api_selection(user_request)

# Stage 2: Logic Creation
if api_result["status"] == "success":
    logic_result = logic_creation(
        user_request=user_request,
        selected_api=api_result["selected_api"]
    )
    
    # Stage 3: Code Creation
    if logic_result["status"] == "success":
        code_result = code_creation(
            pseudo_code=logic_result["pseudo_code"],
            data_structures=logic_result["data_structures"],
            error_handling_strategy=logic_result["error_handling_strategy"],
            selected_api=api_result["selected_api"],
            target_language="Python"
        )
        
        # Stage 4: Test Run
        if code_result["status"] == "success":
            test_result = test_run(
                code=code_result["code"],
                target_language="Python",
                selected_api=api_result["selected_api"]
            )
            
            # Stage 5: File Output
            if test_result["status"] == "success":
                output_result = file_output(
                    code=code_result["code"],
                    target_language="Python",
                    selected_api=api_result["selected_api"],
                    dependencies=code_result["dependencies"],
                    test_results=test_result
                )
                
                # Write files to disk
                if output_result["status"] == "success":
                    files = write_files_to_disk(output_result, "output")
                    print(f"Generated files: {files}")
```

## Project Structure

```
pi-system-coder/
├── backend/                           # Backend source code
│   ├── mcp/                           # MCP Server
│   │   ├── server.py                  # MCP server implementation
│   │   └── README.md                  # MCP server documentation
│   ├── src/
│   │   ├── tools/                     # Five-stage pipeline tools
│   │   │   ├── api_selection.py      # Stage 1: API selection
│   │   │   ├── logic_creation.py     # Stage 2: Logic creation
│   │   │   ├── code_creation.py      # Stage 3: Code creation
│   │   │   ├── test_run.py           # Stage 4: Test run
│   │   │   └── file_output.py        # Stage 5: File output
│   │   └── config/                    # Configuration management
│   └── tests/                         # Backend unit tests
│       ├── test_api_selection.py
│       ├── test_logic_creation.py
│       ├── test_code_creation.py
│       ├── test_test_run.py
│       └── test_file_output.py
│
├── frontend/                          # Frontend application (future)
│
├── config/                            # Shared configuration files
│
├── docs/                              # Additional documentation
│
├── scripts/                           # Utility scripts
│
├── requirements.txt                   # Python dependencies
├── pyproject.toml                     # Modern Python project config
├── README.md                          # This file
├── USER_REQUIREMENTS_DOCUMENT.md      # Full requirements specification
└── system_prompt.md                   # System prompt for AI assistant
```

## Features

### Supported PI System APIs
- **PI SDK**: High-performance server-side data access
- **PI AF SDK**: Asset Framework operations
- **PI Web API**: RESTful cross-platform access
- **PI SQL Client**: Direct database queries

### Supported Languages
- Primary: Python, C#, VB.NET, JavaScript/TypeScript
- Secondary: Java, PowerShell, C++

### Code Quality Features
- Syntax validation
- Logic consistency checks
- PI API best practices enforcement
- Security scanning (hardcoded credentials, SQL injection, etc.)
- Error handling verification
- Comprehensive documentation generation

## Security

- **No Hardcoded Credentials**: Generated code uses environment variables or configuration files
- **Security Scanning**: Automatic detection of security vulnerabilities
- **Safe Patterns**: Follows PI System security best practices
- **Secure API Usage**: Uses only public, documented SDK methods

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add/update tests
5. Ensure all tests pass
6. Submit a pull request

## Testing

The project includes comprehensive unit tests with mocking for Gemini API calls:

- **Unit Tests**: Each tool has dedicated test file
- **Coverage**: Tests cover success paths, error handling, and edge cases
- **Integration Tests**: Can be added for full pipeline testing (requires API key)
- **Mocking**: Uses `unittest.mock` to avoid API costs during development

Run tests:
```bash
python -m unittest discover -v
```

## Documentation

- **User Requirements Document**: See `USER_REQUIREMENTS_DOCUMENT.md` for complete specifications
- **System Prompt**: See `system_prompt.md` for AI assistant behavior
- **Code Comments**: Each module includes detailed docstrings
- **Examples**: Main block in each tool provides usage examples

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Acknowledgments

- AVEVA for PI System APIs
- Google for Gemini AI capabilities
- Built following the User Requirements Document specifications

## Support

For issues, questions, or contributions, please open an issue on the repository.

## Version History

- **v1.0.0** - Initial release with five-stage pipeline
  - API selection tool
  - Logic creation tool
  - Code creation tool
  - Test run tool
  - File output tool
  - Comprehensive unit tests

## Future Enhancements

- Web-based UI for pipeline execution
- CLI for command-line usage
- Additional language support
- More PI System API integrations
- Batch processing capabilities
- Code templates and snippets library

