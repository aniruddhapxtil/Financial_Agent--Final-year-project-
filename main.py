

# import os
# import time
# import re
# from typing import TypedDict, List, Annotated
# from dotenv import load_dotenv

# os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"

# from crewai import Agent, Task, Crew, Process, LLM
# from langgraph.graph import StateGraph, END, add_messages
# from rapidfuzz import fuzz
# from langsmith import traceable

# from langchain_community.document_loaders import PyPDFLoader, TextLoader
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_community.vectorstores import FAISS
# from langchain_community.embeddings import HuggingFaceEmbeddings

# from tools import (
#     fetch_stock_data,
#     fetch_news_and_sentiment,
#     fetch_risk_metrics
# )

# # =========================
# # Environment
# # =========================
# load_dotenv()

# # =========================
# # LLM
# # =========================
# llm = LLM(
#     model="meta/llama3-8b-instruct",
#     api_key=os.getenv("NVIDIA_API_KEY"),
#     base_url="https://integrate.api.nvidia.com/v1",
#     provider="openai",
#     temperature=0,
#     max_tokens=300
# )

# # =========================
# # AUTO TICKER DETECTION
# # =========================
# COMPANY_TICKER_MAP = {
#     "nvidia": "NVDA",
#     "apple": "AAPL",
#     "microsoft": "MSFT",
#     "google": "GOOGL",
#     "alphabet": "GOOGL",
#     "amazon": "AMZN",
#     "tesla": "TSLA",
#     "meta": "META",
#     "facebook": "META",
#     "netflix": "NFLX",
#     "amd": "AMD",
#     "intel": "INTC"
# }

# def extract_ticker_from_query(query: str):
#     query_lower = query.lower()
#     for company, ticker in COMPANY_TICKER_MAP.items():
#         pattern = r"\b" + re.escape(company) + r"\b"
#         if re.search(pattern, query_lower):
#             return ticker
#     ticker_pattern = re.findall(r"\b[A-Z]{2,5}\b", query)
#     if ticker_pattern:
#         return ticker_pattern[0]
#     return None

# # =========================
# # Agents
# # =========================
# fin_analyst = Agent(
#     role="Senior Financial Analyst",
#     goal="Analyze {ticker} financial health",
#     backstory="Expert in valuation and fundamentals",
#     tools=[fetch_stock_data],
#     llm=llm,
#     allow_delegation=False
# )

# news_analyst = Agent(
#     role="News & Sentiment Analyst",
#     goal="Analyze ONLY three structured headlines for {ticker}",
#     backstory="Tracks market-moving headlines concisely",
#     tools=[fetch_news_and_sentiment],
#     llm=llm,
#     allow_delegation=False
# )

# risk_analyst = Agent(
#     role="Risk Analyst",
#     goal="Assess market risk for {ticker}",
#     backstory="Quantitative risk specialist",
#     tools=[fetch_risk_metrics],
#     llm=llm,
#     allow_delegation=False
# )

# rag_agent = Agent(
#     role="Document Intelligence Agent",
#     goal="Answer strictly from uploaded documents",
#     backstory="Expert at document analysis",
#     llm=llm,
#     allow_delegation=False
# )

# # =========================
# # Tasks
# # =========================
# financial_task = Task(
#     description="""
# Analyze financial health of {ticker} using ONLY tool data.

# STRICT FORMAT:

# 1. Current Price:
# 2. Market Cap:
# 3. P/E Ratio:
# 4. Revenue Growth (%):
# 5. EBITDA Margin (%):

# Then provide:
# - Valuation Interpretation
# - Growth Interpretation
# - Profitability Interpretation

# IMPORTANT:
# - Use exact numeric values from tool.
# - Do NOT hallucinate.
# - Keep output under 250 words.
# - End with:
#   Source: Yahoo Finance (via yfinance)
# """,
#     expected_output="Structured financial report",
#     agent=fin_analyst
# )

# news_task = Task(
#     description="""
# Using ONLY structured tool output:

# Return EXACTLY 3 headlines.

# FORMAT:

# 1. Title:
#    Source:
#    Published Date:

# 2. Title:
#    Source:
#    Published Date:

# 3. Title:
#    Source:
#    Published Date:

# Then:
# Overall Sentiment: (Positive / Neutral / Negative)

