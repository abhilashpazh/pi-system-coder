"""
Status display component for Streamlit UI

Shows real-time pipeline execution status, current tool, and progress.
"""

import streamlit as st
from typing import Dict, Any, Optional, List


# Tool name to display name mapping
TOOL_DISPLAY_NAMES = {
    "api_selection": "API Selection",
    "logic_creation": "Logic Creation",
    "code_creation": "Code Creation",
    "test_run": "Test Run",
    "file_output": "File Output"
}

# Tool to stage mapping
TOOL_TO_STAGE = {
    "api_selection": 1,
    "logic_creation": 2,
    "code_creation": 3,
    "test_run": 4,
    "file_output": 5
}

# Stage descriptions
STAGE_DESCRIPTIONS = {
    1: "Selecting the most appropriate PI System API",
    2: "Creating step-by-step logic and pseudo-code",
    3: "Generating implementation code",
    4: "Running quality checks and validation",
    5: "Packaging final output with documentation"
}


def render_status_display(
    current_tool: Optional[str] = None,
    current_stage: Optional[int] = None,
    total_stages: int = 5,
    tool_result: Optional[str] = None,
    iteration_count: int = 0,
    is_completed: bool = False,
    tool_has_completed: bool = False
) -> None:
    """
    Render the status display showing current execution state.
    
    Args:
        current_tool: Name of the current tool being executed
        current_stage: Current stage number (1-5)
        total_stages: Total number of stages (default: 5)
        tool_result: Result from the last tool execution (optional)
        iteration_count: Total number of iterations completed
    """
    st.subheader("📊 Execution Status")
    
    # Current status
    if is_completed or (current_stage == total_stages and current_tool == "file_output"):
        # Pipeline completed
        st.success(f"✅ **Pipeline Completed Successfully!**\n\nAll {total_stages} stages completed.")
    elif current_tool:
        display_name = TOOL_DISPLAY_NAMES.get(current_tool, current_tool.title())
        stage_num = current_stage or TOOL_TO_STAGE.get(current_tool)
        
        if stage_num:
            stage_desc = STAGE_DESCRIPTIONS.get(stage_num, "")
            # Check if tool has completed (has tool_result)
            if tool_has_completed:
                st.success(f"✅ **Stage {stage_num}/{total_stages}: {display_name} - Completed**\n\n{stage_desc}")
            else:
                st.info(f"🔄 **Stage {stage_num}/{total_stages}: {display_name}**\n\n{stage_desc}")
        else:
            if tool_has_completed:
                st.success(f"✅ **{display_name} - Completed**")
            else:
                st.info(f"🔄 **Executing: {display_name}**")
    else:
        st.info("⏳ Waiting to start...")
    
    # Progress bar - always show, update based on current stage
    if is_completed or (current_stage == total_stages):
        # Pipeline completed - show 100% progress
        st.progress(1.0, text=f"✅ Completed: All {total_stages} stages finished")
    elif current_stage:
        # Calculate progress: if we're on stage N, we've completed N-1 stages and are working on stage N
        # Progress should reflect completed stages, so stage 1 = 0% complete, stage 2 = 20% complete, etc.
        # But we want to show we're working on it, so stage 1 = 20% (working on it), stage 2 = 40%, etc.
        progress = current_stage / total_stages
        st.progress(progress, text=f"Stage {current_stage}/{total_stages}: {TOOL_DISPLAY_NAMES.get(current_tool, 'In Progress')}")
    elif current_tool:
        # Tool is executing but stage not determined yet - show minimal progress
        st.progress(0.1, text="Starting pipeline execution...")
    else:
        # No tool yet - show waiting state
        st.progress(0.0, text="Waiting to start...")
    
    # Stage indicators
    render_stage_indicators(current_stage, total_stages)
    
    # Iteration count
    if iteration_count > 0:
        st.caption(f"Total iterations: {iteration_count}")
    
    # Tool result preview (if available)
    if tool_result:
        with st.expander("🔍 Latest Tool Result Preview"):
            # Truncate if too long
            preview = tool_result[:1000] + "..." if len(tool_result) > 1000 else tool_result
            st.text(preview)


