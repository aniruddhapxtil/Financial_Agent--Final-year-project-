#NEW CODE ============================================================
import os
import requests
import yfinance as yf
import numpy as np
from crewai.tools import tool
from dotenv import load_dotenv
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    CSVLoader
)

load_dotenv()
NEWS_API_KEY = os.getenv("NEWS_API_KEY")


# @tool("fetch_stock_data")
# def fetch_stock_data(ticker: str):
#     """Fetch stock price, valuation, and growth metrics."""
#     stock = yf.Ticker(ticker)
#     info = stock.info

#     return {
#         "price": info.get("currentPrice"),
#         "market_cap": info.get("marketCap"),
#         "pe_ratio": info.get("trailingPE"),
#         "revenue_growth": info.get("revenueGrowth"),
#         "ebitda_margins": info.get("ebitdaMargins"),
#         "currency": info.get("currency"),
#     }

# In tools.py

# In tools.py
@tool("fetch_stock_data")
def fetch_stock_data(ticker: str):
    """Fetch stock price, valuation, and growth metrics."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Select only essential keys to keep token count low
        essential_keys = {
            "currentPrice": info.get("currentPrice"),
            "marketCap": info.get("marketCap"),
            "trailingPE": info.get("trailingPE"),
            "revenueGrowth": info.get("revenueGrowth"),
            "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh"),
            "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow"),
            "currency": info.get("currency"),
        }
        
        # Remove None values
        return {k: v for k, v in essential_keys.items() if v is not None}
    except Exception as e:
        return {"error": f"Failed to fetch data for {ticker}: {str(e)}"}
# @tool("fetch_news_and_sentiment")
# def fetch_news_and_sentiment(ticker: str):
#     """Fetch latest news headlines for sentiment analysis."""
#     url = "https://newsapi.org/v2/everything"
#     params = {
#         "q": ticker,
#         "sortBy": "publishedAt",
#         "language": "en",
#         "apiKey": NEWS_API_KEY,
#         "pageSize": 5
#     }

#     response = requests.get(url, params=params).json()
#     articles = response.get("articles", [])

#     return [
#         {
#             "title": a.get("title"),
#             "description": a.get("description"),
#             "source": a.get("source", {}).get("name"),
#         }
#         for a in articles
#     ]

@tool("fetch_news_and_sentiment")
def fetch_news_and_sentiment(ticker: str):
    """Fetch latest news headlines for sentiment analysis."""
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": ticker,
        "sortBy": "publishedAt",
        "language": "en",
        "apiKey": NEWS_API_KEY,
        "pageSize": 5
    }

    response = requests.get(url, params=params).json()
    articles = response.get("articles", [])

    return [
        {
            "title": a.get("title"),
            "description": a.get("description"),
            "source": a.get("source", {}).get("name"),
            "url": a.get("url"),
            "published_at": a.get("publishedAt"),
        }
        for a in articles
    ]


@tool("fetch_risk_metrics")
def fetch_risk_metrics(ticker: str):
    """Compute volatility, beta, and max drawdown."""
    stock = yf.Ticker(ticker)
    hist = stock.history(period="1y")

    returns = hist["Close"].pct_change().dropna()
    volatility = np.std(returns) * np.sqrt(252)

    rolling_max = hist["Close"].cummax()
    drawdown = (hist["Close"] - rolling_max) / rolling_max

    return {
        "volatility": round(float(volatility), 4),
        "beta": stock.info.get("beta"),
        "max_drawdown": round(float(drawdown.min()), 4),
    }


@tool("read_uploaded_document")
def read_uploaded_document(file_path: str):
    """
    Reads uploaded documents (PDF, TXT, CSV) for RAG-based question answering.
    Supports multiple files separated by commas.
    """
    try:
        all_content = []
        
        # Handle multiple file paths separated by commas
        file_paths = [fp.strip() for fp in file_path.split(",") if fp.strip()]
        
        for single_path in file_paths:
            ext = os.path.splitext(single_path)[1].lower()

            if ext == ".pdf":
                loader = PyPDFLoader(single_path)
            elif ext == ".csv":
                loader = CSVLoader(single_path)
            else:
                loader = TextLoader(single_path)

            docs = loader.load()
            content = "\n".join(d.page_content for d in docs)
            
            # Add filename header to distinguish content from different files
            file_name = os.path.basename(single_path)
            all_content.append(f"=== Content from {file_name} ===\n{content}")
        
        combined_content = "\n\n".join(all_content)
        return combined_content[:8000]  # safe context size for multiple files
        
    except Exception as e:
        return f"Error reading document: {str(e)}"
