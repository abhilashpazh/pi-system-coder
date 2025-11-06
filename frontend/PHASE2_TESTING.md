# Phase 2 Testing Guide

## Overview

Phase 2 integrates the orchestrator backend with the Streamlit UI, enabling full pipeline execution from the chat interface.

## Quick Start Test

1. **Ensure dependencies are installed**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Ensure environment variables are set** (`.env` file or environment):
   - `GEMINI_API_KEY` or `OPENAI_API_KEY` (depending on your LLM provider)

3. **Run the application**:
   ```bash
   streamlit run frontend/streamlit_app.py
   ```

## Test Checklist

### ✅ Test 1: Basic Pipeline Execution
- [ ] Type a simple request: "Read PI tag values for the last 24 hours"
- [ ] Click Send button
- [ ] Loading spinner appears: "🔄 Executing pipeline... This may take a moment."
- [ ] Pipeline executes (may take 30-60 seconds)
- [ ] Final output appears in chat history
- [ ] Output section displays below chat

### ✅ Test 2: Successful Execution
- [ ] Send a valid request
- [ ] Wait for pipeline to complete
- [ ] Check that status is "success"
- [ ] Verify final code output is displayed
- [ ] Code is syntax-highlighted (basic detection)
- [ ] Execution summary shows correct number of iterations
- [ ] Tools used are listed correctly

### ✅ Test 3: Error Handling
- [ ] Test with invalid API key (temporarily set wrong key)
- [ ] Verify error message displays clearly
- [ ] Error appears in chat history
- [ ] Error section shows in output area
- [ ] Debug information is available (expandable)

### ✅ Test 4: Multiple Requests
- [ ] Send first request and wait for completion
- [ ] Send second request: "Write PI tag values"
- [ ] Verify both requests execute independently
- [ ] Chat history shows both conversations
- [ ] Output section updates with latest result

### ✅ Test 5: Loading States
- [ ] Input field is disabled during execution
- [ ] Send button is disabled during execution
- [ ] Processing indicator shows: "🔄 Processing your request..."
- [ ] Spinner appears during pipeline execution
- [ ] UI remains responsive (no freezing)

### ✅ Test 6: Output Display
- [ ] Final code output is visible
- [ ] Code is formatted and readable
- [ ] Syntax highlighting works (basic)
- [ ] Execution summary expandable section works
- [ ] Tools used are listed correctly
- [ ] Iteration count is accurate

### ✅ Test 7: Clear Chat Functionality
- [ ] Send a request and get result
- [ ] Click "🗑️ Clear Chat" button
- [ ] Chat history is cleared
- [ ] Output section is cleared
- [ ] Can start fresh conversation

### ✅ Test 8: Edge Cases
- [ ] Send empty message (should be prevented by UI)
- [ ] Send very long request (1000+ characters)
- [ ] Send request with special characters
- [ ] Verify all cases handle gracefully

## Expected Behavior

### Successful Execution Flow:
1. User types message and clicks Send
2. Loading spinner appears
3. Pipeline executes (5 stages: API Selection → Logic → Code → Test → File Output)
4. Final code appears in chat (truncated if long)
5. Full output section displays below with:
   - Success message
   - Generated code with syntax highlighting
   - Execution summary (expandable)

### Error Flow:
1. User types message and clicks Send
2. Loading spinner appears
3. Error occurs during execution
4. Error message appears in chat
5. Error section displays with:
   - Error message
   - Debug information (expandable)
   - Last iteration details

## Sample Test Requests

### Simple Request:
```
Read PI tag values for the last 24 hours
```

### Medium Complexity:
```
Write a Python script to connect to PI Server and read tag values for temperature sensors
```

### Complex Request:
```
Create a PowerShell script using PI Web API to query all tags in a pointsource, filter by name pattern, and export to CSV
```

## Troubleshooting

### Import Errors
If you see "Could not import orchestrator":
- Check that `backend/agent/orchestrator.py` exists
- Verify Python path is set correctly
- Ensure all backend dependencies are installed

### API Key Errors
If you see API key errors:
- Check `.env` file exists and has correct key
- Verify environment variable is set: `GEMINI_API_KEY` or `OPENAI_API_KEY`
- Check key is valid and has credits

### Execution Timeout
If pipeline takes too long:
- Check network connection
- Verify LLM API is accessible
- Check API rate limits
- Consider reducing `max_iterations` in code

### No Output Displayed
If output section doesn't appear:
- Check browser console for errors (F12)
- Verify `last_result` is in session state
- Check that result has `status` field
- Try clearing chat and resubmitting

## Success Criteria

Phase 2 is complete when:
- ✅ All 8 test categories pass
- ✅ Pipeline executes successfully from UI
- ✅ Final code output is visible and formatted
- ✅ Errors are handled gracefully
- ✅ Multiple requests work correctly
- ✅ Loading states are clear
- ✅ Ready for Phase 3 (status display)

## Known Limitations (Phase 2)

These will be addressed in later phases:
- ⚠️ No real-time status updates (shows only after completion)
- ⚠️ Basic syntax highlighting (language detection is simple)
- ⚠️ No file download functionality (Phase 4)
- ⚠️ No metadata display (Phase 4)
- ⚠️ No progress tracking during execution (Phase 3)

## Next Steps

Once Phase 2 testing is complete:
1. Document any issues found
2. Fix any bugs
3. Proceed to Phase 3: Real-time Status Display

