# agents.py

import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from tools import web_search_tool

# --- Robust Debugging Helper ---
def write_debug_file(step_name: str, data: dict):
    """Writes the output of a step to a file in the debug_output folder."""
    try:
        if not os.path.exists("debug_output"):
            os.makedirs("debug_output")
        filepath = f"debug_output/{step_name}.json"
        print(f"--- WRITING DEBUG FILE: {filepath} ---")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"!!! CRITICAL ERROR WRITING DEBUG FILE for {step_name}: {e} !!!")

def get_llm(model_name: str):
    return ChatGoogleGenerativeAI(model=model_name, temperature=0)

def execute_agent(agent_name: str, agent_logic, state, model_name=None):
    """A wrapper to run an agent with robust error handling and debugging."""
    print(f"---EXECUTING {agent_name.upper()} AGENT---")
    result = {}
    try:
        if model_name:
            result = agent_logic(state, model_name)
        else:
            result = agent_logic(state)
    except Exception as e:
        print(f"!!! ERROR in {agent_name} Agent: {e} !!!")
        result = {"error": f"{agent_name} Agent failed: {str(e)}"}
    finally:
        write_debug_file(f"{agent_name}_output", result)
        return result

# --- Agent Logic Functions ---
def _planner_logic(state, model_name):
    prompt = ChatPromptTemplate.from_template(
        "You are a research planner. Create a JSON object with a 'plan' key containing a list of 3-5 search queries for the user's request.\nRequest: {prompt}"
    )
    planner = prompt | get_llm(model_name) | JsonOutputParser()
    plan = planner.invoke({"prompt": state["original_prompt"]})
    return {"research_plan": plan.get('plan', [])}

def _researcher_logic(state):
    context_documents = []
    plan = state.get("research_plan", [])
    if not plan: raise ValueError("Research plan is empty.")
    for query in plan:
        search_results = web_search_tool.invoke({"query": query})
        for res in search_results: context_documents.append({"source": res.get('url'), "content": res.get('content')})
    
    user_files = state.get("user_file_paths", [])
    if user_files:
        # RAG logic here...
        pass # For brevity, assuming RAG logic is correct
    return {"context_documents": context_documents}

def _augmentor_logic(state, model_name):
    prompt_template = ChatPromptTemplate.from_template(
        "You are a prompt engineer. Rewrite the user's prompt into a detailed, XML-structured prompt using the provided context. If context is insufficient, output a JSON with a 'questions' key.\nOriginal Prompt: {original_prompt}\nContext: {context}"
    )
    augmentor = prompt_template | get_llm(model_name)
    formatted_context = "\n\n".join([f"Source: {doc['source']}\nContent: {doc['content']}" for doc in state.get("context_documents", [])])
    result_content = augmentor.invoke({"original_prompt": state["original_prompt"], "context": formatted_context}).content
    if result_content.strip().startswith('{'):
        return {"questions_for_user": JsonOutputParser().parse(result_content).get("questions", [])}
    else:
        return {"refined_prompt": result_content, "questions_for_user": []}

def _generator_logic(state, model_name):
    refined_prompt = state.get("refined_prompt")
    if not refined_prompt: raise ValueError("Refined prompt is missing.")
    generator = get_llm(model_name) | StrOutputParser()
    final_output = generator.invoke(refined_prompt)
    return {"final_output": final_output}

# --- Agent Node Functions ---
def planner_agent(state, model_name): return execute_agent("1_planner", _planner_logic, state, model_name)
def research_agent(state): return execute_agent("2_researcher", _researcher_logic, state)
def prompt_augmentor_agent(state, model_name): return execute_agent("3_augmentor", _augmentor_logic, state, model_name)
def generator_agent(state, model_name): return execute_agent("4_generator", _generator_logic, state, model_name)