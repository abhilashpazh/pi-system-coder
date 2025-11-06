"""
Output display component for Streamlit UI

Displays final code output and results from the pipeline.
"""

import streamlit as st
import re
from typing import Dict, Any, Optional, Tuple


def render_final_output(result: Dict[str, Any]) -> None:
    """
    Render the final output from the pipeline execution.
    
    Args:
        result: Dictionary from orchestrator containing:
                - status: "success" or "error"
                - final_answer: Final code output (if successful)
                - error_msg: Error message (if failed)
                - iterations: List of iteration details
    """
    if result.get("status") == "error":
        render_error_output(result)
    else:
        render_success_output(result)


def render_success_output(result: Dict[str, Any]) -> None:
    """
    Render successful pipeline output.
    
    Args:
        result: Successful result dictionary
    """
    final_answer = result.get("final_answer", "")
    
    if not final_answer:
        st.warning("Pipeline completed but no output was generated.")
        return
    
    st.success("✅ Pipeline completed successfully!")
    
    # Extract code, metadata, and files from final_answer
    extracted_code, metadata, files = extract_code_from_final_answer(final_answer)
    
    # Display metadata section
    if metadata:
        with st.expander("📋 Metadata & Information", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                if 'Language' in metadata:
                    st.metric("Language", metadata['Language'])
                if 'API' in metadata:
                    st.metric("PI API", metadata['API'])
            
            with col2:
                if 'Version' in metadata:
                    st.metric("Version", metadata['Version'])
                if 'Generated' in metadata:
                    st.metric("Generated", metadata['Generated'])
            
            # Dependencies
            if 'dependencies' in metadata:
                st.write("**Dependencies:**")
                if isinstance(metadata['dependencies'], list):
                    for dep in metadata['dependencies']:
                        st.write(f"- `{dep}`")
                else:
                    st.write(f"- {metadata['dependencies']}")
            
            # Test status
            if 'test_status' in metadata:
                status = metadata['test_status'].upper()
                if status == 'PASS':
                    st.success(f"✅ Quality Checks: {status}")
                else:
                    st.warning(f"⚠️ Quality Checks: {status}")
            
            # File hashes
            if 'file_hashes' in metadata and isinstance(metadata['file_hashes'], dict):
                st.write("**File Integrity:**")
                for file_name, file_hash in metadata['file_hashes'].items():
                    st.caption(f"{file_name}: `{file_hash}`")
    
    # File structure and downloads
    if files:
        st.subheader("📁 Generated Files")
        
        # Show file list
        for file_key, file_info in files.items():
            filename = file_info.get('filename', file_key)
            content = file_info.get('content', '')
            
            # Create download button for each file
            st.download_button(
                label=f"📥 Download {filename}",
                data=content,
                file_name=filename,
                mime=_get_mime_type(filename),
                key=f"download_{file_key}"
            )
    
    # Display the main code
    st.subheader("📄 Generated Code")
    
    # Get filename for code display
    code_filename = files.get('main_code', {}).get('filename', 'code') if files else 'code'
    if code_filename != 'code':
        st.caption(f"File: {code_filename}")
    
    # Try to detect code language for syntax highlighting
    code_language = detect_code_language(extracted_code)
    
    # Display code with syntax highlighting and proper formatting
    st.code(extracted_code, language=code_language)
    
    # Show iteration summary
    iterations = result.get("iterations", [])
    if iterations:
        with st.expander("📊 Execution Summary"):
            st.write(f"**Total Iterations:** {len(iterations)}")
            
            # List tools used
            tools_used = []
            for iteration in iterations:
                if iteration.get('tool_call'):
                    tool_name = iteration['tool_call'].get('function')
                    if tool_name and tool_name not in tools_used:
                        tools_used.append(tool_name)
            
            if tools_used:
                st.write(f"**Tools Used:** {', '.join(tools_used)}")


def render_error_output(result: Dict[str, Any]) -> None:
    """
    Render error output from failed pipeline execution.
    
    Args:
        result: Error result dictionary
    """
    error_msg = result.get("error_msg", "Unknown error occurred")
    
    st.error("❌ Pipeline execution failed")
    
    # Display error message
    st.error(f"**Error:** {error_msg}")
    
    # Show iteration details if available (for debugging)
    iterations = result.get("iterations", [])
    if iterations:
        with st.expander("🔍 Debug Information"):
            st.write(f"**Iterations completed:** {len(iterations)}")
            
            # Show last few iterations
            if len(iterations) > 0:
                st.write("**Last Iteration:**")
                last_iteration = iterations[-1]
                
                if last_iteration.get('tool_call'):
                    st.json(last_iteration['tool_call'])
                
                if last_iteration.get('tool_result'):
                    tool_result = last_iteration['tool_result']
                    # Truncate if too long
                    if len(tool_result) > 500:
                        st.text(tool_result[:500] + "...")
                    else:
                        st.text(tool_result)


def extract_code_from_final_answer(final_answer: str) -> Tuple[str, Dict[str, Any], Dict[str, str]]:
    """
    Extract code, metadata, and file information from final_answer string.
    The final_answer may contain markdown formatting with code blocks.
    
    Args:
        final_answer: Raw final answer string from orchestrator
    
    Returns:
        Tuple of (extracted_code, metadata_dict, files_dict)
        files_dict contains: {'main_code': content, 'readme': content, etc.}
    """
    if not final_answer:
        return "", {}, {}
    
    metadata = {}
    files = {}
    extracted_code = final_answer
    
    # Extract metadata from markdown headers if present
    metadata_pattern = r'## Metadata\s*\n(.*?)(?=\n##|\n```|$)'
    metadata_match = re.search(metadata_pattern, final_answer, re.DOTALL)
    if metadata_match:
        metadata_text = metadata_match.group(1)
        # Extract key-value pairs
        for line in metadata_text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lstrip('-').strip()
                value = value.strip()
                if key and value:
                    metadata[key] = value
    
    # Extract main code from code blocks
    # Pattern: ## Main Code (filename)\n```language\ncode\n```
    main_code_pattern = r'## Main Code\s*\(([^)]+)\)\s*\n```(?:python|javascript|typescript|csharp|java|powershell|cpp|ps1|cs|js|ts)?\n?(.*?)```'
    main_code_match = re.search(main_code_pattern, final_answer, re.DOTALL)
    if main_code_match:
        filename = main_code_match.group(1).strip()
        code_content = main_code_match.group(2).strip()
        extracted_code = code_content
        files['main_code'] = {
            'filename': filename,
            'content': code_content
        }
    else:
        # Fallback: try to extract any code block
        code_block_pattern = r'```(?:python|javascript|typescript|csharp|java|powershell|cpp|ps1|cs|js|ts)?\n?(.*?)```'
        code_blocks = re.findall(code_block_pattern, final_answer, re.DOTALL)
        if code_blocks:
            extracted_code = code_blocks[0].strip()
            files['main_code'] = {
                'filename': 'code',
                'content': extracted_code
            }
    
    # Extract dependencies
    deps_pattern = r'## Dependencies\s*\n(.*?)(?=\n##|$)'
    deps_match = re.search(deps_pattern, final_answer, re.DOTALL)
    if deps_match:
        deps_text = deps_match.group(1)
        dependencies = [line.strip().lstrip('-').strip() for line in deps_text.split('\n') if line.strip()]
        if dependencies:
            metadata['dependencies'] = dependencies
    
    # Extract documentation/README
    doc_pattern = r'## Documentation\s*\n(.*?)(?=\n## File Integrity|$)'
    doc_match = re.search(doc_pattern, final_answer, re.DOTALL)
    if doc_match:
        readme_content = doc_match.group(1).strip()
        files['readme'] = {
            'filename': 'README.md',
            'content': readme_content
        }
    
    # Extract file integrity hashes
    integrity_pattern = r'## File Integrity\s*\n(.*?)(?=\n##|$)'
    integrity_match = re.search(integrity_pattern, final_answer, re.DOTALL)
    if integrity_match:
        integrity_text = integrity_match.group(1)
        hashes = {}
        for line in integrity_text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lstrip('-').strip()
                value = value.strip()
                if key and value:
                    hashes[key] = value
        metadata['file_hashes'] = hashes
    
    # Extract quality checks/test status
    quality_pattern = r'## Quality Checks\s*\n(.*?)(?=\n##|$)'
    quality_match = re.search(quality_pattern, final_answer, re.DOTALL)
    if quality_match:
        quality_text = quality_match.group(1)
        for line in quality_text.split('\n'):
            if ':' in line or 'Status' in line:
                if 'Status' in line:
                    status_match = re.search(r'Status:\s*(\w+)', line, re.IGNORECASE)
                    if status_match:
                        metadata['test_status'] = status_match.group(1)
    
    # Ensure proper line breaks are preserved
    extracted_code = extracted_code.replace('\\n', '\n')
    for file_key in files:
        if 'content' in files[file_key]:
            files[file_key]['content'] = files[file_key]['content'].replace('\\n', '\n')
    
    return extracted_code, metadata, files


def _get_mime_type(filename: str) -> str:
    """
    Get MIME type based on file extension.
    
    Args:
        filename: Name of the file
    
    Returns:
        MIME type string
    """
    ext = filename.split('.')[-1].lower() if '.' in filename else ''
    
    mime_types = {
        'py': 'text/x-python',
        'js': 'text/javascript',
        'ts': 'text/typescript',
        'cs': 'text/x-csharp',
        'java': 'text/x-java',
        'ps1': 'text/x-powershell',
        'cpp': 'text/x-c++',
        'c': 'text/x-c',
        'md': 'text/markdown',
        'json': 'application/json',
        'xml': 'application/xml',
        'txt': 'text/plain',
        'html': 'text/html',
        'css': 'text/css'
    }
    
    return mime_types.get(ext, 'text/plain')


def _get_file_extension(language: str) -> str:
    """
    Get file extension based on programming language.
    
    Args:
        language: Programming language name
    
    Returns:
        File extension (e.g., '.py', '.js')
    """
    language_lower = language.lower()
    
    extensions = {
        'python': '.py',
        'javascript': '.js',
        'typescript': '.ts',
        'csharp': '.cs',
        'c#': '.cs',
        'java': '.java',
        'powershell': '.ps1',
        'cpp': '.cpp',
        'c++': '.cpp',
        'c': '.c'
    }
    
    return extensions.get(language_lower, '.txt')


def detect_code_language(code: str) -> str:
    """
    Detect the programming language from code content.
    
    Args:
        code: Code string
    
    Returns:
        Language identifier for syntax highlighting
    """
    code_lower = code.lower()
    
    # Python indicators
    if any(keyword in code_lower for keyword in ['import ', 'def ', 'class ', 'print(', 'pip install']):
        return "python"
    
    # JavaScript/TypeScript indicators
    if any(keyword in code_lower for keyword in ['function ', 'const ', 'let ', 'var ', 'require(', 'export ']):
        if 'typescript' in code_lower or 'interface ' in code_lower or ': string' in code_lower:
            return "typescript"
        return "javascript"
    
    # C# indicators
    if any(keyword in code_lower for keyword in ['using ', 'namespace ', 'public class', 'static void']):
        return "csharp"
    
    # Java indicators
    if any(keyword in code_lower for keyword in ['package ', 'public class', 'public static void main']):
        return "java"
    
    # PowerShell indicators
    if any(keyword in code_lower for keyword in ['$', 'get-pidata', 'write-host', 'function ']):
        return "powershell"
    
    # C++ indicators
    if any(keyword in code_lower for keyword in ['#include', 'int main()', 'std::', 'using namespace']):
        return "cpp"
    
    # Default to text
    return "text"


def render_output_in_chat(final_answer: str) -> str:
    """
    Format final answer for display in chat interface.
    Returns a formatted string suitable for chat display.
    
    Args:
        final_answer: Raw final answer from orchestrator
    
    Returns:
        Formatted string for chat display
    """
    if not final_answer:
        return "No output generated."
    
    # For Phase 2, return a simplified version
    # Phase 4 will enhance this with better formatting
    
    # Truncate if too long for chat
    max_chat_length = 1000
    if len(final_answer) > max_chat_length:
        return final_answer[:max_chat_length] + f"\n\n... (truncated, see output section for full code)"
    
    return final_answer