# IMPORTANT:
# - Do NOT summarize.
# - Do NOT rewrite.
# - Keep under 200 words.
# """,
#     expected_output="Structured news report",
#     agent=news_analyst
# )

# risk_task = Task(
#     description="""
# Analyze risk metrics for {ticker} using tool data only.

# Provide:
# - Beta
# - Volatility
# - Key Risk Observations

# Keep under 200 words.
# """,
#     expected_output="Risk analysis",
#     agent=risk_analyst
# )

# # =========================
# # Crews
# # =========================
# financial_crew = Crew(
#     agents=[fin_analyst],
#     tasks=[financial_task],
#     process=Process.sequential
# )

# news_crew = Crew(
#     agents=[news_analyst],
#     tasks=[news_task],
#     process=Process.sequential
# )

# risk_crew = Crew(
#     agents=[risk_analyst],
#     tasks=[risk_task],
#     process=Process.sequential
# )

# # =========================
# # Graph State
# # =========================
# class GraphState(TypedDict):
#     query: str
#     ticker: str
#     doc_path: str
#     routes: List[str]
#     outputs: Annotated[List[str], add_messages]

# # =========================
# # Intent Detection
# # =========================
# def fuzzy_contains(query: str, keywords: list) -> bool:
#     return any(fuzz.partial_ratio(query, kw) > 70 for kw in keywords)

# financial_keywords = ["financial", "valuation", "revenue", "growth", "fundamental"]
# news_keywords = ["news", "sentiment", "headline"]
# risk_keywords = ["risk", "volatility", "beta"]

# # =========================
# # Orchestrator
# # =========================
# @traceable(name="Orchestrator")
# def orchestrator_node(state: GraphState):
#     q = state["query"].lower()
#     routes = []

#     if state["doc_path"]:
#         routes.append("rag")
#     if fuzzy_contains(q, financial_keywords):
#         routes.append("financial")
#     if fuzzy_contains(q, news_keywords):
#         routes.append("news")
#     if fuzzy_contains(q, risk_keywords):
#         routes.append("risk")
#     if not routes:
#         routes = ["financial", "news", "risk"]
#     return {"routes": routes}

# # =========================
# # Vector Cache
# # =========================
# vectorstore_cache = {}

# # =========================
# # Agent Nodes
# # =========================
# @traceable(name="Financial Agent")
# def financial_node(state: GraphState):
#     start = time.time()
#     result = financial_crew.kickoff(inputs={"ticker": state["ticker"]})
#     latency = round(time.time() - start, 2)
#     return {"outputs": [f"📊 FINANCIAL ANALYSIS (Latency: {latency}s)\n{result}"]}

# @traceable(name="News Agent")
# def news_node(state: GraphState):
#     start = time.time()
#     result = news_crew.kickoff(inputs={"ticker": state["ticker"]})
#     latency = round(time.time() - start, 2)
#     return {"outputs": [f"📰 NEWS & SENTIMENT (Latency: {latency}s)\n{result}"]}

# @traceable(name="Risk Agent")
# def risk_node(state: GraphState):
#     start = time.time()
#     result = risk_crew.kickoff(inputs={"ticker": state["ticker"]})
#     latency = round(time.time() - start, 2)
#     return {"outputs": [f"⚠️ RISK ASSESSMENT (Latency: {latency}s)\n{result}"]}

# @traceable(name="RAG Agent")
# def rag_node(state: GraphState):
#     start = time.time()
#     loader = PyPDFLoader(state["doc_path"]) if state["doc_path"].endswith(".pdf") else TextLoader(state["doc_path"])
#     docs = loader.load()
#     splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=80)
#     chunks = splitter.split_documents(docs)

#     if state["doc_path"] in vectorstore_cache:
#         vectorstore = vectorstore_cache[state["doc_path"]]
#     else:
#         embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
#         vectorstore = FAISS.from_documents(chunks, embeddings)
#         vectorstore_cache[state["doc_path"]] = vectorstore

#     retriever = vectorstore.as_retriever(search_kwargs={"k": 2})
#     retrieved_docs = retriever.invoke(state["query"])
#     context = "\n\n".join(d.page_content[:800] for d in retrieved_docs)

#     prompt = f"""
# Answer ONLY using context below.

# Context:
# {context}

# Question:
# {state['query']}

