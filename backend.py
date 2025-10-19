# backend.py

from typing import TypedDict, List, Optional
from agents import planner_agent, research_agent, prompt_augmentor_agent, generator_agent

# --- 1. Define the State for the Graph ---

class GraphState(TypedDict):
    original_prompt: str
    user_file_paths: Optional[List[str]] = None
    research_plan: Optional[List[str]] = None
    context_documents: Optional[List[dict]] = None
    refined_prompt: Optional[str] = None
    questions_for_user: Optional[List[str]] = None
    final_output: Optional[str] = None

def run_graph(prompt: str, file_paths: List[str], model_config: dict):
    """
    Executes the agent pipeline sequentially and returns the final state.
    """
    state: GraphState = {
        "original_prompt": prompt,
        "user_file_paths": file_paths or [],
    }

    try:
        # Planner
        planner_result = planner_agent(state, model_name=model_config["planner"])
        state.update(planner_result or {})
        if state.get("error"):
            return state

        # Researcher
        research_result = research_agent(state)
        state.update(research_result or {})
        if state.get("error"):
            return state

        # Augmentor
        augmentor_result = prompt_augmentor_agent(
            state, model_name=model_config["augmentor"]
        )
        state.update(augmentor_result or {})
        if state.get("error") or state.get("questions_for_user"):
            return state

        # Generator
        generator_result = generator_agent(state, model_name=model_config["generator"])
        state.update(generator_result or {})
        return state
    except Exception as exc:
        state["error"] = f"Workflow execution failed: {exc}"
        return state
