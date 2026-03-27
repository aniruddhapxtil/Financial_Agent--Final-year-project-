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


# #new code withour perfroamcen agent
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

#     for company, ticker in company_map.items():
#         if company in query_lower:
#             return ticker

#     match = re.search(r"\b[A-Z]{2,5}\b", query)
#     if match:
#         return match.group()

#     return "NVDA"


# # Import tools
# from tools import (
#     fetch_stock_data,
#     fetch_news_and_sentiment,
#     fetch_risk_metrics,
#     read_uploaded_document
# )

# load_dotenv()

# # =========================
# # LLM Configuration
# # =========================
# llm = LLM(
#     model="meta/llama3-70b-instruct",
#     api_key=os.getenv("NVIDIA_API_KEY"),
#     base_url="https://integrate.api.nvidia.com/v1",
#     provider="openai",
#     temperature=0,
#     max_tokens=512
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

# # =========================
# # Build Workflow
# # =========================
# workflow = StateGraph(GraphState)

# workflow.add_node("orchestrator", orchestrator_node)
# workflow.add_node("financial", financial_node)
# workflow.add_node("news", news_node)
# workflow.add_node("risk", risk_node)
# workflow.add_node("rag", rag_node)

# workflow.set_entry_point("orchestrator")
# workflow.add_conditional_edges("orchestrator", lambda s: s["routes"])

# workflow.add_edge("financial", END)
# workflow.add_edge("news", END)
# workflow.add_edge("risk", END)
# workflow.add_edge("rag", END)

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


# #latst compasion code also
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

# # Import tools
# from tools import (
#     fetch_stock_data,
#     fetch_news_and_sentiment,
#     fetch_risk_metrics,
#     read_uploaded_document
# )

# load_dotenv()

# # =========================
# # Automatic Multi-Ticker Detection
# # =========================
# def extract_tickers(query: str) -> List[str]:

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

#     tickers = []

#     for company, ticker in company_map.items():
#         if company in query_lower:
#             tickers.append(ticker)

#     # Detect ticker symbols directly
#     matches = re.findall(r"\b[A-Z]{2,5}\b", query)
#     tickers.extend(matches)

#     # Remove duplicates
#     tickers = list(set(tickers))

#     if not tickers:
#         tickers = ["NVDA"]

#     return tickers


# # =========================
# # LLM Configuration
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
#     goal="Analyze {ticker} financial health",
#     backstory="Expert in valuation and financial metrics.",
#     tools=[fetch_stock_data],
#     llm=llm
# )

# news_analyst = Agent(
#     role="News Analyst",
#     goal="Analyze sentiment from latest headlines for {ticker}",
#     backstory="Tracks market-moving news.",
#     tools=[fetch_news_and_sentiment],
#     llm=llm
# )

# risk_analyst = Agent(
#     role="Risk Analyst",
#     goal="Assess market risk for {ticker}",
#     backstory="Specialist in volatility and correlations.",
#     tools=[fetch_risk_metrics],
#     llm=llm
# )

# rag_agent = Agent(
#     role="Document Intelligence Agent",
#     goal="Answer questions strictly from document {doc_path}",
#     backstory="Expert in financial document analysis.",
#     tools=[read_uploaded_document],
#     llm=llm
# )

# # =========================
# # Graph State
# # =========================
# class GraphState(TypedDict):
#     query: str
#     tickers: List[str]
#     doc_path: str
#     routes: List[str]
#     outputs: Annotated[List[str], add_messages]

# # =========================
# # Intent Detection
# # =========================
# def fuzzy_contains(query: str, keywords: list) -> bool:
#     return any(fuzz.partial_ratio(query.lower(), kw) > 70 for kw in keywords)

# financial_keywords = ["financial", "valuation", "revenue", "price", "pe"]
# news_keywords = ["news", "sentiment", "headline"]
# risk_keywords = ["risk", "volatility", "beta"]

# # =========================
# # Orchestrator
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
# # Financial Node
# # =========================
# @traceable(name="Financial Node")
# def financial_node(state: GraphState):

#     start = time.time()
#     results = []

#     for ticker in state["tickers"]:

#         task = Task(
#             description=f"Provide financial analysis for {ticker}",
#             expected_output="Price, Market Cap, PE ratio summary",
#             agent=fin_analyst
#         )

#         crew = Crew(
#             agents=[fin_analyst],
#             tasks=[task],
#             process=Process.sequential
#         )

#         result = crew.kickoff(inputs={"ticker": ticker})
#         results.append(f"### {ticker}\n{result}")

#     return {
#         "outputs": [
#             f"📊 FINANCIAL ANALYSIS ({round(time.time()-start,2)}s)\n\n" +
#             "\n\n".join(results)
#         ]
#     }


# # =========================
# # News Node
# # =========================
# @traceable(name="News Node")
# def news_node(state: GraphState):

#     start = time.time()
#     results = []

#     for ticker in state["tickers"]:

#         task = Task(
#             description=f"Analyze news sentiment for {ticker}",
#             expected_output="Top headlines and sentiment summary",
#             agent=news_analyst
#         )

#         crew = Crew(
#             agents=[news_analyst],
#             tasks=[task],
#             process=Process.sequential
#         )

#         result = crew.kickoff(inputs={"ticker": ticker})
#         results.append(f"### {ticker}\n{result}")

#     return {
#         "outputs": [
#             f"📰 NEWS & SENTIMENT ({round(time.time()-start,2)}s)\n\n" +
#             "\n\n".join(results)
#         ]
#     }


# # =========================
# # Risk Node
# # =========================
# @traceable(name="Risk Node")
# def risk_node(state: GraphState):

#     start = time.time()
#     results = []

#     for ticker in state["tickers"]:

#         task = Task(
#             description=f"Assess risk metrics for {ticker}",
#             expected_output="Beta, volatility, risk summary",
#             agent=risk_analyst
#         )

#         crew = Crew(
#             agents=[risk_analyst],
#             tasks=[task],
#             process=Process.sequential
#         )

#         result = crew.kickoff(inputs={"ticker": ticker})
#         results.append(f"### {ticker}\n{result}")

#     return {
#         "outputs": [
#             f"⚠️ RISK ASSESSMENT ({round(time.time()-start,2)}s)\n\n" +
#             "\n\n".join(results)
#         ]
#     }


# # =========================
# # RAG Node
# # =========================
# @traceable(name="RAG Node")
# def rag_node(state: GraphState):

#     start = time.time()

#     task = Task(
#         description=f"Read {state['doc_path']} and answer: {state['query']}",
#         expected_output="Answer based only on document",
#         agent=rag_agent
#     )

#     crew = Crew(
#         agents=[rag_agent],
#         tasks=[task],
#         process=Process.sequential
#     )

#     result = crew.kickoff()

#     return {
#         "outputs": [
#             f"📄 DOCUMENT INSIGHTS ({round(time.time()-start,2)}s)\n{result}"
#         ]
#     }


# # =========================
# # Build Workflow
# # =========================
# workflow = StateGraph(GraphState)

# workflow.add_node("orchestrator", orchestrator_node)
# workflow.add_node("financial", financial_node)
# workflow.add_node("news", news_node)
# workflow.add_node("risk", risk_node)
# workflow.add_node("rag", rag_node)

# workflow.set_entry_point("orchestrator")

# workflow.add_conditional_edges(
#     "orchestrator",
#     lambda s: s["routes"]
# )

# workflow.add_edge("financial", END)
# workflow.add_edge("news", END)
# workflow.add_edge("risk", END)
# workflow.add_edge("rag", END)

# app = workflow.compile()

# # =========================
# # Run Graph
# # =========================
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
        routes = ["financial", "news", "risk"]

    return {"routes": routes}


# =========================
# Financial Node
# =========================
# @traceable(name="Financial Node")
# def financial_node(state: GraphState):

#     start = time.time()
#     results = []

#     for ticker in state["tickers"]:

#         task = Task(
#             description=f"""
# Use the provided financial tool data to analyze {ticker}.

# STRICT RULES:
# - You MUST use the tool output values.
# - Do NOT invent numbers.
# - If a value is missing write "Data not available".