# Keep answer under 200 words.
# """
#     answer = rag_agent.llm.call(prompt)
#     latency = round(time.time() - start, 2)
#     return {"outputs": [f"📄 DOCUMENT INSIGHTS (Latency: {latency}s)\n{answer.strip()}"]}

# # =========================
# # Build a fresh workflow per query
# # =========================
# def build_workflow():
#     workflow = StateGraph(GraphState)
#     workflow.add_node("orchestrator", orchestrator_node)
#     workflow.add_node("financial", financial_node)
#     workflow.add_node("news", news_node)
#     workflow.add_node("risk", risk_node)
#     workflow.add_node("rag", rag_node)
#     workflow.set_entry_point("orchestrator")
#     workflow.add_conditional_edges("orchestrator", lambda s: s["routes"])
#     workflow.add_edge("financial", END)
#     workflow.add_edge("news", END)
#     workflow.add_edge("risk", END)
#     workflow.add_edge("rag", END)
#     return workflow.compile()

# # =========================
# # Runner
# # =========================
# def run_graph(query, doc_path=""):

#     ticker = extract_ticker_from_query(query)
#     if not ticker and not doc_path:
#         return {"outputs": ["❌ Could not detect company. Please mention company like Nvidia, Apple, Tesla, etc."]}

#     # Create fresh Crew objects each time
#     financial_crew = Crew(
#         agents=[fin_analyst],
#         tasks=[financial_task],
#         process=Process.sequential
#     )
#     news_crew = Crew(
#         agents=[news_analyst],
#         tasks=[news_task],
#         process=Process.sequential
#     )
#     risk_crew = Crew(
#         agents=[risk_analyst],
#         tasks=[risk_task],
#         process=Process.sequential
#     )

#     workflow_app = build_workflow()  # fresh workflow
#     state: GraphState = {
#         "query": query.strip(),
#         "ticker": ticker,
#         "doc_path": doc_path,
#         "routes": [],
#         "outputs": []
#     }

#     result = workflow_app.invoke(state)
#     return result

#patils repo code...

# import os
# import time
# from typing import TypedDict, List, Annotated
# from dotenv import load_dotenv

# os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"

# from crewai import Agent, Task, Crew, Process, LLM
# from langgraph.graph import StateGraph, END, add_messages
# from rapidfuzz import fuzz
# from langsmith import traceable

# import re

# # =========================
# # Automatic Ticker Detection
# # =========================
# def extract_ticker(query: str) -> str:
#     query_lower = query.lower()

#     company_map = {
#         "nvidia": "NVDA",
#         "apple": "AAPL",
#         "tesla": "TSLA",
#         "microsoft": "MSFT",
#         "amazon": "AMZN",
#         "google": "GOOGL",
#         "meta": "META"
#     }

#     # Check company names
#     for company, ticker in company_map.items():
#         if company in query_lower:
#             return ticker

#     # Check direct ticker symbols (like NVDA, TSLA)
#     match = re.search(r"\b[A-Z]{2,5}\b", query)
#     if match:
#         return match.group()

#     # Default fallback
#     return "NVDA"

# # Import tools from your tools.py
# from tools import (
#     fetch_stock_data,
#     fetch_news_and_sentiment,
#     fetch_risk_metrics,
#     read_uploaded_document
# )

# load_dotenv()

# # =========================
# # LLM Configuration (FIXED FOR NVIDIA NIM)
# # =========================
# llm = LLM(
#     model="meta/llama3-70b-instruct",
#     api_key=os.getenv("NVIDIA_API_KEY"),
#     base_url="https://integrate.api.nvidia.com/v1",
#     provider="openai",
#     temperature=0,
#     max_tokens=1024
# )

# # =========================
# # Agents
# # =========================
# fin_analyst = Agent(
#     role="Senior Financial Analyst",
#     goal="Analyze {ticker} financial health using tool data",
#     backstory="Expert in valuation and fundamental analysis. You use precise numbers.",
#     tools=[fetch_stock_data],
#     llm=llm
# )

# news_analyst = Agent(
#     role="News & Sentiment Analyst",
#     goal="Extract sentiment from the latest news for {ticker}",
#     backstory="You track market-moving headlines and summarize their impact.",
#     tools=[fetch_news_and_sentiment],
#     llm=llm
# )

