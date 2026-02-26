import os
import time
from typing import TypedDict, List, Annotated
from dotenv import load_dotenv

from crewai import Agent, Task, Crew, Process, LLM
from langgraph.graph import StateGraph, END, add_messages
from rapidfuzz import fuzz
from langsmith import traceable

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

from tools import (
    fetch_stock_data,
    fetch_news_and_sentiment,
    fetch_risk_metrics
)

# =========================
# Environment
# =========================
load_dotenv()

# =========================
# LLM (NVIDIA NIM)
# =========================
llm = LLM(
    model="meta/llama3-70b-instruct",
    api_key=os.getenv("NVIDIA_API_KEY"),
    base_url="https://integrate.api.nvidia.com/v1",
    provider="openai",
    temperature=0,
    max_tokens=1024
)

# =========================
# Agents
# =========================
fin_analyst = Agent(
    role="Senior Financial Analyst",
    goal="Analyze {ticker} financial health",
    backstory="Expert in valuation and fundamentals",
    tools=[fetch_stock_data],
    llm=llm,
    allow_delegation=False
)

news_analyst = Agent(
    role="News & Sentiment Analyst",
    goal="Analyze latest news for {ticker}",
    backstory="Tracks market-moving headlines",
    tools=[fetch_news_and_sentiment],
    llm=llm,
    allow_delegation=False
)

risk_analyst = Agent(
    role="Risk Analyst",
    goal="Assess market risk for {ticker}",
    backstory="Quantitative risk specialist",
    tools=[fetch_risk_metrics],
    llm=llm,
    allow_delegation=False
)

rag_agent = Agent(
    role="Document Intelligence Agent",
    goal="Answer strictly from uploaded documents",
    backstory="Expert at document analysis",
    llm=llm,
    allow_delegation=False
)

performance_agent = Agent(
    role="Performance Evaluation Agent",
    goal="Evaluate quality of agent outputs",
    backstory="Expert in LLM evaluation metrics",
    llm=llm,
    allow_delegation=False
)

# =========================
# Tasks
# =========================
financial_task = Task(
    description="""
    Analyze valuation and growth for {ticker}.

    IMPORTANT:
    - Clearly mention all metrics used.
    - At the end, include a section:
      "Source: Yahoo Finance (via yfinance)"
    """,
    expected_output="Financial analysis with source citation",
    agent=fin_analyst
)


news_task = Task(
    description="""
    Analyze news sentiment for {ticker}.

    IMPORTANT:
    - For each headline, mention:
        Title
        Source
        Published Date
    - Provide overall sentiment summary.
    """,
    expected_output="News sentiment report with citations",
    agent=news_analyst
)

