
#new UI bug edit code...
import os
import time
import re
from typing import TypedDict, List, Annotated
from dotenv import load_dotenv

os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"

from crewai import Agent, Task, Crew, Process, LLM
from langgraph.graph import StateGraph, END, add_messages
from rapidfuzz import fuzz
from langsmith import traceable

# Import tools
from tools import (
    fetch_stock_data,
    fetch_news_and_sentiment,
    fetch_risk_metrics,
    read_uploaded_document
)

load_dotenv()

# =========================
# Automatic Multi-Ticker Detection
# =========================
def extract_tickers(query: str) -> List[str]:

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

    tickers = []

    for company, ticker in company_map.items():
        if company in query_lower:
            tickers.append(ticker)

    matches = re.findall(r"\b[A-Z]{2,5}\b", query)
    tickers.extend(matches)

    tickers = list(set(tickers))

    if not tickers:
        tickers = ["NVDA"]

    return tickers


# =========================
# Response Formatter
# =========================
def clean_markdown(text: str) -> str:

    text = str(text)

    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'\s+\n', '\n', text)

    return text.strip()


# =========================
# LLM Configuration
# =========================
llm = LLM(
    model="meta/llama3-70b-instruct",
    api_key=os.getenv("NVIDIA_API_KEY"),
    base_url="https://integrate.api.nvidia.com/v1",
    provider="openai",
    temperature=0,
    max_tokens=300 #change to 1024 when not doing evaltion
)

# =========================
# Agents
# =========================
fin_analyst = Agent(
    role="Senior Financial Analyst",
    goal="Analyze {ticker} financial health",
    backstory="Expert in valuation and financial metrics.",
    tools=[fetch_stock_data],
    llm=llm
)

news_analyst = Agent(
    role="News Analyst",
    goal="Analyze sentiment from latest headlines for {ticker}",
    backstory="Tracks market-moving news.",
    tools=[fetch_news_and_sentiment],
    llm=llm
)

risk_analyst = Agent(
    role="Risk Analyst",
    goal="Assess market risk for {ticker}",
    backstory="Specialist in volatility and correlations.",
    tools=[fetch_risk_metrics],
    llm=llm
)

rag_agent = Agent(
    role="Document Intelligence Agent",
    goal="Answer questions strictly from document {doc_path}",
    backstory="Expert in financial document analysis.",
    tools=[read_uploaded_document],
    llm=llm
)

# =========================
# Graph State
# =========================
class GraphState(TypedDict):
    query: str
    tickers: List[str]
    doc_path: str
    routes: List[str]
    outputs: Annotated[List[str], add_messages]


# =========================
# Intent Detection
# =========================
def fuzzy_contains(query: str, keywords: list) -> bool:
    return any(fuzz.partial_ratio(query.lower(), kw) > 70 for kw in keywords)

financial_keywords = [
    "financial", "valuation", "revenue", "profit", "income",
    "earnings", "eps", "pe", "p/e", "ratio", "balance sheet",
    "cash flow", "fundamentals", "growth", "margin",
    "overvalued", "undervalued", "fair value", "intrinsic value",
    "target price", "forecast", "outlook", "guidance",
    "should i buy", "should i invest", "is it a good investment",
    "long term", "short term", "analysis"
]


news_keywords = [
    "news", "headline", "headlines", "sentiment",
    "latest news", "recent news", "updates",
    "what happened", "why is", "why did",
    "breaking news", "market news",
    "announcement", "acquisition", "merger",
    "lawsuit", "scandal", "earnings call",
    "press release"
]

risk_keywords = [
    "risk", "volatility", "beta", "drawdown",
    "downside", "upside risk", "uncertainty",
    "safe", "risky", "stability",
    "variance", "standard deviation",
    "sharpe", "sortino",
    "crash", "fall", "drop",
    "exposure", "sensitivity"
]


# =========================
# Orchestrator
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
        routes = ["financial"]#only for evaltion time only..else put all

    return {"routes": routes}



from concurrent.futures import ThreadPoolExecutor

@traceable(name="Financial Node")
def financial_node(state: GraphState):
    start = time.time()

    def run_task(ticker):
        # Determine if this is a comparison based on the number of tickers
        is_comparison = len(state["tickers"]) > 1
        comparison_context = f"This is a comparative analysis alongside: {', '.join([t for t in state['tickers'] if t != ticker])}." if is_comparison else ""

        task = Task(
            description=f"""
Use the provided financial tool data to analyze {ticker}.
{comparison_context}

STRICT RULES:
- Use tool output only.
- Do NOT invent numbers.
- If missing → "Data not available".
- If this is a comparison, ensure the metrics are clearly presented for side-by-side reading.

Return:

## {ticker} Financial Summary

| Metric | Value |
|------|------|
| Current Price | |
| Market Cap | |
| PE Ratio | |
| 52 Week High | |
| 52 Week Low | |
| Revenue Growth | |

### Key Insights
- 3 bullet points (focus on relative strength if comparing)

### Investment Outlook
3-4 lines
""",
            expected_output="Structured financial markdown report",
            agent=fin_analyst
        )

        crew = Crew(
            agents=[fin_analyst],
            tasks=[task],
            process=Process.sequential,
            memory=False,
            max_iter=2
        )

        result = crew.kickoff(inputs={"ticker": ticker})
        return f"### {ticker}\n{clean_markdown(result)}"

    with ThreadPoolExecutor() as executor:
        results = list(executor.map(run_task, state["tickers"]))

    return {
        "outputs": ["\n\n".join(results)],
        "debug": {
            "agent": "financial",
            "latency": round(time.time() - start, 2)
        }
    }


