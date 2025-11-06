# PI System Code Generator - Streamlit UI

Frontend interface for the PI System Code Generation Pipeline.

## Phase 1: Basic Chat Interface

This phase implements:
- ✅ Streamlit app structure
- ✅ Chat interface with input and history
- ✅ Session state management
- ✅ Basic UI layout

## Running the Application

### Prerequisites

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure you have a `.env` file with your LLM API keys (for Phase 2)

### Start the Streamlit App

From the project root directory:

```bash
streamlit run frontend/streamlit_app.py
```

Or from the frontend directory:

```bash
cd frontend
streamlit run streamlit_app.py
```

The app will open in your default web browser at `http://localhost:8501`

## Testing Phase 1

### Functional Tests

1. **App Launch**
   - [ ] App launches without errors
   - [ ] Header and sidebar display correctly
   - [ ] No console errors

2. **Chat Input**
   - [ ] Text input field is visible
   - [ ] Placeholder text displays correctly
   - [ ] Can type in the input field
   - [ ] Send button is visible

3. **Message Display**
   - [ ] Type a message and click Send
   - [ ] User message appears in chat history
   - [ ] Assistant response appears (placeholder for Phase 1)
   - [ ] Messages display in correct order

4. **Session State**
   - [ ] Chat history persists when typing new messages
   - [ ] Messages remain after page interactions
   - [ ] Clear Chat button works and removes all messages

5. **UI Responsiveness**
   - [ ] Interface is responsive
   - [ ] No layout issues
   - [ ] Sidebar functions correctly

## Project Structure

```
frontend/
├── streamlit_app.py          # Main Streamlit application
├── components/
│   ├── __init__.py
│   └── chat.py               # Chat interface component
├── utils/
│   ├── __init__.py
│   └── session_manager.py    # Session state management
└── README.md                 # This file
```

## Next Steps (Phase 2)

Phase 2 will add:
- Orchestrator integration
- Actual pipeline execution
- Basic output display
- Error handling

