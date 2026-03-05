import os
import time
from typing import TypedDict, List, Annotated
from dotenv import load_dotenv

os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"

from crewai import Agent, Task, Crew, Process, LLM
from langgraph.graph import StateGraph, END, add_messages
from rapidfuzz import fuzz
from langsmith import traceable

# Import tools from your tools.py
from tools import (
    fetch_stock_data,
    fetch_news_and_sentiment,
    fetch_risk_metrics,
    read_uploaded_document
)

load_dotenv()

# =========================
# LLM Configuration (FIXED FOR NVIDIA NIM)
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

performance_agent = Agent(
    role="Performance Evaluation Agent",
    goal="Evaluate quality and accuracy of the reports generated",
    backstory="An auditor who ensures LLM outputs are helpful and non-hallucinatory.",
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

@traceable(name="Performance Node")
def performance_node(state: GraphState):
    combined_output = "\n\n".join([str(o.content if hasattr(o, 'content') else o) for o in state["outputs"]])
    eval_prompt = f"Evaluate these agent outputs for accuracy and clarity:\n\n{combined_output}\n\nReturn a Score Table (0-10) and a summary."
    evaluation = performance_agent.llm.call(eval_prompt)
    return {"outputs": [f"📈 PERFORMANCE EVALUATION\n{evaluation}"]}

# =========================
# Build Workflow
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

def run_graph(query, ticker, doc_path):
    state: GraphState = {
        "query": query,
        "ticker": ticker,
        "doc_path": doc_path,
        "routes": [],
        "outputs": []
    }
    return app.invoke(state)