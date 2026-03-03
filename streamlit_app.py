# import streamlit as st
# import tempfile
# import os

# from main import run_graph

# st.set_page_config(
#     page_title="Financial Multi-Agent System",
#     layout="wide"
# )

# st.title("📊 LangGraph + CrewAI Financial Multi-Agent System")

# st.markdown("Ask financial, news, risk or document-based questions.")

# # --------------------------
# # Inputs
# # --------------------------
# query = st.text_input("Ask your financial question:")

# ticker = st.text_input("Enter Company Ticker (Optional):")

# uploaded_file = st.file_uploader(
#     "Upload document (PDF / TXT / CSV) for RAG (Optional)",
#     type=["pdf", "txt", "csv"]
# )

# doc_path = ""

# if uploaded_file is not None:
#     with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
#         tmp_file.write(uploaded_file.read())
#         doc_path = tmp_file.name

# # --------------------------
# # Run Button
# # --------------------------
# if st.button("Run Analysis"):

#     if not query:
#         st.warning("Please enter a question.")
#     else:
#         with st.spinner("Running multi-agent analysis..."):

#             result = run_graph(query, ticker, doc_path)

#         st.success("Analysis Complete ✅")

#         st.markdown("---")
#         st.header("📑 FINAL REPORT")

#         for output in result["outputs"]:
#             if isinstance(output, str):
#                 st.markdown(output)
#             else:
#                 st.markdown(output.content)

#         st.markdown("---")

import streamlit as st
import tempfile

from main import run_graph

# =========================
# Streamlit Config
# =========================
st.set_page_config(
    page_title="Financial Multi-Agent System",
    layout="wide"
)

st.title("📊 LangGraph + CrewAI Financial Multi-Agent System")
st.markdown("Ask financial, news, risk, or document-based questions.")

# =========================
# Initialize session state
# =========================
if "last_result" not in st.session_state:
    st.session_state["last_result"] = None

query = st.text_input("Ask your financial question:")

uploaded_file = st.file_uploader(
    "Upload document (PDF / TXT / CSV) for RAG (Optional)",
    type=["pdf", "txt", "csv"]
)

doc_path = ""

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(uploaded_file.read())
        doc_path = tmp_file.name

# =========================
# Run Analysis Button
# =========================
if st.button("Run Analysis"):

    if not query:
        st.warning("Please enter a question.")
    else:
        with st.spinner("Running multi-agent analysis..."):
            # Run graph fresh for current query and doc
            result = run_graph(query, doc_path)
            st.session_state["last_result"] = result

# =========================
# Display Output
# =========================
if st.session_state["last_result"]:
    st.success("Analysis Complete ✅")
    st.markdown("---")
    st.header("📑 FINAL REPORT")

    for output in st.session_state["last_result"]["outputs"]:
        if isinstance(output, str):
            st.markdown(output)
        else:
            st.markdown(output.content)

    st.markdown("---")