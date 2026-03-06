# import streamlit as st
# import tempfile

# from main import run_graph

# # =========================
# # Streamlit Config
# # =========================
# st.set_page_config(
#     page_title="Financial Multi-Agent System",
#     layout="wide"
# )

# st.title("📊 LangGraph + CrewAI Financial Multi-Agent System")
# st.markdown("Ask financial, news, risk, or document-based questions.")

# # =========================
# # Initialize session state
# # =========================
# if "last_result" not in st.session_state:
#     st.session_state["last_result"] = None

# query = st.text_input("Ask your financial question:")

# uploaded_file = st.file_uploader(
#     "Upload document (PDF / TXT / CSV) for RAG (Optional)",
#     type=["pdf", "txt", "csv"]
# )

# doc_path = ""

# if uploaded_file is not None:
#     with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
#         tmp_file.write(uploaded_file.read())
#         doc_path = tmp_file.name

# # =========================
# # Run Analysis Button
# # =========================
# if st.button("Run Analysis"):

#     if not query:
#         st.warning("Please enter a question.")
#     else:
#         with st.spinner("Running multi-agent analysis..."):
#             # Run graph fresh for current query and doc
#             result = run_graph(query, doc_path)
#             st.session_state["last_result"] = result

# # =========================
# # Display Output
# # =========================
# if st.session_state["last_result"]:
#     st.success("Analysis Complete ✅")
#     st.markdown("---")
#     st.header("📑 FINAL REPORT")

#     for output in st.session_state["last_result"]["outputs"]:
#         if isinstance(output, str):
#             st.markdown(output)
#         else:
#             st.markdown(output.content)

#     st.markdown("---")

#patil code
import streamlit as st
import tempfile
import os
import time
from main import run_graph
import db_manager as db

# =========================
# 1. Page Configuration & Theme
# =========================
st.set_page_config(
    page_title="Fin-Agent AI Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize the SQLite Database
db.init_db()

# Custom CSS for Gemini-style Chat UI
st.markdown("""
    <style>
    /* Main background */
    .stApp {
        background-color: #131314;
        color: #e3e3e3;
    }
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #1e1f20 !important;
    }
    /* Chat Message Bubbles */
    .stChatMessage {
        background-color: #1e1f20;
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 10px;
        border: 1px solid #333;
    }
    /* User Message distinct style */
    div[data-testid="stChatMessageUser"] {
        background-color: #2b2c2f;
    }
    /* Buttons */
    .stButton>button {
        border-radius: 20px;
        text-transform: uppercase;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# =========================
# 2. Session State Management
# =========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# =========================
# 3. Authentication Flow
# =========================
def auth_screen():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("📊 Fin-Agent AI")
        st.subheader("Login to your Analysis Dashboard")

        tab_login, tab_signup = st.tabs(["Sign In", "Create Account"])

        with tab_login:
            user = st.text_input("Username", key="login_user")
            pw = st.text_input("Password", type="password", key="login_pw")

            if st.button("Login"):
                if db.check_user(user, pw):
                    st.session_state.logged_in = True
                    st.session_state.username = user
                    st.session_state.chat_history = db.get_chat_history(user)
                    st.success(f"Welcome back, {user}!")
                    st.rerun()
                else:
                    st.error("Invalid Username or Password")

        with tab_signup:
            new_user = st.text_input("Choose Username", key="reg_user")
            new_pw = st.text_input("Choose Password", type="password", key="reg_pw")
            confirm_pw = st.text_input("Confirm Password", type="password", key="reg_pw_conf")

            if st.button("Register"):
                if new_pw != confirm_pw:
                    st.error("Passwords do not match")
                elif len(new_pw) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    if db.add_user(new_user, new_pw):
                        st.success("Account created! You can now login.")
                    else:
                        st.error("Username already taken")

# =========================
# 4. Main Chat Interface
# =========================
def main_chat_screen():

    # -------- Sidebar --------
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=80)
        st.title("Settings")
        st.write(f"Logged in: **{st.session_state.username}**")

        st.divider()

        st.subheader("Document Context (RAG)")
        uploaded_file = st.file_uploader(
            "Upload PDF/TXT",
            type=["pdf", "txt"],
            help="Agents will query this document for answers."
        )

        st.divider()

        if st.button("Clear Conversation"):
            st.session_state.chat_history = []
            st.rerun()

        if st.button("Sign Out", type="secondary"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.chat_history = []
            st.rerun()

    # -------- Chat Area --------
    st.title("Financial Multi-Agent Analyst")
    st.caption("Powered by LangGraph, CrewAI, and NVIDIA NIMs")

    # Display Chat History
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # -------- Chat Input --------
    if prompt := st.chat_input("What would you like to analyze today?"):

        # Store user message
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        db.save_message(st.session_state.username, "user", prompt)

        with st.chat_message("user"):
            st.markdown(prompt)

        # -------- Assistant Response --------
        with st.chat_message("assistant"):

            with st.spinner("Agents are analyzing market data..."):

                doc_path = ""

                if uploaded_file:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
                        tmp.write(uploaded_file.read())
                        doc_path = tmp.name

                try:

                    result = run_graph(prompt, doc_path)

                    full_response = ""

                    for output in result.get("outputs", []):
                        text = output if isinstance(output, str) else getattr(output, "content", str(output))
                        full_response += f"{text}\n\n---\n\n"

                    if not full_response:
                        full_response = "Agents completed the task but returned no specific text output."

                    # -------- STREAMING OUTPUT --------
                    placeholder = st.empty()
                    streamed_text = ""

                    for word in full_response.split():
                        streamed_text += word + " "
                        placeholder.markdown(streamed_text)
                        time.sleep(0.02)

                    # Save assistant response
                    st.session_state.chat_history.append(
                        {"role": "assistant", "content": full_response}
                    )

                    db.save_message(
                        st.session_state.username,
                        "assistant",
                        full_response
                    )

                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")


# =========================
# Execution Entry Point
# =========================
if __name__ == "__main__":

    if not st.session_state.logged_in:
        auth_screen()
    else:
        main_chat_screen()