# risk_analyst = Agent(
#     role="Risk Analyst",
#     goal="Assess quantitative market risk for {ticker}",
#     backstory="Specialist in volatility and market correlations.",
#     tools=[fetch_risk_metrics],
#     llm=llm
# )

# rag_agent = Agent(
#     role="Document Intelligence Agent",
#     goal="Answer questions strictly based on the provided file path: {doc_path}",
#     backstory="Expert at parsing and summarizing uploaded financial reports.",
#     tools=[read_uploaded_document],
#     llm=llm
# )

# performance_agent = Agent(
#     role="Performance Evaluation Agent",
#     goal="Evaluate quality and accuracy of the reports generated",
#     backstory="An auditor who ensures LLM outputs are helpful and non-hallucinatory.",
#     llm=llm
# )

# # =========================
# # Graph State
# # =========================
# class GraphState(TypedDict):
#     query: str
#     ticker: str
#     doc_path: str
#     routes: List[str]
#     outputs: Annotated[List[str], add_messages]

# # =========================
# # Intent Detection Logic
# # =========================
# def fuzzy_contains(query: str, keywords: list) -> bool:
#     return any(fuzz.partial_ratio(query.lower(), kw) > 70 for kw in keywords)

# financial_keywords = ["financial", "valuation", "revenue", "growth", "price", "pe ratio"]
# news_keywords = ["news", "sentiment", "headline", "latest"]
# risk_keywords = ["risk", "volatility", "beta", "drawdown"]

# # =========================
# # Orchestrator Node
# # =========================
# def orchestrator_node(state: GraphState):
#     q = state["query"].lower()
#     routes = []

#     if state.get("doc_path"):
#         routes.append("rag")
#     if fuzzy_contains(q, financial_keywords):
#         routes.append("financial")
#     if fuzzy_contains(q, news_keywords):
#         routes.append("news")
#     if fuzzy_contains(q, risk_keywords):
#         routes.append("risk")

#     if not routes:
#         routes = ["financial", "news", "risk"]

#     return {"routes": routes}

# # =========================
# # Agent Nodes
# # =========================
# @traceable(name="Financial Node")
# def financial_node(state: GraphState):
#     start = time.time()
#     task = Task(
#         description="Provide a structured financial report for {ticker}. Focus on Price, Market Cap, and P/E.",
#         expected_output="A clean numeric summary of financial health.",
#         agent=fin_analyst
#     )
#     crew = Crew(agents=[fin_analyst], tasks=[task], process=Process.sequential)
#     result = crew.kickoff(inputs={"ticker": state["ticker"]})
#     return {"outputs": [f"📊 FINANCIAL ANALYSIS (Latency: {round(time.time()-start,2)}s)\n{result}"]}

# @traceable(name="News Node")
# def news_node(state: GraphState):
#     start = time.time()
#     task = Task(
#         description="Analyze sentiment for {ticker} using latest headlines.",
#         expected_output="Summary of the top 3 news stories and overall sentiment.",
#         agent=news_analyst
#     )
#     crew = Crew(agents=[news_analyst], tasks=[task], process=Process.sequential)
#     result = crew.kickoff(inputs={"ticker": state["ticker"]})
#     return {"outputs": [f"📰 NEWS & SENTIMENT (Latency: {round(time.time()-start,2)}s)\n{result}"]}

# @traceable(name="Risk Node")
# def risk_node(state: GraphState):
#     start = time.time()
#     task = Task(
#         description="Calculate and interpret risk metrics for {ticker}.",
#         expected_output="Risk assessment including Beta and Volatility.",
#         agent=risk_analyst
#     )
#     crew = Crew(agents=[risk_analyst], tasks=[task], process=Process.sequential)
#     result = crew.kickoff(inputs={"ticker": state["ticker"]})
#     return {"outputs": [f"⚠️ RISK ASSESSMENT (Latency: {round(time.time()-start,2)}s)\n{result}"]}

# @traceable(name="RAG Node")
# def rag_node(state: GraphState):
#     start = time.time()
#     task = Task(
#         description=f"Using the tool, read the file at {state['doc_path']} and answer: {state['query']}",
#         expected_output="Answer derived only from the document context.",
#         agent=rag_agent
#     )
#     crew = Crew(agents=[rag_agent], tasks=[task], process=Process.sequential)
#     result = crew.kickoff()
#     return {"outputs": [f"📄 DOCUMENT INSIGHTS (Latency: {round(time.time()-start,2)}s)\n{result}"]}

