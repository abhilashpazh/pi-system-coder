"""
File Output Tool for PI System Code Generation Pipeline

This tool packages and delivers the final code with metadata and documentation.
Uses Google Gemini 2.0 Flash API for generating comprehensive documentation.

Requirements: FR-005, FR-010, FR-050, DR-002
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
import hashlib

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

# File output prompt template
FILE_OUTPUT_PROMPT = """You are an expert technical writer specializing in PI System documentation.

Generated Code:
```{target_language}
{code}
```

Language: {target_language}
API: {selected_api}
Dependencies: {dependencies}

Generate comprehensive documentation in JSON format:

{{
    "readme_content": "Complete README.md content with installation, usage, examples",
    "manifest_content": {{
        "author": "PI System Code Generator",
        "version": "1.0.0",
        "description": "Brief description",
        "language": "{target_language}",
        "api": "{selected_api}",
        "dependencies": {dependencies},
        "requirements": "System requirements and prerequisites",
        "usage": "Basic usage instructions"
    }}
}}

Include in README:
1. Project title and description
2. Features
3. Installation/setup instructions
4. API reference (if applicable)
5. Usage examples
6. Configuration instructions
7. Error handling
8. Dependencies and requirements
9. Security considerations
10. Examples and screenshots (if applicable)

Return ONLY the JSON response, no additional text."""


def file_output(
    code: str,
    target_language: str,
    selected_api: str,
    dependencies: List[str],
    test_results: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate final file package with code, metadata, and documentation.
    
    Args:
        code: Generated implementation code
        target_language: Programming language
        selected_api: The PI API used
        dependencies: List of required dependencies
        test_results: Results from test_run tool
        context: Optional context from previous interactions
        
    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - files: Dictionary with file contents
            - main_code: Main code file content
            - readme: README.md content
            - manifest: Manifest/metadata file content
        - file_hashes: Dictionary with file hashes
        - reasoning: Explanation
        - reasoning_type: "finalization"
        - error_msg: Error message if status is error
    """
    try:
        # Get file extension for target language
        file_extensions = {
            "C#": ".cs",
            "Python": ".py",
            "VB.NET": ".vb",
            "JavaScript": ".js",
            "TypeScript": ".ts",
            "Java": ".java",
            "PowerShell": ".ps1",
            "C++": ".cpp"
        }
        ext = file_extensions.get(target_language, ".txt")
        
        # Get timestamp
        timestamp = datetime.now().isoformat()
        
        # Build complete prompt for documentation generation
        full_prompt = FILE_OUTPUT_PROMPT.format(
            target_language=target_language,
            code=code,
            selected_api=selected_api,
            dependencies=json.dumps(dependencies, indent=2)
        )
        
        # Add context if available
        if context:
            context_str = json.dumps(context, indent=2)
            full_prompt += f"\n\nAdditional Context:\n{context_str}"
        
        # Call LLM API for documentation
        response_text = llm_config.generate_content(
            full_prompt,
            temperature=0.5,
            max_tokens=2000
        )
        
        # Extract JSON from response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start == -1 or json_end == 0:
            raise ValueError("No JSON found in response")
        
        doc_result = json.loads(response_text[json_start:json_end])
        
        # Validate documentation structure
        if "readme_content" not in doc_result:
            raise ValueError("Missing readme_content in documentation")
        if "manifest_content" not in doc_result:
            raise ValueError("Missing manifest_content in documentation")
        
        # Enhance manifest with additional metadata
        manifest = doc_result["manifest_content"]
        manifest["timestamp"] = timestamp
        manifest["code_size_bytes"] = len(code.encode('utf-8'))
        manifest["code_lines"] = len(code.split('\n'))
        
        # Add test results to manifest if available
        if test_results and test_results.get("overall_result"):
            manifest["test_status"] = test_results["overall_result"]
            manifest["quality_metrics"] = {
                "syntax_check_passed": test_results["syntax_check"]["passed"],
                "logic_check_passed": test_results["logic_consistency"]["passed"],
                "best_practices_passed": test_results["best_practices"]["passed"],
                "error_handling_passed": test_results["error_handling"]["passed"],
                "security_passed": test_results["security"]["passed"]
            }
        
        # Generate file hashes
        code_hash = hashlib.sha256(code.encode('utf-8')).hexdigest()
        readme_hash = hashlib.sha256(doc_result["readme_content"].encode('utf-8')).hexdigest()
        manifest_hash = hashlib.sha256(json.dumps(manifest, indent=2).encode('utf-8')).hexdigest()
        
        # Build files dictionary
        files = {
            "main_code": {
                "filename": f"pi_code{ext}",
                "content": code
            },
            "readme": {
                "filename": "README.md",
                "content": doc_result["readme_content"]
            },
            "manifest": {
                "filename": "manifest.json",
                "content": json.dumps(manifest, indent=2)
            }
        }
        
        # Return success result
        return {
            "status": "success",
            "files": files,
            "file_hashes": {
                "main_code": code_hash,
                "readme": readme_hash,
                "manifest": manifest_hash
            },
            "reasoning": "Files successfully generated with complete documentation and metadata",
            "reasoning_type": "finalization",
            "error_msg": None
        }
        
    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "files": None,
            "file_hashes": None,
            "reasoning": None,
            "reasoning_type": "error_recovery",
            "error_msg": f"Failed to parse JSON response: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "files": None,
            "file_hashes": None,
            "reasoning": None,
            "reasoning_type": "error_recovery",
            "error_msg": f"File output failed: {str(e)}"
        }


