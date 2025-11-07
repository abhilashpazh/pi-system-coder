"""
Chat interface component for Streamlit UI

Provides chat input and history display functionality.
"""

import streamlit as st
from typing import Optional, Callable
from frontend.utils.session_manager import (
    get_chat_history,
    add_message_to_history
)


def render_chat_interface(
    on_submit: Optional[Callable[[str], None]] = None,
    disabled: bool = False
) -> Optional[str]:
    """
    Render the chat interface with history and input.
    
    Args:
        on_submit: Optional callback function called when user submits a message.
                   Takes the user message as argument.
        disabled: If True, disable the input field and submit button.
    
    Returns:
        User input string if submitted, None otherwise.
    """
    # Chat history is not displayed (removed for cleaner UI)
    # History is still maintained in session state for potential future use
    
    # Chat input
    user_input = None
    
    # Create a form for the input to prevent auto-submit on Enter
    with st.form(key="chat_input_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        
        with col1:
            user_input = st.text_area(
                "Type your message...",
                key="user_input",
                placeholder="e.g., Read PI tag values for the last 24 hours",
                disabled=disabled,
                label_visibility="collapsed",
                height=100
            )
        
        with col2:
            # Disable button if processing is disabled
            # Note: user_input check removed because it's None at render time
            submit_button = st.form_submit_button(
                "Send",
                use_container_width=True,
                disabled=disabled
            )
    
    # Handle submission
    if submit_button:
        # Prevent submission if disabled
        if disabled:
            st.warning("⏳ Please wait for the current request to complete.")
        # Prevent submission if input is empty
        elif not user_input or not user_input.strip():
            st.warning("⚠️ Please enter a message before sending.")
        else:
            # Valid submission - proceed
            # Add user message to history
            add_message_to_history('user', user_input)
            
            # Call callback if provided
            if on_submit:
                on_submit(user_input)
            
            # Rerun to update the UI
            st.rerun()
    
    return user_input if submit_button and user_input else None


def render_chat_message(role: str, content: str) -> None:
    """
    Render a single chat message.
    
    Args:
        role: 'user' or 'assistant'
        content: Message content
    """
    with st.chat_message(role):
        st.write(content)

