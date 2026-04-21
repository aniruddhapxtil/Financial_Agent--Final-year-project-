# import streamlit as st
# import tempfile
# import time
# import yfinance as yf
# import numpy as np
# import pandas as pd
# import plotly.express as px

# from main import run_graph, extract_tickers
# from evaluation import evaluate_system
# import db_manager as db

# @st.cache_data
# def run_eval_cached():
#     return evaluate_system()


# # =========================
# # PAGE CONFIG
# # =========================
# st.set_page_config(
#     page_title="Fin-Agent AI Pro",
#     page_icon="📊",
#     layout="wide"
# )

# db.init_db()


# # =========================
# # SESSION STATE
# # =========================

# if "page" not in st.session_state:
#     st.session_state.page = "chat"

# if "logged_in" not in st.session_state:
#     st.session_state.logged_in = False

# if "username" not in st.session_state:
#     st.session_state.username = None

# if "chat_history" not in st.session_state:
#     st.session_state.chat_history = []

# if "current_chat_id" not in st.session_state:
#     st.session_state.current_chat_id = None


# # =========================
# # CHARTS
# # =========================
# def plot_price_chart(ticker):
#     stock = yf.Ticker(ticker)
#     hist = stock.history(period="6mo")

#     if hist.empty:
#         return

#     fig = px.line(
#         hist,
#         x=hist.index,
#         y="Close",
#         title=f"{ticker} Price Trend (6 Months)"
#     )

#     st.plotly_chart(fig, use_container_width=True, key=f"price_{ticker}_{time.time()}")


# def plot_risk_pie(ticker):
#     stock = yf.Ticker(ticker)
#     hist = stock.history(period="1y")

#     if hist.empty:
#         return

#     returns = hist["Close"].pct_change().dropna()
#     volatility = np.std(returns) * np.sqrt(252)

#     risk_score = min(volatility * 100, 100)
#     safe_score = 100 - risk_score

#     df = pd.DataFrame({
#         "Category": ["Safe", "Risk"],
#         "Value": [safe_score, risk_score]
#     })

#     fig = px.pie(
#         df,
#         names="Category",
#         values="Value",
#         title=f"{ticker} Risk Distribution"
#     )

#     st.plotly_chart(fig, use_container_width=True, key=f"price_{ticker}_{time.time()}")

#     # =========================
# # GRAPH VISUALIZATION
# # =========================
# import networkx as nx
# import plotly.graph_objects as go

# def render_graph(routes):

#     G = nx.DiGraph()

#     G.add_node("orchestrator")

#     for r in routes:
#         G.add_edge("orchestrator", r)

#     pos = nx.spring_layout(G)

#     edge_x = []
#     edge_y = []

#     for edge in G.edges():
#         x0, y0 = pos[edge[0]]
#         x1, y1 = pos[edge[1]]
#         edge_x += [x0, x1, None]
#         edge_y += [y0, y1, None]

#     edge_trace = go.Scatter(
#         x=edge_x, y=edge_y,
#         mode='lines'
#     )

#     node_x = []
#     node_y = []
#     text = []

#     for node in G.nodes():
#         x, y = pos[node]
#         node_x.append(x)
#         node_y.append(y)
#         text.append(node)

#     node_trace = go.Scatter(
#         x=node_x,
#         y=node_y,
#         mode='markers+text',
#         text=text,
#         textposition="bottom center"
#     )

#     fig = go.Figure(data=[edge_trace, node_trace])

#     st.plotly_chart(fig, use_container_width=True)


# # =========================
# # AUTH SCREEN
# # =========================
# def auth_screen():
#     st.title("📊 Fin-Agent AI")

#     tab1, tab2 = st.tabs(["Login", "Sign Up"])

#     with tab1:
#         user = st.text_input("Username")
#         pw = st.text_input("Password", type="password")

#         if st.button("Login"):
#             if db.check_user(user, pw):
#                 st.session_state.logged_in = True
#                 st.session_state.username = user

#                 chats = db.get_user_chats(user)

#                 if chats:
#                     chat_id = chats[0][0]
#                 else:
#                     chat_id = db.create_chat(user)

