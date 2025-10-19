
# --- IMPORTANT: LOAD ENV VARIABLES FIRST ---
from dotenv import load_dotenv
load_dotenv()
# --- END IMPORTANT SECTION ---

import os
from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, START, END
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

# --- 2. Define the Nodes and Edges ---

def should_continue(state: GraphState) -> str:
    """
    This is our main router. It decides the next step based on the state.
    """
    # Use .get() to safely access the key, providing an empty list if it's missing.
    if state.get("questions_for_user"):
        return "ask_human"
    else:
        return "generate"

def build_graph():
    """
    Builds the LangGraph agentic workflow.
    """
    workflow = StateGraph(GraphState)

    # Add nodes to the graph
    workflow.add_node("planner", planner_agent)
    workflow.add_node("researcher", research_agent)
    workflow.add_node("augmentor", prompt_augmentor_agent)
    workflow.add_node("generator", generator_agent)
    workflow.add_node("ask_human", lambda state: state)

    # Set the entry point using an edge from START
    workflow.add_edge(START, "planner")

    # Add the rest of the edges
    workflow.add_edge("planner", "researcher")
    workflow.add_edge("researcher", "augmentor")
    workflow.add_conditional_edges(
        "augmentor",
        should_continue,
        {
            "ask_human": "ask_human",
            "generate": "generator",
        }
    )
    workflow.add_edge("generator", END)
    workflow.add_edge("ask_human", "planner")

    # Compile the graph
    return workflow.compile()

# --- 3. The Main Terminal Interface ---

def main():
    print("--- Welcome to the Augmentor Agent ---")
    
    original_prompt = input("Please enter your project idea or question:\n> ")
    file_paths_input = input("Enter paths to local files (PDF, TXT), comma-separated. Press Enter to skip:\n> ")
    user_file_paths = [path.strip() for path in file_paths_input.split(',') if path.strip()]

    app = build_graph()

    current_state = {
        "original_prompt": original_prompt,
        "user_file_paths": user_file_paths,
    }
    
    print("\n--- Initializing Agent Workflow ---")

    while True:
        # The stream method lets us run the graph and get outputs from each step
        for event in app.stream(current_state, {"recursion_limit": 25}):
            step_name = list(event.keys())[0]
            step_output = event[step_name]

            print(f"\n--- Executing Step: {step_name} ---")
            
            # The output of a step can be None, so we handle that gracefully
            if step_output:
                current_state.update(step_output)

            if step_name == "ask_human":
                questions = current_state.get("questions_for_user", [])
                if questions:
                    print("\nThe agent has some questions for you:")
                    for q in questions:
                        print(f"- {q}")
                    
                    human_answer = input("\nPlease provide your answers:\n> ")
                    
                    current_state["original_prompt"] += f"\n\nUser's clarification: {human_answer}"
                    current_state["questions_for_user"] = [] # Clear questions
                    break # Restart the graph stream with the new info
        else:
            # This 'else' belongs to the 'for' loop. It runs if the loop finishes without a 'break'.
            # This means the graph has reached the END state.
            break

    print("\n\n--- ✨ Final Result ✨ ---\n")
    print(current_state.get("final_output", "No output was generated."))


if __name__ == "__main__":
    main()