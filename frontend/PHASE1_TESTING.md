# Phase 1 Testing Guide

## Quick Start Test

1. **Install Streamlit** (if not already installed):
   ```bash
   pip install streamlit>=1.28.0
   ```

2. **Run the application**:
   ```bash
   streamlit run frontend/streamlit_app.py
   ```

3. **Verify the app opens** in your browser at `http://localhost:8501`

## Test Checklist

### ✅ Test 1: App Launch
- [ ] App launches without errors
- [ ] Header "🔧 PI System Code Generator" displays
- [ ] Subtitle displays correctly
- [ ] Sidebar is visible with controls
- [ ] No errors in browser console (F12)

### ✅ Test 2: Chat Interface
- [ ] Chat input field is visible
- [ ] Placeholder text shows: "e.g., Read PI tag values for the last 24 hours"
- [ ] Send button is visible and enabled when text is entered
- [ ] Send button is disabled when input is empty

### ✅ Test 3: Message Sending
- [ ] Type a message: "Test message"
- [ ] Click Send button
- [ ] User message appears in chat with user avatar
- [ ] Assistant response appears (placeholder message for Phase 1)
- [ ] Input field clears after sending

### ✅ Test 4: Chat History
- [ ] Send multiple messages
- [ ] All messages appear in chronological order
- [ ] User messages show on the right (or with user styling)
- [ ] Assistant messages show on the left (or with assistant styling)
- [ ] Messages persist when interacting with sidebar

### ✅ Test 5: Clear Chat
- [ ] Click "🗑️ Clear Chat" button in sidebar
- [ ] All chat messages are removed
- [ ] Chat history is empty
- [ ] Can start new conversation

### ✅ Test 6: Session State Persistence
- [ ] Send a message
- [ ] Interact with sidebar (click buttons, expand sections)
- [ ] Verify messages remain in chat history
- [ ] Refresh the page (F5) - messages should persist (Streamlit session state)

### ✅ Test 7: UI Layout
- [ ] Header is properly styled
- [ ] Sidebar contains: Controls, About, Instructions sections
- [ ] Main chat area is properly sized
- [ ] No layout overflow or scrolling issues
- [ ] Responsive on different window sizes

### ✅ Test 8: Error Handling
- [ ] Try sending empty message (should not work - button disabled)
- [ ] Try rapid clicking Send button (should handle gracefully)
- [ ] No JavaScript errors in console
- [ ] No Python errors in terminal

## Expected Behavior

### Current Phase 1 Behavior:
- User can type and send messages
- Messages appear in chat history
- Assistant responds with placeholder: "Received your request: [message]\n\n(Orchestrator integration coming in Phase 2)"
- Clear Chat button resets the conversation

### What's NOT Implemented Yet (Phase 2+):
- ❌ Actual orchestrator integration
- ❌ Real pipeline execution
- ❌ Status display during processing
- ❌ Final code output display
- ❌ Error handling for backend calls

## Troubleshooting

### Import Errors
If you see import errors:
1. Ensure you're running from the project root
2. Check that `frontend/` directory structure is correct
3. Verify `sys.path` modification in `streamlit_app.py`

### Module Not Found
If `frontend` module is not found:
- Make sure you're running: `streamlit run frontend/streamlit_app.py`
- Not: `cd frontend && streamlit run streamlit_app.py`

### Session State Issues
- Streamlit session state persists during the session
- To reset, stop the app and restart
- Or use the Clear Chat button

## Success Criteria

Phase 1 is complete when:
- ✅ All 8 test categories pass
- ✅ No errors or crashes
- ✅ Chat interface is functional
- ✅ UI is clean and responsive
- ✅ Ready for Phase 2 integration

## Next Steps

Once Phase 1 testing is complete:
1. Document any issues found
2. Fix any bugs
3. Proceed to Phase 2: Orchestrator Integration

