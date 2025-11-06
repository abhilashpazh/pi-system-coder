"""
PI System Code Generator - Streamlit UI

Main Streamlit application for the PI System Code Generation Pipeline.
Provides a chat-like interface for interacting with the agentic LLM backend.
"""

import streamlit as st
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from frontend.utils.session_manager import (
    initialize_session_state,
    clear_chat_history,
    set_processing_status,
    add_message_to_history,
    set_final_output
)
from frontend.components.chat import render_chat_interface
from frontend.components.output import render_final_output, render_output_in_chat
from frontend.components.status import (
    render_status_display,
    render_iteration_details,
    get_current_status_from_iterations
)
from frontend.utils.orchestrator_helper import execute_pipeline
from frontend.utils.session_manager import (
    set_current_status,
    set_pipeline_progress
)

# Page configuration
st.set_page_config(
    page_title="PI System Code Generator",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
        .main-header {
            font-size: 1.8rem;
            font-weight: bold;
            color: #1f77b4;
            margin-bottom: 0.5rem;
        }
        .subtitle {
            font-size: 0.95rem;
            color: #666;
            margin-bottom: 1rem;
        }
        .stButton>button {
            width: 100%;
        }
    </style>
""", unsafe_allow_html=True)


def handle_user_submit(user_message: str):
    """
    Handle user message submission and execute the pipeline.
    
    Args:
        user_message: User's input message
    """
    set_processing_status(True)
    
    # Clear previous completion status when starting new execution
    if 'current_status_info' in st.session_state:
        st.session_state.current_status_info['completed'] = False
    
    # Create empty containers for real-time status updates
    status_container = st.empty()
    progress_container = st.empty()
    
    try:
        # Execute the pipeline using orchestrator with status callback
        # Use st.status() for better status display (Streamlit 1.28+)
        with st.status("🔄 Executing pipeline...", expanded=True) as status:
            status.update(label="🔄 Starting pipeline execution...")
            
            # Initial status display
            with status_container.container():
                render_status_display(
                    current_tool=None,
                    current_stage=None,
                    total_stages=5,
                    tool_result=None,
                    iteration_count=0,
                    is_completed=False
                )
            
            # Status callback function to update status during execution
            def status_callback(status_info: dict):
                """Update session state and status display with current status information."""
                # Update session state
                st.session_state.current_status_info = status_info
                current_tool = status_info.get('current_tool')
                current_stage = status_info.get('current_stage')
                latest_iteration = status_info.get('latest_iteration', {})
                iterations = status_info.get('iterations', [])
                iteration_count = status_info.get('iteration_count', 0)
                
                # Get tool result from latest iteration
                tool_result = None
                if latest_iteration:
                    tool_result = latest_iteration.get('tool_result')
                
                # Check if tool has completed (has tool_result)
                tool_has_completed = tool_result is not None and len(tool_result) > 0
                
                # Update status display in real-time
                with status_container.container():
                    render_status_display(
                        current_tool=current_tool,
                        current_stage=current_stage,
                        total_stages=5,
                        tool_result=tool_result,
                        iteration_count=iteration_count,
                        is_completed=False,  # Still executing, not completed yet
                        tool_has_completed=tool_has_completed
                    )
                
                # Update status context label
                if current_tool:
                    tool_display = {
                        "api_selection": "API Selection",
                        "logic_creation": "Logic Creation",
                        "code_creation": "Code Creation",
                        "test_run": "Test Run",
                        "file_output": "File Output"
                    }.get(current_tool, current_tool.title())
                    
                    # Check if tool has completed (has tool_result)
                    tool_has_completed = tool_result is not None and len(tool_result) > 0
                    
                    if current_stage:
                        if tool_has_completed:
                            status.update(label=f"✅ Stage {current_stage}/5: {tool_display} - Completed")
                        else:
                            status.update(label=f"🔄 Stage {current_stage}/5: {tool_display}")
                    else:
                        if tool_has_completed:
                            status.update(label=f"✅ {tool_display} - Completed")
                        else:
                            status.update(label=f"🔄 Executing: {tool_display}")
                elif latest_iteration.get('final_answer'):
                    status.update(label="✅ Pipeline execution completed")
                
                # Update session state helpers
                if current_tool:
                    set_current_status(f"Executing {current_tool}...")
                if current_stage:
                    set_pipeline_progress(current_stage, total_stages=5)
            
            result = execute_pipeline(
                user_prompt=user_message,
                max_iterations=20,
                status_callback=status_callback
            )
            
            # Update status with final information
            if result.get('iterations'):
                status_info = get_current_status_from_iterations(result.get('iterations', []))
                if status_info.get('current_tool'):
                    tool_name = status_info['current_tool']
                    stage = status_info.get('current_stage')
                    tool_display = {
                        "api_selection": "API Selection",
                        "logic_creation": "Logic Creation",
                        "code_creation": "Code Creation",
                        "test_run": "Test Run",
                        "file_output": "File Output"
                    }.get(tool_name, tool_name.title())
                    if stage:
                        status.update(label=f"✅ Completed stage {stage}/5: {tool_display}")
                    else:
                        status.update(label=f"✅ Completed: {tool_display}")
                else:
                    status.update(label="✅ Pipeline execution completed")
            else:
                status.update(label="✅ Pipeline execution completed")
        
        # Store result in session state
        st.session_state.last_result = result
        set_final_output(result)
        
        # Store status info for display
        if result.get('iterations'):
            status_info = get_current_status_from_iterations(result.get('iterations', []))
            # If pipeline completed successfully, set stage to 5 (100% complete)
            if result.get("status") == "success":
                status_info["current_stage"] = 5
                status_info["current_tool"] = "file_output"
                status_info["completed"] = True
            st.session_state.current_status_info = status_info
        
        # Add response to chat history
        if result.get("status") == "success":
            final_answer = result.get("final_answer", "")
            # Format for chat display (truncated version)
            chat_response = render_output_in_chat(final_answer)
            add_message_to_history('assistant', chat_response)
        else:
            error_msg = result.get("error_msg", "Unknown error occurred")
            add_message_to_history('assistant', f"❌ Error: {error_msg}")
        
    except Exception as e:
        error_msg = f"Failed to execute pipeline: {str(e)}"
        add_message_to_history('assistant', f"❌ Error: {error_msg}")
        st.session_state.last_result = {
            "status": "error",
            "error_msg": error_msg,
            "iterations": []
        }
    finally:
        set_processing_status(False)


def main():
    """Main application function."""
    # Initialize session state
    initialize_session_state()
    
    # Simplified header
    st.markdown('<div class="main-header">🔧 PI System Code Generator</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Controls")
        
        if st.button("🔄 Reset All", use_container_width=True):
            clear_chat_history()
            st.rerun()
        
        st.divider()
        
        # Collapsible About section
        with st.expander("ℹ️ About", expanded=False):
            st.markdown("""
            AI-powered code generation assistant for the AVEVA PI System.
            
            Generates production-ready code for interacting with PI System components.
            """)
        
        # Collapsible Instructions section
        with st.expander("📋 How to Use", expanded=False):
            st.markdown("""
            1. Enter your request in the input field
            2. Click **Send** to execute the pipeline
            3. View status and results below
            """)
    
    # Main content area - no "Chat" header needed
    
    # Get processing status
    is_processing = st.session_state.get('is_processing', False)
    
    # Render chat interface
    user_input = render_chat_interface(
        on_submit=handle_user_submit,
        disabled=is_processing
    )
    
    # Display status section if processing or result available
    if is_processing or 'current_status_info' in st.session_state:
        st.divider()
        
        # Get status info (may be None during initial execution)
        status_info = st.session_state.get('current_status_info')
        iterations = st.session_state.get('last_result', {}).get('iterations', [])
        
        # Get tool result from latest iteration
        tool_result = None
        if iterations:
            last_iter = iterations[-1]
            tool_result = last_iter.get('tool_result')
        
        # Determine current tool and stage
        current_tool = None
        current_stage = None
        iteration_count = 0
        is_completed = False
        tool_has_completed = False
        
        if status_info:
            current_tool = status_info.get('current_tool')
            current_stage = status_info.get('current_stage')
            iteration_count = status_info.get('iteration_count', 0)
            is_completed = status_info.get('completed', False)
            
            # Check if tool has completed (has tool_result)
            tool_has_completed = tool_result is not None and len(tool_result) > 0
            
            # If completed, ensure stage is 5
            if is_completed and current_stage != 5:
                current_stage = 5
                current_tool = "file_output"
        elif is_processing:
            # During execution but before first callback, show initial state
            current_tool = None
            current_stage = None
        
        # Always render status display during execution or after completion
        render_status_display(
            current_tool=current_tool,
            current_stage=current_stage,
            total_stages=5,
            tool_result=tool_result,
            iteration_count=iteration_count,
            is_completed=is_completed,
            tool_has_completed=tool_has_completed
        )
        
        # Show detailed iteration log if available
        if iterations:
            render_iteration_details(iterations)
    
    # Display final output section if result is available
    if 'last_result' in st.session_state:
        st.divider()
        st.header("📤 Output")
        render_final_output(st.session_state.last_result)


if __name__ == "__main__":
    main()