# @traceable(name="Performance Node")
# def performance_node(state: GraphState):
#     combined_output = "\n\n".join([str(o.content if hasattr(o, 'content') else o) for o in state["outputs"]])
#     eval_prompt = f"Evaluate these agent outputs for accuracy and clarity:\n\n{combined_output}\n\nReturn a Score Table (0-10) and a summary."
#     evaluation = performance_agent.llm.call(eval_prompt)
#     return {"outputs": [f"📈 PERFORMANCE EVALUATION\n{evaluation}"]}

# # =========================
# # Build Workflow
# # =========================
# workflow = StateGraph(GraphState)

# workflow.add_node("orchestrator", orchestrator_node)
# workflow.add_node("financial", financial_node)
# workflow.add_node("news", news_node)
# workflow.add_node("risk", risk_node)
# workflow.add_node("rag", rag_node)
# workflow.add_node("performance", performance_node)

# workflow.set_entry_point("orchestrator")
# workflow.add_conditional_edges("orchestrator", lambda s: s["routes"])

# workflow.add_edge("financial", "performance")
# workflow.add_edge("news", "performance")
# workflow.add_edge("risk", "performance")
# workflow.add_edge("rag", "performance")
# workflow.add_edge("performance", END)

# app = workflow.compile()

# def run_graph(query, doc_path):

#     ticker = extract_ticker(query)

#     state: GraphState = {
#         "query": query,
#         "ticker": ticker,
#         "doc_path": doc_path,
#         "routes": [],
#         "outputs": []
#     }

#     return app.invoke(state)


#new code withour perfroamcen agent
import os
import time
from typing import TypedDict, List, Annotated
from dotenv import load_dotenv

os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"

from crewai import Agent, Task, Crew, Process, LLM
from langgraph.graph import StateGraph, END, add_messages
from rapidfuzz import fuzz
from langsmith import traceable

import re

# =========================
# Automatic Ticker Detection
# =========================
def extract_ticker(query: str) -> str:
    query_lower = query.lower()

    company_map = {
        "nvidia": "NVDA",
        "apple": "AAPL",
        "tesla": "TSLA",
        "microsoft": "MSFT",
        "amazon": "AMZN",
        "google": "GOOGL",
        "meta": "META"
    }

    for company, ticker in company_map.items():
        if company in query_lower:
            return ticker

    match = re.search(r"\b[A-Z]{2,5}\b", query)
    if match:
        return match.group()

    return "NVDA"


# Import tools
from tools import (
    fetch_stock_data,
    fetch_news_and_sentiment,
    fetch_risk_metrics,
    read_uploaded_document
)

load_dotenv()

# =========================
# LLM Configuration
# =========================
llm = LLM(
    model="meta/llama3-70b-instruct",
    api_key=os.getenv("NVIDIA_API_KEY"),
    base_url="https://integrate.api.nvidia.com/v1",
    provider="openai",
    temperature=0,
    max_tokens=512
)

# =========================
# Agents
# =========================
fin_analyst = Agent(
    role="Senior Financial Analyst",
    goal="Analyze {ticker} financial health using tool data",
    backstory="Expert in valuation and fundamental analysis. You use precise numbers.",
    tools=[fetch_stock_data],
    llm=llm
)

news_analyst = Agent(
    role="News & Sentiment Analyst",
    goal="Extract sentiment from the latest news for {ticker}",
    backstory="You track market-moving headlines and summarize their impact.",
    tools=[fetch_news_and_sentiment],
    llm=llm
)

risk_analyst = Agent(
    role="Risk Analyst",
    goal="Assess quantitative market risk for {ticker}",
    backstory="Specialist in volatility and market correlations.",
    tools=[fetch_risk_metrics],
    llm=llm
)

rag_agent = Agent(
    role="Document Intelligence Agent",
    goal="Answer questions strictly based on the provided file path: {doc_path}",
    backstory="Expert at parsing and summarizing uploaded financial reports.",
    tools=[read_uploaded_document],
    llm=llm
)