#                 st.session_state.current_chat_id = chat_id
#                 st.session_state.chat_history = db.get_chat_messages(chat_id)

#                 st.rerun()
#             else:
#                 st.error("Invalid credentials")

#     with tab2:
#         new_user = st.text_input("New Username")
#         new_pw = st.text_input("New Password", type="password")

#         if st.button("Register"):
#             if db.add_user(new_user, new_pw):
#                 st.success("Account created!")
#             else:
#                 st.error("Username exists")


# # =========================
# # MAIN CHAT UI
# # =========================
# def main_chat_screen():

#     # ===== SIDEBAR =====
#     with st.sidebar:

#         st.markdown("""
#             <style>
#             .signout-btn button {
#                 border-radius: 25px;
#                 padding: 6px 14px;
#                 font-weight: 600;
#             }
#             </style>
#         """, unsafe_allow_html=True)

#         col1, col2 = st.columns([3, 2])

#         with col1:
#             st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=80)

#         with col2:
#             st.markdown('<div class="signout-btn">', unsafe_allow_html=True)
#             if st.button("Sign Out"):
#                 st.session_state.logged_in = False
#                 st.session_state.username = None
#                 st.session_state.chat_history = []
#                 st.session_state.current_chat_id = None
#                 st.rerun()
#             st.markdown('</div>', unsafe_allow_html=True)

#         st.markdown(f"### 👤 {st.session_state.username}")

#         st.divider()

#         col1, col2 = st.columns(2)

#         with col1:
#             if st.button("➕ New "):
#                 chat_id = db.create_chat(st.session_state.username)
#                 st.session_state.current_chat_id = chat_id
#                 st.session_state.chat_history = []
#                 st.rerun()

#         with col2:
#             if st.button("🧹 Clear "):
#                 st.session_state.chat_history = []
#                 st.rerun()

#         st.divider()

#         st.subheader("💬 Previous Chats")

#         chats = db.get_user_chats(st.session_state.username)

#         for chat_id, title in chats:
#             if st.button(f"🗂️ {title}", key=f"chat_{chat_id}"):
#                 st.session_state.current_chat_id = chat_id
#                 st.session_state.chat_history = db.get_chat_messages(chat_id)
#                 st.rerun()

#         st.divider()

#         uploaded_file = st.file_uploader("Upload PDF / TXT", type=["pdf", "txt"])

#     # ===== MAIN =====
#     # st.title("Financial Multi-Agent Analyst")

#     col1, col2 = st.columns([8, 2])

#     with col1:
#         st.title("Financial Multi-Agent Analyst")

#     with col2:
#         if st.button("Check Dashboard"):
#             st.session_state.page = "dashboard"
#             st.rerun()

#     # =========================
#     # RENDER CHAT HISTORY
#     # =========================
#     for msg in st.session_state.chat_history:

#         with st.chat_message(msg["role"]):
#             st.markdown(msg["content"])

#             if "charts" in msg:

#                 tickers = msg["charts"]["tickers"]
#                 routes = msg["charts"]["routes"]

#                 if "financial" in routes:
#                     st.divider()
#                     st.subheader("📈 Price Trend")

#                     for ticker in tickers:
#                         plot_price_chart(ticker)

#                 if "risk" in routes:
#                     st.divider()
#                     st.subheader("⚠️ Risk Analysis")

#                     for ticker in tickers:
#                         plot_risk_pie(ticker)

#     # =========================
#     # INPUT
#     # =========================
#     if prompt := st.chat_input("Ask about any stock..."):

#         # SAVE USER MESSAGE
#         st.session_state.chat_history.append({
#             "role": "user",
#             "content": prompt
#         })

#         db.save_message(
#             st.session_state.current_chat_id,
#             "user",
#             prompt
#         )

#         # ✅ SHOW USER MESSAGE IMMEDIATELY
#         with st.chat_message("user"):
#             st.markdown(prompt)

#         # ASSISTANT RESPONSE
#         with st.chat_message("assistant"):

#             with st.spinner("Analyzing..."):

#                 doc_path = ""