def write_files_to_disk(output_result: Dict[str, Any], output_dir: str = "output") -> List[str]:
    """
    Write the generated files to disk.
    
    Args:
        output_result: Result from file_output function
        output_dir: Directory to write files to
        
    Returns:
        List of file paths written
    """
    if output_result["status"] != "success":
        raise ValueError("Cannot write files from failed file_output result")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    written_files = []
    
    # Write each file
    for file_key, file_data in output_result["files"].items():
        file_path = os.path.join(output_dir, file_data["filename"])
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(file_data["content"])
        written_files.append(file_path)
    
    return written_files


def format_tool_output(file_result: Dict[str, Any]) -> str:
    """
    Format the file output result according to TOOL_RESULT or FINAL_ANSWER specification.
    
    Args:
        file_result: Result from file_output function
        
    Returns:
        Formatted string in FINAL_ANSWER format
    """
    if file_result["status"] == "success":
        # Build final answer with code and documentation
        output_lines = []
        output_lines.append("# Generated PI System Code Package\n")
        
        # Add manifest info
        manifest = json.loads(file_result["files"]["manifest"]["content"])
        output_lines.append(f"## Metadata\n")
        output_lines.append(f"- Language: {manifest['language']}")
        output_lines.append(f"- API: {manifest['api']}")
        output_lines.append(f"- Version: {manifest['version']}")
        output_lines.append(f"- Generated: {manifest['timestamp']}\n")
        
        # Add main code
        output_lines.append(f"## Main Code ({file_result['files']['main_code']['filename']})\n")
        output_lines.append(f"```{manifest['language'].lower()}")
        output_lines.append(file_result["files"]["main_code"]["content"])
        output_lines.append("```\n")
        
        # Add dependencies
        if manifest.get("dependencies"):
            output_lines.append("## Dependencies\n")
            for dep in manifest["dependencies"]:
                output_lines.append(f"- {dep}")
            output_lines.append("")
        
        # Add test results if available
        if manifest.get("test_status"):
            output_lines.append(f"## Quality Checks\n")
            output_lines.append(f"- Overall Status: {manifest['test_status'].upper()}")
            output_lines.append("")
        
        # Add README content
        output_lines.append("## Documentation\n")
        output_lines.append(file_result["files"]["readme"]["content"])
        
        # Add file hashes
        output_lines.append("\n## File Integrity\n")
        for file_name, file_hash in file_result["file_hashes"].items():
            output_lines.append(f"- {file_name}: {file_hash[:16]}...")
        
        # Return as FINAL_ANSWER
        final_output = "\n".join(output_lines)
        return f"FINAL_ANSWER: {final_output}"
    else:
        return f"TOOL_RESULT: file_output|status=error|data=|error_msg={file_result['error_msg']}"


if __name__ == "__main__":
    # Example usage
    test_code = """import requests
from requests.auth import HTTPBasicAuth

def read_pi_tag_value(base_url, username, password, tag_name):
    try:
        auth = HTTPBasicAuth(username, password)
        url = f"{base_url}/streams/{tag_name}/value"
        response = requests.get(url, auth=auth, timeout=30)
        response.raise_for_status()
        return response.json()['Value']['Value']
    except Exception as e:
        print(f"Error: {e}")
        return None"""
    
    test_dependencies = ["requests"]
    
    print("File Output Tool - Example")
    print("=" * 60)
    
    result = file_output(
        code=test_code,
        target_language="Python",
        selected_api="PI Web API",
        dependencies=test_dependencies
    )
    
    if result["status"] == "success":
        print("\nFiles Generated:")
        for file_key, file_data in result["files"].items():
            print(f"  - {file_data['filename']}: {len(file_data['content'])} chars")
        
        print("\nFile Hashes:")
        for file_name, file_hash in result["file_hashes"].items():
            print(f"  - {file_name}: {file_hash[:32]}...")
        
        print("\nSummary:")
        print(f"  Status: {result['status']}")
        print(f"  Reasoning: {result['reasoning']}")
        print(f"  Type: {result['reasoning_type']}")
        
        # Demonstrate writing files to disk
        try:
            written = write_files_to_disk(result, "test_output")
            print(f"\nFiles written to disk: {len(written)}")
        except Exception as e:
            print(f"\nCould not write files: {e}")
    else:
        print(f"\nError: {result['error_msg']}")
    
    print("-" * 60)