# =========================
# Graph State
# =========================
class GraphState(TypedDict):
    query: str
    ticker: str
    doc_path: str
    routes: List[str]
    outputs: Annotated[List[str], add_messages]

# =========================
# Intent Detection Logic
# =========================
def fuzzy_contains(query: str, keywords: list) -> bool:
    return any(fuzz.partial_ratio(query.lower(), kw) > 70 for kw in keywords)

financial_keywords = ["financial", "valuation", "revenue", "growth", "price", "pe ratio"]
news_keywords = ["news", "sentiment", "headline", "latest"]
risk_keywords = ["risk", "volatility", "beta", "drawdown"]

# =========================
# Orchestrator Node
# =========================
def orchestrator_node(state: GraphState):
    q = state["query"].lower()
    routes = []

    if state.get("doc_path"):
        routes.append("rag")
    if fuzzy_contains(q, financial_keywords):
        routes.append("financial")
    if fuzzy_contains(q, news_keywords):
        routes.append("news")
    if fuzzy_contains(q, risk_keywords):
        routes.append("risk")

    if not routes:
        routes = ["financial", "news", "risk"]

    return {"routes": routes}

# =========================
# Agent Nodes
# =========================
@traceable(name="Financial Node")
def financial_node(state: GraphState):
    start = time.time()
    task = Task(
        description="Provide a structured financial report for {ticker}. Focus on Price, Market Cap, and P/E.",
        expected_output="A clean numeric summary of financial health.",
        agent=fin_analyst
    )
    crew = Crew(agents=[fin_analyst], tasks=[task], process=Process.sequential)
    result = crew.kickoff(inputs={"ticker": state["ticker"]})
    return {"outputs": [f"📊 FINANCIAL ANALYSIS (Latency: {round(time.time()-start,2)}s)\n{result}"]}

@traceable(name="News Node")
def news_node(state: GraphState):
    start = time.time()
    task = Task(
        description="Analyze sentiment for {ticker} using latest headlines.",
        expected_output="Summary of the top 3 news stories and overall sentiment.",
        agent=news_analyst
    )
    crew = Crew(agents=[news_analyst], tasks=[task], process=Process.sequential)
    result = crew.kickoff(inputs={"ticker": state["ticker"]})
    return {"outputs": [f"📰 NEWS & SENTIMENT (Latency: {round(time.time()-start,2)}s)\n{result}"]}

@traceable(name="Risk Node")
def risk_node(state: GraphState):
    start = time.time()
    task = Task(
        description="Calculate and interpret risk metrics for {ticker}.",
        expected_output="Risk assessment including Beta and Volatility.",
        agent=risk_analyst
    )
    crew = Crew(agents=[risk_analyst], tasks=[task], process=Process.sequential)
    result = crew.kickoff(inputs={"ticker": state["ticker"]})
    return {"outputs": [f"⚠️ RISK ASSESSMENT (Latency: {round(time.time()-start,2)}s)\n{result}"]}

@traceable(name="RAG Node")
def rag_node(state: GraphState):
    start = time.time()
    task = Task(
        description=f"Using the tool, read the file at {state['doc_path']} and answer: {state['query']}",
        expected_output="Answer derived only from the document context.",
        agent=rag_agent
    )
    crew = Crew(agents=[rag_agent], tasks=[task], process=Process.sequential)
    result = crew.kickoff()
    return {"outputs": [f"📄 DOCUMENT INSIGHTS (Latency: {round(time.time()-start,2)}s)\n{result}"]}

# =========================
# Build Workflow
# =========================
workflow = StateGraph(GraphState)

workflow.add_node("orchestrator", orchestrator_node)
workflow.add_node("financial", financial_node)
workflow.add_node("news", news_node)
workflow.add_node("risk", risk_node)
workflow.add_node("rag", rag_node)

workflow.set_entry_point("orchestrator")
workflow.add_conditional_edges("orchestrator", lambda s: s["routes"])

workflow.add_edge("financial", END)
workflow.add_edge("news", END)
workflow.add_edge("risk", END)
workflow.add_edge("rag", END)

app = workflow.compile()

def run_graph(query, doc_path):

    ticker = extract_ticker(query)

    state: GraphState = {
        "query": query,
        "ticker": ticker,
        "doc_path": doc_path,
        "routes": [],
        "outputs": []
    }

    return app.invoke(state)