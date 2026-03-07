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

import streamlit as st
import tempfile
import os
import time
import yfinance as yf
import numpy as np
import pandas as pd
import plotly.express as px

from main import run_graph, extract_tickers
import db_manager as db


# =========================
# Page Config
# =========================
st.set_page_config(
    page_title="Fin-Agent AI Pro",
    page_icon="📊",
    layout="wide"
)

db.init_db()


# =========================
# Custom UI Styling
# =========================
st.markdown("""
<style>

.stApp {
    background-color: #131314;
    color: #e3e3e3;
}

section[data-testid="stSidebar"] {
    background-color: #1e1f20;
}

.stChatMessage {
    background-color: #1e1f20;
    border-radius: 15px;
    padding: 15px;
    border: 1px solid #333;
}

div[data-testid="stChatMessageUser"] {
    background-color: #2b2c2f;
}

.stButton>button {
    border-radius: 20px;
    font-weight: bold;
}

</style>
""", unsafe_allow_html=True)


# =========================
# Session State
# =========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# =========================
# Chart Functions
# =========================
def plot_price_chart(ticker):

    stock = yf.Ticker(ticker)
    hist = stock.history(period="6mo")

    if hist.empty:
        return

    fig = px.line(
        hist,
        x=hist.index,
        y="Close",
        title=f"{ticker} Price Trend (6 Months)"
    )

    st.plotly_chart(fig, use_container_width=True)


def plot_risk_pie(ticker):

    stock = yf.Ticker(ticker)
    hist = stock.history(period="1y")

    if hist.empty:
        return

    returns = hist["Close"].pct_change().dropna()
    volatility = np.std(returns) * np.sqrt(252)

    risk_score = min(volatility * 100, 100)
    safe_score = 100 - risk_score

    df = pd.DataFrame({
        "Category": ["Safe", "Risk"],
        "Value": [safe_score, risk_score]
    })

    fig = px.pie(
        df,
        names="Category",
        values="Value",
        title=f"{ticker} Risk Distribution",
        color="Category",
        color_discrete_map={
            "Safe": "green",
            "Risk": "red"
        }
    )

    st.plotly_chart(fig, use_container_width=True)


def plot_volatility_bar(tickers):

    vol_data = {}

    for ticker in tickers:

        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")

        if hist.empty:
            continue

        returns = hist["Close"].pct_change().dropna()
        volatility = np.std(returns) * np.sqrt(252)

        vol_data[ticker] = volatility

    if not vol_data:
        return

    df = pd.DataFrame.from_dict(
        vol_data,
        orient="index",
        columns=["Volatility"]
    )

    fig = px.bar(
        df,
        x=df.index,
        y="Volatility",
        title="Volatility Comparison"
    )

    st.plotly_chart(fig, use_container_width=True)


# =========================
# Authentication Screen
# =========================
def auth_screen():

    col1, col2, col3 = st.columns([1,2,1])

    with col2:

        st.title("📊 Fin-Agent AI")
        st.subheader("Login to your Financial Analysis Dashboard")

        tab1, tab2 = st.tabs(["Login", "Sign Up"])

        with tab1:

            user = st.text_input("Username")
            pw = st.text_input("Password", type="password")

            if st.button("Login"):

                if db.check_user(user, pw):

                    st.session_state.logged_in = True
                    st.session_state.username = user
                    st.session_state.chat_history = db.get_chat_history(user)

                    st.success("Login successful")
                    st.rerun()

                else:
                    st.error("Invalid credentials")

        with tab2:

            new_user = st.text_input("Create Username")
            new_pw = st.text_input("Create Password", type="password")

            if st.button("Register"):

                if db.add_user(new_user, new_pw):
                    st.success("Account created! Please login.")
                else:
                    st.error("Username already exists")


# =========================
# Main Chat UI
# =========================
def main_chat_screen():

    # -------- Sidebar --------
    with st.sidebar:

        st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=80)

        st.title("Settings")

        st.write(f"Logged in as **{st.session_state.username}**")

        st.divider()

        st.subheader("Document Context (RAG)")

        uploaded_file = st.file_uploader(
            "Upload PDF / TXT",
            type=["pdf","txt"]
        )

        st.divider()

        if st.button("Clear Conversation"):
            st.session_state.chat_history = []
            st.rerun()

        if st.button("Sign Out"):

            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.chat_history = []

            st.rerun()


    # -------- Chat Header --------
    st.title("Financial Multi-Agent Analyst")
    st.caption("LangGraph + CrewAI + NVIDIA NIM")


    # -------- Chat History --------
    for message in st.session_state.chat_history:

        with st.chat_message(message["role"]):
            st.markdown(message["content"])


    # -------- Chat Input --------
    if prompt := st.chat_input("Ask about any stock..."):

        st.session_state.chat_history.append({
            "role":"user",
            "content":prompt
        })

        db.save_message(st.session_state.username,"user",prompt)

        with st.chat_message("user"):
            st.markdown(prompt)


        with st.chat_message("assistant"):

            with st.spinner("Agents analyzing market data..."):

                doc_path = ""

                if uploaded_file:

                    with tempfile.NamedTemporaryFile(delete=False) as tmp:
                        tmp.write(uploaded_file.read())
                        doc_path = tmp.name

                try:

                    result = run_graph(prompt, doc_path)

                    full_response = ""

                    for output in result.get("outputs",[]):

                        text = output if isinstance(output,str) else getattr(output,"content",str(output))

                        full_response += f"{text}\n\n---\n\n"

                    if not full_response:
                        full_response = "No response generated."


                    # Streaming effect
                    placeholder = st.empty()
                    streamed = ""

                    for word in full_response.split():

                        streamed += word + " "
                        placeholder.markdown(streamed)

                        time.sleep(0.02)


                    st.session_state.chat_history.append({
                        "role":"assistant",
                        "content":full_response
                    })

                    db.save_message(
                        st.session_state.username,
                        "assistant",
                        full_response
                    )


                    # =========================
                    # Charts Section
                    # =========================

                    tickers = extract_tickers(prompt)

                    st.divider()
                    st.subheader("📊 Market Visualizations")

                    for ticker in tickers:

                        st.markdown(f"## {ticker}")

                        col1, col2 = st.columns(2)

                        with col1:
                            plot_price_chart(ticker)

                        with col2:
                            plot_risk_pie(ticker)

                    if len(tickers) > 1:
                        plot_volatility_bar(tickers)


                except Exception as e:

                    st.error(f"Error: {str(e)}")


# =========================
# Entry Point
# =========================
if __name__ == "__main__":

    if not st.session_state.logged_in:
        auth_screen()

    else:
        main_chat_screen()