def render_stage_indicators(current_stage: Optional[int], total_stages: int = 5) -> None:
    """
    Render visual stage indicators showing progress through the pipeline.
    
    Args:
        current_stage: Current stage number (1-5) or None
        total_stages: Total number of stages (default: 5)
    """
    stages = [
        ("1️⃣", "API Selection", 1),
        ("2️⃣", "Logic Creation", 2),
        ("3️⃣", "Code Creation", 3),
        ("4️⃣", "Test Run", 4),
        ("5️⃣", "File Output", 5)
    ]
    
    # Create columns for stage indicators
    cols = st.columns(total_stages)
    
    for idx, (emoji, name, stage_num) in enumerate(stages[:total_stages]):
        with cols[idx]:
            if current_stage is None:
                # Not started
                st.markdown(f"{emoji}\n**{name}**\n⏸️")
            elif stage_num < current_stage:
                # Completed
                st.markdown(f"{emoji}\n**{name}**\n✅")
            elif stage_num == current_stage:
                # Current
                st.markdown(f"{emoji}\n**{name}**\n🔄")
            else:
                # Pending
                st.markdown(f"{emoji}\n**{name}**\n⏳")


def render_iteration_details(iterations: List[Dict[str, Any]]) -> None:
    """
    Render detailed information about all iterations.
    
    Args:
        iterations: List of iteration dictionaries from orchestrator
    """
    if not iterations:
        return
    
    with st.expander("📋 Detailed Execution Log", expanded=False):
        for iteration in iterations:
            iter_num = iteration.get('iteration', 0)
            tool_call = iteration.get('tool_call')
            tool_result = iteration.get('tool_result')
            final_answer = iteration.get('final_answer')
            
            st.markdown(f"**Iteration {iter_num}**")
            
            if tool_call:
                tool_name = tool_call.get('function', 'unknown')
                display_name = TOOL_DISPLAY_NAMES.get(tool_name, tool_name.title())
                st.write(f"🔧 Tool: {display_name}")
                
                # Show arguments (truncated)
                args = tool_call.get('arguments', {})
                if args:
                    with st.expander("Arguments", expanded=False):
                        # Show only key arguments, not full context
                        key_args = {k: v for k, v in args.items() if k != 'context'}
                        st.json(key_args)
            
            if tool_result:
                with st.expander("Tool Result", expanded=False):
                    # Truncate long results
                    result_preview = tool_result[:500] + "..." if len(tool_result) > 500 else tool_result
                    st.text(result_preview)
            
            if final_answer:
                st.success("✅ Final answer received")
            
            st.divider()


def get_current_status_from_iterations(iterations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract current status information from iteration history.
    
    Args:
        iterations: List of iteration dictionaries
    
    Returns:
        Dictionary with current status information:
        - current_tool: Name of current tool
        - current_stage: Current stage number
        - tool_result: Last tool result
        - iteration_count: Number of iterations
    """
    if not iterations:
        return {
            "current_tool": None,
            "current_stage": None,
            "tool_result": None,
            "iteration_count": 0
        }
    
    last_iteration = iterations[-1]
    tool_call = last_iteration.get('tool_call')
    tool_result = last_iteration.get('tool_result')
    
    current_tool = None
    current_stage = None
    
    if tool_call:
        current_tool = tool_call.get('function')
        current_stage = TOOL_TO_STAGE.get(current_tool)
    
    return {
        "current_tool": current_tool,
        "current_stage": current_stage,
        "tool_result": tool_result,
        "iteration_count": len(iterations)
    }


def render_status_in_sidebar(
    current_tool: Optional[str] = None,
    current_stage: Optional[int] = None,
    total_stages: int = 5
) -> None:
    """
    Render a compact status display in the sidebar.
    
    Args:
        current_tool: Name of the current tool
        current_stage: Current stage number
        total_stages: Total number of stages
    """
    st.sidebar.header("📊 Status")
    
    if current_tool:
        display_name = TOOL_DISPLAY_NAMES.get(current_tool, current_tool.title())
        if current_stage:
            st.sidebar.write(f"**Stage {current_stage}/{total_stages}**")
            st.sidebar.write(f"🔄 {display_name}")
            
            # Mini progress bar
            progress = current_stage / total_stages
            st.sidebar.progress(progress)
        else:
            st.sidebar.write(f"🔄 {display_name}")
    else:
        st.sidebar.write("⏳ Ready")
    
    st.sidebar.divider()

