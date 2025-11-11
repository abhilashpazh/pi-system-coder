# Gemini CLI

   ## General Recommendations

        1. Refactor Tool Dispatch: Implement a dictionary-based dispatch for call_tool in both orchestrator.py and mcp/server.py to improve extensibility and maintainability. -- Done
        2. Standardize Path Management: Consider using a more standard Python package structure or PYTHONPATH configuration instead of multiple sys.path.insert calls.
        3. Enhance Context Object: Develop a more structured context object or class to pass state and information between pipeline stages, rather than relying on implicit tracking or simple JSON dumps.

   ## backend/agent/orchestrator.py
        * Areas for Improvement:
            * Tool Dispatch: The call_tool function uses a long if/elif chain. Consider refactoring this into a dictionary mapping function names to tool functions for better scalability and readability (e.g., tool_map = {"api_selection": api_selection, ...}).
            * State Management: tracked_language and tracked_api are managed somewhat ad-hoc. A more explicit pipeline_state object or a structured context argument passed between tools could improve clarity and prevent potential issues.
            * Redundant Import: import json inside a try-except block within orchestrator is redundant as json is already imported at the top level.

   ## backend/mcp/server.py
        * Areas for Improvement:
            * Tool Dispatch: Similar to the orchestrator, the call_tool function could benefit from a dictionary-based dispatch mechanism instead of an if/elif chain.
            * Path Management: Multiple sys.path.insert calls are used. While functional, it's generally better to configure Python's package system (e.g., PYTHONPATH or editable installs) to manage module imports more robustly.

   ## backend/src/tools/api_selection.py & backend/src/tools/code_creation.py
        * Areas for Improvement:
            * Context Handling: The context_str concatenation (user_request + context_str) could be more sophisticated. If context contains complex or sensitive data, a more structured approach to integrate it into the prompt might be beneficial.
            * LLM Output Parsing: The json_start/json_end logic for extracting JSON from LLM responses is a common workaround but can be brittle if the LLM's output format varies unexpectedly

   ## frontend/streamlit_app.py
        * Areas for Improvement:
            * Path Management: Similar to backend files, sys.path.insert is used.
            * Unused Variable: The progress_container is created but not utilized.
            * Code Duplication: The logic for determining tool_has_completed is duplicated. This could be extracted into a helper function.
            * `st.rerun()` Usage: While often necessary in Streamlit, frequent st.rerun() calls can sometimes impact performance. Ensure it's only triggered when essential for UI updates.

   ## frontend/components/chat.py
        * Areas for Improvement:
            * Chat History Display: The comment indicates chat history is maintained but not displayed. Providing an optional way to view it (e.g., in an st.expander) could enhance user experience for debugging or reference.
            * Comment Clarity: The comment Note: user_input check removed because it's None at render time is slightly confusing as the user_input check is present. Clarifying its intent or removing it if no longer relevant would be beneficial.