risk_task = Task(
    description="Analyze risk metrics for {ticker}",
    expected_output="Risk analysis",
    agent=risk_analyst
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
# Intent Detection
# =========================
def fuzzy_contains(query: str, keywords: list) -> bool:
    return any(fuzz.partial_ratio(query, kw) > 70 for kw in keywords)

financial_keywords = ["financial", "valuation", "revenue", "growth"]
news_keywords = ["news", "sentiment", "headline"]
risk_keywords = ["risk", "volatility", "beta"]

# =========================
# Orchestrator
# =========================
@traceable(name="Orchestrator")
def orchestrator_node(state: GraphState):
    q = state["query"].lower()
    routes = []

    if state["doc_path"]:
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
# Agent Nodes (with Latency)
# =========================
@traceable(name="Financial Agent")
def financial_node(state: GraphState):
    start = time.time()
    crew = Crew(agents=[fin_analyst], tasks=[financial_task], process=Process.sequential)
    result = crew.kickoff(inputs={"ticker": state["ticker"]})
    latency = round(time.time() - start, 2)
    return {"outputs": [f"📊 FINANCIAL ANALYSIS (Latency: {latency}s)\n{result}"]}


@traceable(name="News Agent")
def news_node(state: GraphState):
    start = time.time()
    crew = Crew(agents=[news_analyst], tasks=[news_task], process=Process.sequential)
    result = crew.kickoff(inputs={"ticker": state["ticker"]})
    latency = round(time.time() - start, 2)
    return {"outputs": [f"📰 NEWS & SENTIMENT (Latency: {latency}s)\n{result}"]}


@traceable(name="Risk Agent")
def risk_node(state: GraphState):
    start = time.time()
    crew = Crew(agents=[risk_analyst], tasks=[risk_task], process=Process.sequential)
    result = crew.kickoff(inputs={"ticker": state["ticker"]})
    latency = round(time.time() - start, 2)
    return {"outputs": [f"⚠️ RISK ASSESSMENT (Latency: {latency}s)\n{result}"]}


@traceable(name="RAG Agent")
def rag_node(state: GraphState):
    start = time.time()

    loader = PyPDFLoader(state["doc_path"]) if state["doc_path"].endswith(".pdf") else TextLoader(state["doc_path"])
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = splitter.split_documents(docs)

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(chunks, embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    retrieved_docs = retriever.invoke(state["query"])
    context = "\n\n".join(d.page_content for d in retrieved_docs)

    prompt = f"""
Answer ONLY using context below.

Context:
{context}

Question:
{state['query']}
"""

    answer = rag_agent.llm.call(prompt)
    latency = round(time.time() - start, 2)

    return {"outputs": [f"📄 DOCUMENT INSIGHTS (Latency: {latency}s)\n{answer.strip()}"]}


@traceable(name="Performance Agent")
def performance_node(state: GraphState):
    start = time.time()

    combined_output = "\n\n".join(
        [o.content if hasattr(o, "content") else str(o)
         for o in state["outputs"]]
    )

    eval_prompt = f"""
Evaluate the following outputs.

{combined_output}

Give scores (0-10):
1. Accuracy
2. Content Freshness
3. Completeness
4. Clarity & Quality

Return:
- Score table
- Short explanation
- Overall rating out of 10
"""

    evaluation = performance_agent.llm.call(eval_prompt)
    latency = round(time.time() - start, 2)

    return {"outputs": [f"📈 PERFORMANCE EVALUATION (Latency: {latency}s)\n{evaluation.strip()}"]}

# =========================
# Build Graph
# =========================
workflow = StateGraph(GraphState)

workflow.add_node("orchestrator", orchestrator_node)
workflow.add_node("financial", financial_node)
workflow.add_node("news", news_node)
workflow.add_node("risk", risk_node)
workflow.add_node("rag", rag_node)
workflow.add_node("performance", performance_node)

workflow.set_entry_point("orchestrator")
workflow.add_conditional_edges("orchestrator", lambda s: s["routes"])

workflow.add_edge("financial", "performance")
workflow.add_edge("news", "performance")
workflow.add_edge("risk", "performance")
workflow.add_edge("rag", "performance")

workflow.add_edge("performance", END)

app = workflow.compile()

# =========================
# Run
# =========================
if __name__ == "__main__":

    print("\n### LangGraph + CrewAI Financial Multi-Agent System ###")
    print("LangSmith tracing enabled.\n")

    while True:

        query = input("\nAsk your financial question: ").strip()

        if query.lower() in ["quit", "exit", "bye"]:
            print("\n👋 Exiting chatbot.")
            break

        ticker = input("Enter company ticker (or press Enter): ").strip()
        doc_path = input("Enter document path if any (or press Enter): ").strip()

        state: GraphState = {
            "query": query,
            "ticker": ticker,
            "doc_path": doc_path,
            "routes": [],
            "outputs": []
        }

        result = app.invoke(state)

        print("\n========================")
        print("FINAL REPORT")
        print("========================\n")

        for msg in result["outputs"]:
            print(msg if isinstance(msg, str) else msg.content)
            print()