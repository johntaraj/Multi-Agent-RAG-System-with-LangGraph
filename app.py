# app.py

# --- IMPORTANT: LOAD ENV VARIABLES FIRST ---
from dotenv import load_dotenv

load_dotenv()
# --- END IMPORTANT SECTION ---

import os
import tempfile

import streamlit as st

from backend import run_graph

# --- Page Configuration ---
st.set_page_config(page_title="Augmentor Agent", page_icon=":sparkles:", layout="wide")

# --- Global UI Tweaks ---
st.markdown(
    """
    <style>
    div.chat-input-wrapper {
        display: flex;
        flex-wrap: wrap;
        align-items: flex-end;
        gap: 0.75rem;
    }
    div.chat-input-wrapper div[data-testid="stChatInput"] {
        flex: 1 1 15rem;
        min-width: 0;
    }
    div.chat-input-wrapper div[data-testid="stChatInput"] textarea {
        padding-right: 1rem !important;
    }
    div.chat-input-wrapper div[data-testid="stPopoverAnchor"] {
        position: static;
        flex-shrink: 0;
    }
    div.chat-input-wrapper div[data-testid="stPopoverAnchor"] button {
        border: none;
        border-radius: 999px;
        width: 2.5rem;
        height: 2.5rem;
        padding: 0;
        line-height: 1;
        background-color: var(--primary-color);
        color: var(--background-color);
        box-shadow: 0 4px 10px rgba(0,0,0,0.12);
        display: flex;
        align-items: center;
        justify-content: center;
    }
    div.chat-input-wrapper div[data-testid="stPopoverAnchor"] button:hover {
        filter: brightness(1.05);
        box-shadow: 0 6px 16px rgba(0,0,0,0.16);
    }
    div.chat-input-wrapper div[data-testid="stPopoverAnchor"] button span {
        display: none;
    }
    div.chat-input-wrapper div[data-testid="stPopoverAnchor"] button svg {
        display: none;
    }
    div.chat-input-wrapper div[data-testid="stPopoverAnchor"] button::before {
        content: "+";
        font-size: 1.35rem;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploaded_files_info" not in st.session_state:
    st.session_state.uploaded_files_info = []

# --- Sidebar Configuration ---
with st.sidebar:
    st.header(":gear: Agent Configuration")

    # --- CORRECT MODELS ---
    available_models = ["gemini-2.5-flash-lite", "gemini-2.5-flash"]
    model_config = {
        "planner": st.selectbox("Planner Model", available_models, index=1),
        "augmentor": st.selectbox("Augmentor Model", available_models, index=1),
        "generator": st.selectbox("Generator Model", available_models, index=1),
    }
    st.markdown("---")
    st.info("Use the :heavy_plus_sign: button in the chat input to upload files.")

# --- Main Chat Interface ---
st.title("Augmentor Agent")
st.markdown("Your AI-powered research and generation assistant.")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            sources_history = message.get("sources") or []
            if sources_history:
                with st.popover("Sources"):
                    for index, source in enumerate(sources_history, start=1):
                        link = source.get("source", "Unknown source")
                        st.markdown(f"**{index}:** [{link}]({link})")

# --- UI REDESIGN: File Uploader and Chat Input ---
chat_input_container = st.container()
with chat_input_container:
    st.markdown('<div class="chat-input-wrapper">', unsafe_allow_html=True)
    file_names_str = (
        f" | {len(st.session_state.uploaded_files_info)} file(s) attached"
        if st.session_state.uploaded_files_info
        else ""
    )
    prompt = st.chat_input(f"What would you like to build?{file_names_str}")
    with st.popover(" ✚ "):
        uploaded_files = st.file_uploader(
            "Upload files (PDF, TXT, PY)",
            type=["pdf", "txt", "py"],
            accept_multiple_files=True,
            key="file_uploader",
        )
        existing_files = st.session_state.uploaded_files_info
        if uploaded_files:
            new_files = [{"name": f.name, "data": f.getvalue()} for f in uploaded_files]
            if new_files != existing_files:
                st.session_state.uploaded_files_info = new_files
                st.rerun()
            st.success(f"{len(st.session_state.uploaded_files_info)} files ready!")
        elif existing_files:
            st.session_state.uploaded_files_info = []
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# --- Main Logic ---
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        sources_container = st.container()

        # Handle file saving
        temp_dir = tempfile.mkdtemp()
        file_paths = []
        if st.session_state.uploaded_files_info:
            for file_info in st.session_state.uploaded_files_info:
                file_path = os.path.join(temp_dir, file_info["name"])
                with open(file_path, "wb") as f:
                    f.write(file_info["data"])
                file_paths.append(file_path)
            st.info(f"Processing {len(file_paths)} uploaded file(s)...")

        full_response = ""
        try:
            with st.spinner("The agent is thinking..."):
                final_state = run_graph(prompt, file_paths, model_config) or {}

            if not isinstance(final_state, dict):
                raise ValueError("Workflow returned an invalid response.")
            workflow_error = final_state.get("error")
            if workflow_error:
                error_message = f"An error occurred in the workflow: {workflow_error}"
                message_placeholder.error(error_message)
                full_response = error_message
                sources = []
            else:
                final_output = final_state.get("final_output")
                if final_output:
                    message_placeholder.markdown(final_output)
                    full_response = final_output
                    sources = final_state.get("context_documents") or []
                    if sources:
                        with sources_container.popover("Sources"):
                            for index, source in enumerate(sources, start=1):
                                link = source.get("source", "Unknown source")
                                st.markdown(f"**{index}:** [{link}]({link})")
                else:
                    follow_up_questions = final_state.get("questions_for_user") or []
                    if follow_up_questions:
                        questions_md = "\n".join(f"- {question}" for question in follow_up_questions)
                        need_info_msg = "The agent needs a bit more information:\n" + questions_md
                        message_placeholder.warning(need_info_msg)
                        full_response = need_info_msg
                        sources = []
                    else:
                        fallback_error = "Error: The agent workflow did not return a final output."
                        message_placeholder.error(fallback_error)
                        full_response = fallback_error
                        sources = []

        except Exception as e:
            critical_error = f"A critical error occurred: {e}"
            message_placeholder.error(critical_error)
            full_response = critical_error
            sources = []

        finally:
            for path in file_paths:
                try:
                    os.remove(path)
                except OSError:
                    pass
            try:
                os.rmdir(temp_dir)
            except OSError:
                pass
            st.session_state.uploaded_files_info = []

    st.session_state.messages.append(
        {"role": "assistant", "content": full_response, "sources": sources}
    )
    st.rerun()
