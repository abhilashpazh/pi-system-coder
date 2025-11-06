"""
Session state management for Streamlit UI

Manages chat history, user input, and application state.
"""

import streamlit as st
from typing import List, Dict, Any, Optional


def initialize_session_state():
    """
    Initialize all session state variables if they don't exist.
    This should be called at the start of the Streamlit app.
    """
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'is_processing' not in st.session_state:
        st.session_state.is_processing = False
    
    if 'current_status' not in st.session_state:
        st.session_state.current_status = None
    
    if 'pipeline_progress' not in st.session_state:
        st.session_state.pipeline_progress = None
    
    if 'final_output' not in st.session_state:
        st.session_state.final_output = None
    
    if 'iteration_details' not in st.session_state:
        st.session_state.iteration_details = []


def add_message_to_history(role: str, content: str) -> None:
    """
    Add a message to the chat history.
    
    Args:
        role: 'user' or 'assistant'
        content: Message content
    """
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    st.session_state.chat_history.append({
        'role': role,
        'content': content,
        'timestamp': None  # Can be enhanced with datetime if needed
    })


def clear_chat_history() -> None:
    """Clear all chat history and reset related state."""
    st.session_state.chat_history = []
    st.session_state.final_output = None
    st.session_state.current_status = None
    st.session_state.pipeline_progress = None
    st.session_state.iteration_details = []
    if 'last_result' in st.session_state:
        del st.session_state.last_result
    if 'current_status_info' in st.session_state:
        del st.session_state.current_status_info


def get_chat_history() -> List[Dict[str, Any]]:
    """
    Get the current chat history.
    
    Returns:
        List of message dictionaries with 'role' and 'content' keys
    """
    if 'chat_history' not in st.session_state:
        return []
    return st.session_state.chat_history.copy()


def set_processing_status(is_processing: bool) -> None:
    """Set the processing status flag."""
    st.session_state.is_processing = is_processing


def get_processing_status() -> bool:
    """Get the current processing status."""
    return st.session_state.get('is_processing', False)


def set_current_status(status: Optional[str]) -> None:
    """Set the current status message."""
    st.session_state.current_status = status


def get_current_status() -> Optional[str]:
    """Get the current status message."""
    return st.session_state.get('current_status')


def set_pipeline_progress(stage: Optional[int], total_stages: int = 5) -> None:
    """
    Set the pipeline progress.
    
    Args:
        stage: Current stage (1-5) or None
        total_stages: Total number of stages (default: 5)
    """
    if stage is None:
        st.session_state.pipeline_progress = None
    else:
        st.session_state.pipeline_progress = {
            'current': stage,
            'total': total_stages,
            'percentage': (stage / total_stages) * 100
        }


def get_pipeline_progress() -> Optional[Dict[str, Any]]:
    """Get the current pipeline progress."""
    return st.session_state.get('pipeline_progress')


def set_final_output(result: Dict[str, Any]) -> None:
    """Set the final output result from pipeline execution."""
    st.session_state.final_output = result


def get_final_output() -> Optional[Dict[str, Any]]:
    """Get the final output result."""
    return st.session_state.get('final_output')