# Return a well structured markdown report.

# FORMAT:

# ## {ticker} Financial Summary

# | Metric | Value |
# |------|------|
# | Current Price | |
# | Market Cap | |
# | PE Ratio | |
# | 52 Week High | |
# | 52 Week Low | |
# | Revenue Growth | |

# ### Key Insights
# - Bullet insight about valuation
# - Bullet insight about growth
# - Bullet insight about profitability

# ### Investment Outlook
# Provide a short professional investment outlook (3-4 sentences).
# """,
#             expected_output="Structured financial markdown report",
#             agent=fin_analyst
#         )

#         crew = Crew(
#             agents=[fin_analyst],
#             tasks=[task],
#             process=Process.sequential
#         )

#         result = crew.kickoff(inputs={"ticker": ticker})

#         results.append(f"### {ticker}\n{clean_markdown(result)}")

#     return {
#         "outputs": [
#         "\n\n".join(results)
#     ],
#         "debug": {
#         "agent": "financial",
#         "latency": round(time.time()-start, 2)
#             }
#     }
from concurrent.futures import ThreadPoolExecutor

@traceable(name="Financial Node")
def financial_node(state: GraphState):

    start = time.time()

    def run_task(ticker):

        task = Task(
            description=f"""
Use the provided financial tool data to analyze {ticker}.

STRICT RULES:
- Use tool output only
- Do NOT invent numbers
- If missing → "Data not available"

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
- 3 bullet points

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
            memory = False, #added for evaltionan only,
            max_iter=2
        )

        result = crew.kickoff(inputs={"ticker": ticker})

        return f"### {ticker}\n{clean_markdown(result)}"

    # 🔥 PARALLEL EXECUTION
    with ThreadPoolExecutor() as executor:
        results = list(executor.map(run_task, state["tickers"]))

    return {
        "outputs": [
            "\n\n".join(results)
        ],
        "debug": {
            "agent": "financial",
            "latency": round(time.time() - start, 2)
        }
    }

# =========================
# News Node
# =========================
# @traceable(name="News Node")
# def news_node(state: GraphState):

#     start = time.time()
#     results = []

#     for ticker in state["tickers"]:

#         task = Task(
#             description=f"""
# Analyze latest news for {ticker}.

# Return structured markdown:

# ## {ticker} News Sentiment

# ### Top Headlines
# - headline 1
# - headline 2
# - headline 3

# ### Overall Sentiment
# Bullish / Neutral / Bearish

# ### Key Impact
# Short explanation.
# """,
#             expected_output="News sentiment report",
#             agent=news_analyst
#         )

#         crew = Crew(
#             agents=[news_analyst],
#             tasks=[task],
#             process=Process.sequential
#         )

#         result = crew.kickoff(inputs={"ticker": ticker})

#         results.append(f"### {ticker}\n{clean_markdown(result)}")

#     return {
#          "outputs": [
#         "\n\n".join(results)
#     ],
#         "debug": {
#         "agent": "news",
#         "latency": round(time.time()-start, 2)
#         }
#     }


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


# =========================
# Risk Node
# =========================
# @traceable(name="Risk Node")
# def risk_node(state: GraphState):

#     start = time.time()
#     results = []

#     for ticker in state["tickers"]:

#         task = Task(
#             description=f"""
# Assess investment risk for {ticker}.

# Return markdown format:

# ## {ticker} Risk Assessment

# **Beta:**  
# **Volatility:**

# ### Risk Insights
# - point 1
# - point 2

# ### Overall Risk Level
# Low / Medium / High
# """,
#             expected_output="Risk analysis report",
#             agent=risk_analyst
#         )

#         crew = Crew(
#             agents=[risk_analyst],
#             tasks=[task],
#             process=Process.sequential
#         )

#         result = crew.kickoff(inputs={"ticker": ticker})

#         results.append(f"### {ticker}\n{clean_markdown(result)}")

#     return {
#         "outputs": [
#         "\n\n".join(results)
#     ],
#         "debug": {
#         "agent": "risk",
#         "latency": round(time.time()-start, 2)
#         }
#     }
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