#                 if uploaded_file:
#                     with tempfile.NamedTemporaryFile(delete=False) as tmp:
#                         tmp.write(uploaded_file.read())
#                         doc_path = tmp.name

#                 # result = run_graph(prompt, doc_path)
#                 result, debug_data = run_graph(prompt, doc_path)

#                 if "debug_logs" not in st.session_state:
#                     st.session_state.debug_logs = []

#                 st.session_state.debug_logs.append(debug_data)

#                 outputs = result.get("outputs", [])

#                 # formatted_outputs = []

#                 # for o in outputs:
#                 #     if isinstance(o, str):
#                 #         formatted_outputs.append(o)
#                 #     else:
#                 #         content = getattr(o, "content", str(o))
#                 #         formatted_outputs.append(content)

#                 formatted_outputs = []

#                 for o in outputs:
#                     if isinstance(o, str):
#                         content = o
#                     else:
#                         content = getattr(o, "content", str(o))

#                     # 🔥 REMOVE INTERNAL THINKING
#                     cleaned_lines = []
#                     for line in content.split("\n"):
#                         if not line.strip().startswith(("Thought:", "Action:", "Observation:")):
#                             cleaned_lines.append(line)

#                     cleaned_content = "\n".join(cleaned_lines).strip()

#                     if cleaned_content:
#                         formatted_outputs.append(cleaned_content)

#                 full_response = "\n\n".join(formatted_outputs)

#                 # SHOW RESPONSE
#                 st.markdown(full_response)

#                 routes = result.get("routes", [])
#                 tickers = extract_tickers(prompt)

#                 if "rag" not in routes:

#                     if "financial" in routes:
#                         st.divider()
#                         st.subheader("📈 Price Trend")

#                         for ticker in tickers:
#                             plot_price_chart(ticker)

#                     if "risk" in routes:
#                         st.divider()
#                         st.subheader("⚠️ Risk Analysis")

#                         for ticker in tickers:
#                             plot_risk_pie(ticker)

#                 # SAVE ASSISTANT MESSAGE
#                 st.session_state.chat_history.append({
#                     "role": "assistant",
#                     "content": full_response,
#                     "charts": {
#                         "tickers": tickers,
#                         "routes": routes
#                     }
#                 })

#                 charts_data = {
#                     "tickers": tickers,
#                     "routes": routes
#                 }

#                 db.save_message(
#                     st.session_state.current_chat_id,
#                     "assistant",
#                     full_response,
#                     charts=charts_data
#                 )

#                 # AUTO TITLE
#                 if len(st.session_state.chat_history) == 2:
#                     db.update_chat_title(
#                         st.session_state.current_chat_id,
#                         prompt[:40]
#                     )

# # def dashboard_screen():

# #     st.title("📊 Multi-Agent Execution Dashboard")

# #     if st.button("⬅ Back to Chat"):
# #         st.session_state.page = "chat"
# #         st.rerun()

# #     logs = st.session_state.get("debug_logs", [])

# #     if not logs:
# #         st.info("No runs yet.")
# #         return

# #     for log in reversed(logs):

# #         st.subheader(f"🕒 {log['timestamp']}")

# #         st.markdown(f"**Query:** {log['query']}")
# #         st.markdown(f"**Tickers:** {', '.join(log['tickers'])}")

# #         st.markdown(f"**Agents Triggered:** {', '.join(log['routes'])}")

# #         st.markdown(f"**⏱ Total Latency:** {log['latency_total']} sec")


# #         # 👇 ADD THIS HERE
# #         render_graph(log["routes"])

# #         st.divider()

# def dashboard_screen():

#     st.title("📊 Multi-Agent Execution Dashboard")

#     if st.button("⬅ Back to Chat"):
#         st.session_state.page = "chat"
#         st.rerun()

#     # =========================
#     # 🔥 NEW: EVALUATION SECTION
#     # =========================
#     st.divider()
#     st.subheader("📊 System Benchmarking")

#     if st.button("🚀 Run Evaluation Benchmark"):

#         with st.spinner("Running evaluation on dataset..."):

#             results = run_eval_cached()

#             st.session_state.eval_results = results

#     # SHOW RESULTS
#     if "eval_results" in st.session_state:

#         res = st.session_state.eval_results

#         col1, col2, col3 = st.columns(3)

#         col1.metric("Accuracy", f"{res['accuracy']*100:.2f}%")
#         col2.metric("Avg Latency", f"{res['avg_latency']:.2f}s")
#         col3.metric("Financial Score", f"{res['financial_score']:.2f}/5")

#         # OPTIONAL CHART
#         # df = pd.DataFrame({
#         #     "Metric": ["Accuracy", "Latency", "Financial Score"],
#         #     "Value": [
#         #         res["accuracy"] * 100,
#         #         res["avg_latency"],
#         #         res["financial_score"]
#         #     ]
#         # })

#         # st.bar_chart(df.set_index("Metric"))

#         import plotly.graph_objects as go

#         # =========================
#         # 🎯 ACCURACY CHART (GREEN)
#         # =========================
#         fig_acc = go.Figure(go.Bar(
#             x=["Accuracy"],
#             y=[res["accuracy"] * 100],
#             marker_color="green"
#         ))
#         fig_acc.update_layout(title="Accuracy (%)")

#         st.plotly_chart(fig_acc, use_container_width=True)

#         # =========================
#         # ⏱ LATENCY CHART (BLUE)
#         # =========================
#         fig_lat = go.Figure(go.Bar(
#             x=["Avg Latency"],
#             y=[res["avg_latency"]],
#             marker_color="blue"
#         ))
#         fig_lat.update_layout(title="Average Latency (sec)")

#         st.plotly_chart(fig_lat, use_container_width=True)

#         # =========================
#         # 🧠 FINANCIAL SCORE PIE (COLOR CODED)
#         # =========================

#         scores = res["financial_scores_list"]

#         # Count distribution
#         score_counts = {i: 0 for i in range(6)}  # 0–5

#         for s in scores:
#             score_counts[s] += 1

#         labels = [f"{k}/5" for k in score_counts.keys()]
#         values = list(score_counts.values())

#         # 🔥 COLOR MAP (important for your requirement)
#         color_map = [
#             "red",        # 0
#             "orange",     # 1
#             "yellow",     # 2
#             "lightgreen", # 3
#             "green",      # 4
#             "darkgreen"   # 5
#         ]

#         fig_pie = go.Figure(data=[go.Pie(
#             labels=labels,
#             values=values,
#             marker=dict(colors=color_map)
#         )])

#         fig_pie.update_layout(title="Financial Quality Score Distribution")

#         st.plotly_chart(fig_pie, use_container_width=True)

#     # =========================
#     # EXISTING LOGS
#     # =========================
#     st.divider()
#     st.subheader("🧠 Execution Logs")

#     logs = st.session_state.get("debug_logs", [])

#     if not logs:
#         st.info("No runs yet.")
#         return

#     for log in reversed(logs):

#         st.subheader(f"🕒 {log['timestamp']}")

#         st.markdown(f"**Query:** {log['query']}")
#         st.markdown(f"**Tickers:** {', '.join(log['tickers'])}")

#         st.markdown(f"**Agents Triggered:** {', '.join(log['routes'])}")

#         st.markdown(f"**⏱ Total Latency:** {log['latency_total']} sec")

#         render_graph(log["routes"])

#         st.divider()




# # =========================
# # ENTRY
# # =========================
# # if not st.session_state.logged_in:
# #     auth_screen()
# # else:
# #     main_chat_screen()

# if not st.session_state.logged_in:
#     auth_screen()
# else:
#     if st.session_state.page == "chat":
#         main_chat_screen()
#     elif st.session_state.page == "dashboard":
#         dashboard_screen()

import streamlit as st
import tempfile
import time
import yfinance as yf
import numpy as np
import pandas as pd
import plotly.express as px

from main import run_graph
from evaluation import evaluate_system
import db_manager as db

@st.cache_data
def run_eval_cached():
    return evaluate_system()


# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Fin-Agent AI Pro",
    layout="wide"
)

db.init_db()


# =========================
# SESSION STATE
# =========================
if "page" not in st.session_state:
    st.session_state.page = "chat"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