@traceable(name="News Node")
def news_node(state: GraphState):

    start = time.time()

    def run_task(ticker):

        task = Task(
            description=f"""
Analyze latest news for {ticker}.

Return:

## {ticker} News Sentiment

### Top Headlines
- 3 headlines

### Overall Sentiment
Bullish / Neutral / Bearish

### Key Impact
Short explanation
""",
            expected_output="News sentiment report",
            agent=news_analyst
        )

        crew = Crew(
            agents=[news_analyst],
            tasks=[task],
            process=Process.sequential,
            memory = False, #added for evaltionan only
            max_iter=2
        )

        result = crew.kickoff(inputs={"ticker": ticker})

        return f"### {ticker}\n{clean_markdown(result)}"

    # 🔥 PARALLEL EXECUTION
    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(run_task, state["tickers"]))

    return {
        "outputs": [
            "\n\n".join(results)
        ],
        "debug": {
            "agent": "news",
            "latency": round(time.time() - start, 2)
        }
    }



from concurrent.futures import ThreadPoolExecutor

@traceable(name="Risk Node")
def risk_node(state: GraphState):

    start = time.time()

    def run_task(ticker):

        task = Task(
            description=f"""
Assess investment risk for {ticker}.

Return:

## {ticker} Risk Assessment

**Beta:**  
**Volatility:**

### Risk Insights
- 2 points

### Overall Risk Level
Low / Medium / High

### Investment Recommendation
Buy / Sell / Hold

### Reasoning
- 2 short bullet points explaining the recommendation

STRICT RULES:
- Recommendation must be consistent with risk level
    - Low risk → Buy or Hold
    - Medium risk → Hold
    - High risk → Sell or cautious Hold
- Do NOT invent numbers
- Base reasoning ONLY on tool output
""",
            expected_output="Risk analysis report",
            agent=risk_analyst
        )

        crew = Crew(
            agents=[risk_analyst],
            tasks=[task],
            process=Process.sequential,
            memory = False, #added for evaltionan only
            max_iter=2
        )

        result = crew.kickoff(inputs={"ticker": ticker})

        return f"### {ticker}\n{clean_markdown(result)}"

    # 🔥 PARALLEL EXECUTION
    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(run_task, state["tickers"]))

    return {
        "outputs": [
            "\n\n".join(results)
        ],
        "debug": {
            "agent": "risk",
            "latency": round(time.time() - start, 2)
        }
    }


# =========================
# RAG Node
# =========================
@traceable(name="RAG Node")
def rag_node(state: GraphState):

    start = time.time()

    task = Task(
        description=f"""
Read document {state['doc_path']} and answer:

{state['query']}

Format response in clear markdown sections.
""",
        expected_output="Document based answer",
        agent=rag_agent
    )

    crew = Crew(
        agents=[rag_agent],
        tasks=[task],
        process=Process.sequential,
        memory = False #added for evaltionan only
    )

    result = crew.kickoff()

    return {
         "outputs": [
        clean_markdown(result)
    ],
        "debug": {
        "agent": "rag",
        "latency": round(time.time()-start, 2)
        }
    }


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

workflow.add_conditional_edges(
    "orchestrator",
    lambda s: s["routes"]
)

workflow.add_edge("financial", END)
workflow.add_edge("news", END)
workflow.add_edge("risk", END)
workflow.add_edge("rag", END)

app = workflow.compile()


# =========================
# Run Graph
# =========================
# def run_graph(query, doc_path):

#     tickers = extract_tickers(query)

#     state: GraphState = {
#         "query": query,
#         "tickers": tickers,
#         "doc_path": doc_path,
#         "routes": [],
#         "outputs": []
#     }

#     return app.invoke(state)

def run_graph(query, doc_path):

    start_total = time.time()

    tickers = extract_tickers(query)

    state: GraphState = {
        "query": query,
        "tickers": tickers,
        "doc_path": doc_path,
        "routes": [],
        "outputs": []
    }

    result = app.invoke(state)

    total_time = round(time.time() - start_total, 2)

    debug_data = {
        "query": query,
        "tickers": tickers,
        "routes": result.get("routes", []),
        "outputs": result.get("outputs", []),
        "latency_total": total_time,
        "timestamp": time.strftime("%H:%M:%S")
    }

    return result, debug_data
    