if "uploaded_files_list" not in st.session_state:
    st.session_state.uploaded_files_list = []

if "selected_files" not in st.session_state:
    st.session_state.selected_files = set()


# =========================
# SAFE CHARTS (FIXED)
# =========================
def plot_price_chart(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="6mo")

        if hist is None or hist.empty:
            st.warning(f"No price data for {ticker}")
            return

        fig = px.line(hist, x=hist.index, y="Close",
                      title=f"{ticker} Price Trend (6 Months)")

        st.plotly_chart(fig, width='stretch', key=f"price_{ticker}_{time.time()}")

    except Exception as e:
        st.error(f"{ticker} price chart failed: {e}")


def plot_risk_pie(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")

        if hist is None or hist.empty:
            st.warning(f"No risk data for {ticker}")
            return

        returns = hist["Close"].pct_change().dropna()

        if returns.empty:
            st.warning(f"Not enough data for {ticker}")
            return

        volatility = np.std(returns) * np.sqrt(252)

        risk_score = min(volatility * 100, 100)
        safe_score = 100 - risk_score

        df = pd.DataFrame({
            "Category": ["Safe", "Risk"],
            "Value": [safe_score, risk_score]
        })

        fig = px.pie(df, names="Category", values="Value",
                     title=f"{ticker} Risk Distribution")

        st.plotly_chart(fig, width='stretch', key=f"risk_{ticker}_{time.time()}")

    except Exception as e:
        st.error(f"{ticker} risk chart failed: {e}")


# =========================
# GRAPH VISUALIZATION
# =========================
import networkx as nx
import plotly.graph_objects as go

def render_graph(routes):
    G = nx.DiGraph()
    G.add_node("orchestrator")

    for r in routes:
        G.add_edge("orchestrator", r)

    pos = nx.spring_layout(G)

    edge_x, edge_y = [], []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(x=edge_x, y=edge_y, mode='lines')

    node_x, node_y, text = [], [], []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        text.append(node)

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=text,
        textposition="bottom center"
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    st.plotly_chart(fig, width='stretch')


# =========================
# AUTH SCREEN
# =========================
def auth_screen():
    # Initialize auth mode state
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "login"

    # Apply centered layout with custom CSS
    st.markdown("""
    <style>
        .centered-container {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        .auth-box {
            width: 100%;
            max-width: 400px;
            padding: 40px;
            border-radius: 10px;
        }
        .auth-title {
            text-align: center;
            margin-bottom: 30px;
        }
        .auth-input {
            margin-bottom: 20px;
        }
        .auth-button {
            width: 100%;
            margin-top: 10px;
            margin-bottom: 20px;
        }
        .toggle-text {
            text-align: center;
            margin-top: 30px;
            font-size: 14px;
        }
        .toggle-link {
            color: #FF6B6B;
            cursor: pointer;
            text-decoration: none;
            font-weight: 600;
        }
    </style>
    """, unsafe_allow_html=True)

    # Center the content
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # Title
        st.markdown("""
        <div class="auth-title">
            <h1>Fin-Agent AI</h1>
        </div>
        """, unsafe_allow_html=True)

        # LOGIN MODE
        if st.session_state.auth_mode == "login":
            st.markdown("<h2 style='text-align: center;'>Login</h2>", unsafe_allow_html=True)
            
            user = st.text_input("Username", key="login_user")
            pw = st.text_input("Password", type="password", key="login_pw")

            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                if st.button("Login", use_container_width=True, key="login_btn"):
                    if db.check_user(user, pw):
                        st.session_state.logged_in = True
                        st.session_state.username = user

                        chats = db.get_user_chats(user)
                        chat_id = chats[0][0] if chats else db.create_chat(user)

                        st.session_state.current_chat_id = chat_id
                        st.session_state.chat_history = db.get_chat_messages(chat_id)

                        st.rerun()
                    else:
                        st.error("Invalid credentials")
            
            with col_btn2:
                if st.button("Clear", use_container_width=True):
                    st.session_state.auth_mode = "login"
                    st.rerun()

            # Toggle to Sign Up
            st.markdown("""
            <div class="toggle-text">
                Don't have an account? <span class="toggle-link" onclick="window.location.reload();">Sign Up</span>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Create new account →", use_container_width=True, key="switch_to_signup"):
                st.session_state.auth_mode = "signup"
                st.rerun()

        # SIGNUP MODE
        elif st.session_state.auth_mode == "signup":
            st.markdown("<h2 style='text-align: center;'>Sign Up</h2>", unsafe_allow_html=True)
            
            new_user = st.text_input("Username", key="signup_user")
            new_pw = st.text_input("Password", type="password", key="signup_pw")
            confirm_pw = st.text_input("Confirm Password", type="password", key="confirm_pw")

            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                if st.button("Register", use_container_width=True, key="register_btn"):
                    if new_pw != confirm_pw:
                        st.error("Passwords do not match")
                    elif len(new_user) < 3:
                        st.error("Username must be at least 3 characters")
                    elif len(new_pw) < 6:
                        st.error("Password must be at least 6 characters")
                    elif db.add_user(new_user, new_pw):
                        st.success("Account created! Please login.")
                        st.session_state.auth_mode = "login"
                        st.rerun()
                    else:
                        st.error("Username already exists")
            
            with col_btn2:
                if st.button("Clear", use_container_width=True):
                    st.session_state.auth_mode = "signup"
                    st.rerun()

            # Toggle to Login
            if st.button("← Back to Login", use_container_width=True, key="switch_to_login"):
                st.session_state.auth_mode = "login"
                st.rerun()


# =========================
# MAIN CHAT UI
# =========================
def main_chat_screen():

    with st.sidebar:

        col1, col2 = st.columns([3, 2])

        with col1:
            st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=80)

        with col2:
            if st.button("Sign Out"):
                st.session_state.logged_in = False
                st.session_state.username = None
                st.session_state.chat_history = []
                st.session_state.current_chat_id = None
                st.rerun()

        st.markdown(f"### 👤 {st.session_state.username}")
        st.divider()

        col1, col2 = st.columns(2)

        with col1:
            if st.button("➕ New "):
                chat_id = db.create_chat(st.session_state.username)
                st.session_state.current_chat_id = chat_id
                st.session_state.chat_history = []
                st.rerun()

        with col2:
            if st.button("🧹 Clear"):
                st.session_state.chat_history = []
                st.rerun()

        st.divider()

        st.subheader("Previous Chats")

        chats = db.get_user_chats(st.session_state.username)

        for chat_id, title in chats:
            if st.button(f"🗂️ {title}", key=f"chat_{chat_id}"):
                st.session_state.current_chat_id = chat_id
                st.session_state.chat_history = db.get_chat_messages(chat_id)
                st.rerun()

        st.divider()

        # FILE UPLOAD WITH MULTIPLE FILES SUPPORT
        uploaded_files = st.file_uploader(
            "Upload PDF / TXT",
            type=["pdf", "txt"],
            accept_multiple_files=True
        )

        # ADD NEW FILES TO SESSION STATE
        if uploaded_files:
            for file in uploaded_files:
                # Check if file is not already in the list (by name)
                if not any(f["name"] == file.name for f in st.session_state.uploaded_files_list):
                    st.session_state.uploaded_files_list.append({
                        "name": file.name,
                        "data": file.getvalue()
                    })

        # DISPLAY UPLOADED FILES WITH CHECKBOXES
        if st.session_state.uploaded_files_list:
            for idx, file_info in enumerate(st.session_state.uploaded_files_list):
                col1, col2, col3 = st.columns([0.08, 0.72, 0.2])
                
                with col1:
                    # Checkbox for file selection (hidden label)
                    is_selected = st.checkbox(
                        label=" ",
                        value=idx in st.session_state.selected_files,
                        key=f"checkbox_{idx}_{file_info['name']}",
                        label_visibility="collapsed"
                    )
                    
                    if is_selected:
                        st.session_state.selected_files.add(idx)
                    else:
                        st.session_state.selected_files.discard(idx)
                
                with col2:
                    st.caption(f"📄 {file_info['name']}")
                
                with col3:
                    if st.button("❌", key=f"delete_{idx}_{file_info['name']}"):
                        st.session_state.uploaded_files_list.pop(idx)
                        st.session_state.selected_files.discard(idx)
                        st.rerun()
            
            # Show selection summary
            if st.session_state.selected_files:
                selected_count = len(st.session_state.selected_files)
                st.success(f"✅ {selected_count} file(s) selected for analysis")
            else:
                st.warning("⚠️ No files selected. Check the checkboxes to use files for RAG analysis")

    col1, col2 = st.columns([8, 2])

    with col1:
        st.title("Financial Multi-Agent Analyst")

    with col2:
        if st.button("Check Dashboard"):
            st.session_state.page = "dashboard"
            st.rerun()

    # CHAT HISTORY
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

            if "charts" in msg:
                tickers = msg["charts"]["tickers"]
                routes = msg["charts"]["routes"]

                if "financial" in routes:
                    st.subheader("📈 Price Trend")
                    for ticker in tickers:
                        plot_price_chart(ticker)

                if "risk" in routes:
                    st.subheader("⚠️ Risk Analysis")
                    for ticker in tickers:
                        plot_risk_pie(ticker)

    # INPUT
    if prompt := st.chat_input("Ask about any stock..."):

        st.session_state.chat_history.append({"role": "user", "content": prompt})

        db.save_message(st.session_state.current_chat_id, "user", prompt)

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):

                doc_paths = []
                
                # PROCESS SELECTED FILES ONLY
                if st.session_state.selected_files and st.session_state.uploaded_files_list:
                    for idx in sorted(st.session_state.selected_files):
                        if idx < len(st.session_state.uploaded_files_list):
                            file_info = st.session_state.uploaded_files_list[idx]
                            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_info['name'].split('.')[-1]}") as tmp:
                                tmp.write(file_info["data"])
                                doc_paths.append(tmp.name)
                
                # CONVERT LIST TO COMMA-SEPARATED STRING FOR FUNCTION
                doc_path = ",".join(doc_paths) if doc_paths else ""

                result, debug_data = run_graph(prompt, doc_path)

                if "debug_logs" not in st.session_state:
                    st.session_state.debug_logs = []

                st.session_state.debug_logs.append(debug_data)

                outputs = result.get("outputs", [])
                formatted_outputs = []

                for o in outputs:
                    content = o if isinstance(o, str) else getattr(o, "content", str(o))

                    cleaned = "\n".join([
                        line for line in content.split("\n")
                        if not line.strip().startswith(("Thought:", "Action:", "Observation:"))
                    ]).strip()

                    if cleaned:
                        formatted_outputs.append(cleaned)

                full_response = "\n\n".join(formatted_outputs)
                st.markdown(full_response)

                routes = debug_data.get("routes", [])
                tickers = debug_data.get("tickers", [])

                if "rag" not in routes:

                    if "financial" in routes:
                        st.subheader("📈 Price Trend")
                        for ticker in tickers:
                            plot_price_chart(ticker)

                    if "risk" in routes:
                        st.subheader("⚠️ Risk Analysis")
                        for ticker in tickers:
                            plot_risk_pie(ticker)

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": full_response,
                    "charts": {"tickers": tickers, "routes": routes}
                })

                db.save_message(
                    st.session_state.current_chat_id,
                    "assistant",
                    full_response,
                    charts={"tickers": tickers, "routes": routes}
                )

                if len(st.session_state.chat_history) == 2:
                    db.update_chat_title(
                        st.session_state.current_chat_id,
                        prompt[:40]
                    )


# =========================
# DASHBOARD (RESTORED)
# =========================

def dashboard_screen():

    st.title("Multi-Agent Execution Dashboard")

    if st.button("⬅ Back to Chat"):
        st.session_state.page = "chat"
        st.rerun()

    # =========================
    # 🔥 NEW: EVALUATION SECTION
    # =========================
    st.divider()
    st.subheader("System Benchmarking")

    if st.button("Run Evaluation Benchmark"):

        with st.spinner("Running evaluation on dataset..."):

            results = run_eval_cached()

            st.session_state.eval_results = results

    # SHOW RESULTS
    if "eval_results" in st.session_state:

        res = st.session_state.eval_results

        col1, col2, col3 = st.columns(3)

        col1.metric("Accuracy", f"{res['accuracy']*100:.2f}%")
        col2.metric("Avg Latency", f"{res['avg_latency']:.2f}s")
        col3.metric("Financial Score", f"{res['financial_score']:.2f}/5")

        # OPTIONAL CHART
        # df = pd.DataFrame({
        #     "Metric": ["Accuracy", "Latency", "Financial Score"],
        #     "Value": [
        #         res["accuracy"] * 100,
        #         res["avg_latency"],
        #         res["financial_score"]
        #     ]
        # })

        # st.bar_chart(df.set_index("Metric"))

        import plotly.graph_objects as go

        # # =========================
        # # 🎯 ACCURACY CHART (GREEN)
        # # =========================
        # fig_acc = go.Figure(go.Bar(
        #     x=["Accuracy"],
        #     y=[res["accuracy"] * 100],
        #     marker_color="green"
        # ))
        # fig_acc.update_layout(title="Accuracy (%)")

        # st.plotly_chart(fig_acc, use_container_width=True)

        accuracy_list = res.get("accuracy_list", [])

        if accuracy_list:
            df_acc = pd.DataFrame({
                "Question": range(1, len(accuracy_list) + 1),
                "Accuracy": [x * 100 for x in accuracy_list]
            })

            fig_acc = px.line(
                df_acc,
                x="Question",
                y="Accuracy",
                markers=True,
                title="Accuracy per Question (%)"
            )

            st.plotly_chart(fig_acc, use_container_width=True)

        # =========================
        # ⏱ LATENCY CHART (BLUE)
        # =========================
        # fig_lat = go.Figure(go.Bar(
        #     x=["Avg Latency"],
        #     y=[res["avg_latency"]],
        #     marker_color="blue"
        # ))
        # fig_lat.update_layout(title="Average Latency (sec)")

        # st.plotly_chart(fig_lat, use_container_width=True)

        latency_list = res.get("latencies", [])

        if latency_list:
            df_lat = pd.DataFrame({
                "Question": range(1, len(latency_list) + 1),
                "Latency": latency_list
            })

            fig_lat = px.line(
                df_lat,
                x="Question",
                y="Latency",
                markers=True,
                title="Latency per Question (sec)"
            )

            st.plotly_chart(fig_lat, use_container_width=True)

        # =========================
        # 🧠 FINANCIAL SCORE PIE (COLOR CODED)
        # =========================

        scores = res["financial_scores_list"]

        # Count distribution
        score_counts = {i: 0 for i in range(6)}  # 0–5

        for s in scores:
            score_counts[s] += 1

        labels = [f"{k}/5" for k in score_counts.keys()]
        values = list(score_counts.values())

        # 🔥 COLOR MAP (important for your requirement)
        color_map = [
            "red",        # 0
            "orange",     # 1
            "yellow",     # 2
            "lightgreen", # 3
            "green",      # 4
            "darkgreen"   # 5
        ]

        fig_pie = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            marker=dict(colors=color_map)
        )])

        fig_pie.update_layout(title="Financial Quality Score Distribution")

        st.plotly_chart(fig_pie, use_container_width=True)

    # =========================
    # EXISTING LOGS
    # =========================
    st.divider()
    st.subheader("Execution Logs")

    logs = st.session_state.get("debug_logs", [])

    if not logs:
        st.info("No runs yet.")
        return

    for log in reversed(logs):

        st.subheader(f"🕒 {log['timestamp']}")

        st.markdown(f"**Query:** {log['query']}")
        st.markdown(f"**Tickers:** {', '.join(log['tickers'])}")

        st.markdown(f"**Agents Triggered:** {', '.join(log['routes'])}")

        st.markdown(f"**⏱ Total Latency:** {log['latency_total']} sec")

        render_graph(log["routes"])

        st.divider()



# =========================
# ENTRY
# =========================
if not st.session_state.logged_in:
    auth_screen()
else:
    if st.session_state.page == "chat":
        main_chat_screen()
    elif st.session_state.page == "dashboard":
        dashboard_screen()
