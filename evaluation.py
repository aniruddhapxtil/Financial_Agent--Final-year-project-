# import json
# import time
# import pandas as pd
# import os
# import re
# from typing import Dict, List

# # Ensure main.py is in the same directory
# from main import run_graph

# # =========================
# # SEMANTIC OUTPUT PARSERS
# # =========================

# def extract_sentiment(text: str) -> str:
#     """Uses semantic clusters to identify intent rather than exact words."""
#     text = text.lower()
    
#     # Semantic Clusters
#     bullish_keywords = ["bullish", "positive", "growth", "upside", "optimistic", "outperform", "buy"]
#     bearish_keywords = ["bearish", "negative", "downside", "pessimistic", "underperform", "decline", "sell"]
#     neutral_keywords = ["neutral", "stable", "steady", "balanced", "sideways", "hold"]

#     if any(word in text for word in bullish_keywords):
#         return "Bullish"
#     if any(word in text for word in bearish_keywords):
#         return "Bearish"
#     if any(word in text for word in neutral_keywords):
#         return "Neutral"

#     return "Unknown"

# def extract_risk(text: str) -> str:
#     """Uses phrase-matching to prevent logic collisions (e.g., 'not low' matching 'low')."""
#     text = text.lower()
    
#     # Priority 1: Full Phrase Matching
#     if "high risk" in text or "significant risk" in text or "aggressive" in text:
#         return "High"
#     if "medium risk" in text or "moderate risk" in text or "average risk" in text:
#         return "Medium"
#     if "low risk" in text or "minimal risk" in text or "conservative" in text:
#         return "Low"
    
#     # Priority 2: Keyword Fallback
#     if "high" in text: return "High"
#     if "medium" in text: return "Medium"
#     if "low" in text: return "Low"

#     return "Unknown"

# # =========================
# # CONTEXT-AWARE QUALITY CHECK
# # =========================

# def evaluate_financial_quality(text: str, difficulty: str) -> int:
#     """Grades quality based on the complexity of the task (RAG vs Tool)."""
#     score = 0
#     text_lower = text.lower()

#     # Base: Presence of numerical data
#     if any(char.isdigit() for char in text):
#         score += 1

#     if difficulty == "hard":
#         # RAG Quality: Focus on Citations and Depth
#         if any(kw in text_lower for kw in ["section", "page", "document", "report", "cited"]):
#             score += 2  # Citation bonus
#         if len(text) > 200:
#             score += 2  # Information density bonus
#     else:
#         # Agent Quality: Focus on Structure and Insights
#         if "financial summary" in text_lower or "summary" in text_lower: score += 1
#         if "key insights" in text_lower or "highlights" in text_lower: score += 1
#         if "|" in text: score += 1 # Markdown table check
#         if "outlook" in text_lower or "recommendation" in text_lower: score += 1

#     return min(score, 5) # Cap at 5 points

# # =========================
# # REPORT EXPORTING
# # =========================

# def export_evaluation_report(results_list: List[Dict]):
#     if not results_list:
#         print("⚠️ No results to export.")
#         return

#     df = pd.DataFrame(results_list)
#     df.to_csv("evaluation_results_detailed.csv", index=False)
    
#     summary = df.groupby("Difficulty").agg({
#         "IsCorrect": "mean",
#         "Latency": "mean",
#         "FinancialScore": "mean"
#     }).reset_index()
    
#     summary.columns = ["Difficulty", "Avg Accuracy", "Avg Latency (s)", "Avg Fin Score"]
#     summary.to_csv("accuracy_by_difficulty.csv", index=False)
#     print("\n✅ Reports generated: evaluation_results_detailed.csv, accuracy_by_difficulty.csv")

# # =========================
# # MAIN EVALUATION FUNCTION
# # =========================

# def evaluate_system(dataset_path: str = "evaluation_dataset_demo.json"):
#     if not os.path.exists(dataset_path):
#         print(f"❌ Error: {dataset_path} not found.")
#         return

#     with open(dataset_path, "r") as f:
#         dataset = json.load(f)

#     total = 0
#     correct = 0
#     results_for_csv = []
#     financial_scores = []
#     latencies = []

#     difficulty_stats = {
#         "easy": {"total": 0, "correct": 0},
#         "medium": {"total": 0, "correct": 0},
#         "hard": {"total": 0, "correct": 0}
#     }

#     print("\n🚀 Starting Semantic Evaluation...\n")

#     for difficulty in ["easy", "medium", "hard"]:
#         items = dataset.get(difficulty, [])

#         for i, item in enumerate(items):
#             query = item["query"]
#             expected: Dict = item["expected"]

#             # AUTOMATIC RAG TRIGGER
#             doc_path = ""
#             if difficulty == "hard":
#                 doc_path = "company_report.txt"
#                 if not os.path.exists(doc_path):
#                     print(f"⚠️ Warning: {doc_path} missing.")

#             print(f"🔍 [{difficulty.upper()}] Test {i+1}: {query}")

#             # Run the system
#             start_time = time.time()
#             result, debug = run_graph(query, doc_path)
#             latency = debug.get("latency_total", round(time.time() - start_time, 2))
#             latencies.append(latency)

#             outputs = result.get("outputs", [])
#             output_text = " ".join([o if isinstance(o, str) else getattr(o, "content", str(o)) for o in outputs])

#             # --- SEMANTIC ACCURACY LOGIC ---
#             local_correct = 0
#             local_total = 0

#             if "sentiment" in expected:
#                 pred = extract_sentiment(output_text)
#                 if pred == expected["sentiment"]: local_correct += 1
#                 local_total += 1
#                 print(f"   Sentiment → Pred: {pred} | True: {expected['sentiment']}")

#             if "risk" in expected:
#                 pred = extract_risk(output_text)
#                 if pred == expected["risk"]: local_correct += 1
#                 local_total += 1
#                 print(f"   Risk → Pred: {pred} | True: {expected['risk']}")

#             fin_score = None
#             if "financial" in expected:
#                 fin_score = evaluate_financial_quality(output_text, difficulty)
#                 financial_scores.append(fin_score)
#                 print(f"   Financial Score: {fin_score}/5")

#             is_prompt_correct = (local_correct == local_total) if local_total > 0 else True
#             if is_prompt_correct: correct += 1
#             total += 1

#             difficulty_stats[difficulty]["total"] += 1
#             if is_prompt_correct: difficulty_stats[difficulty]["correct"] += 1

#             results_for_csv.append({
#                 "Difficulty": difficulty,
#                 "Query": query,
#                 "IsCorrect": is_prompt_correct,
#                 "Latency": latency,
#                 "FinancialScore": fin_score,
#                 "Predicted_Sentiment": extract_sentiment(output_text) if "sentiment" in expected else "N/A",
#                 "Predicted_Risk": extract_risk(output_text) if "risk" in expected else "N/A",
#                 "Response_Preview": output_text[:150].replace("\n", " ") + "..."
#             })
#             print(f"   Latency: {latency}s\n")

#     accuracy = correct / total if total > 0 else 0
#     avg_latency = sum(latencies) / len(latencies) if latencies else 0
#     avg_financial_score = sum(financial_scores) / len(financial_scores) if financial_scores else 0

#     print("\n" + "="*40 + "\n📊 FINAL SEMANTIC RESULTS\n" + "="*40)
#     print(f"✅ Overall Accuracy: {accuracy * 100:.2f}%")
#     print(f"⏱ Avg Latency: {avg_latency:.2f}s")
#     print(f"📈 Avg Financial Score: {avg_financial_score:.2f}/5")

#     for d in ["easy", "medium", "hard"]:
#         d_stats = difficulty_stats[d]
#         d_acc = (d_stats["correct"] / d_stats["total"]) if d_stats["total"] > 0 else 0
#         print(f"{d.upper()}: {d_acc * 100:.2f}%")

#     export_evaluation_report(results_for_csv)

#     return {
#         "accuracy": accuracy,
#         "avg_latency": avg_latency,
#         "financial_score": avg_financial_score,
#         "financial_scores_list": financial_scores,
#         "latencies": latencies,
#         "difficulty_stats": difficulty_stats,
#         "detailed_results": results_for_csv
#     }

# if __name__ == "__main__":
#     evaluate_system()

import json
import time
import pandas as pd
import os
import re
from typing import Dict, List

# Ensure main.py is in the same directory
from main import run_graph

# =========================
# SEMANTIC OUTPUT PARSERS
# =========================

def extract_sentiment(text: str) -> str:
    """Uses semantic clusters to identify intent rather than exact words."""
    text = text.lower()
    
    # Semantic Clusters
    bullish_keywords = ["bullish", "positive", "growth", "upside", "optimistic", "outperform", "buy"]
    bearish_keywords = ["bearish", "negative", "downside", "pessimistic", "underperform", "decline", "sell"]
    neutral_keywords = ["neutral", "stable", "steady", "balanced", "sideways", "hold"]

    if any(word in text for word in bullish_keywords):
        return "Bullish"
    if any(word in text for word in bearish_keywords):
        return "Bearish"
    if any(word in text for word in neutral_keywords):
        return "Neutral"

    return "Unknown"

def extract_risk(text: str) -> str:
    """Uses phrase-matching to prevent logic collisions (e.g., 'not low' matching 'low')."""
    text = text.lower()
    
    # Priority 1: Full Phrase Matching
    if "high risk" in text or "significant risk" in text or "aggressive" in text:
        return "High"
    if "medium risk" in text or "moderate risk" in text or "average risk" in text:
        return "Medium"
    if "low risk" in text or "minimal risk" in text or "conservative" in text:
        return "Low"
    
    # Priority 2: Keyword Fallback
    if "high" in text: return "High"
    if "medium" in text: return "Medium"
    if "low" in text: return "Low"

    return "Unknown"

# =========================
# CONTEXT-AWARE QUALITY CHECK
# =========================

def evaluate_financial_quality(text: str, difficulty: str) -> int:
    """Grades quality based on the complexity of the task (RAG vs Tool)."""
    score = 0
    text_lower = text.lower()

    # Base: Presence of numerical data
    if any(char.isdigit() for char in text):
        score += 1

    if difficulty == "hard":
        # RAG Quality: Focus on Citations and Depth
        if any(kw in text_lower for kw in ["section", "page", "document", "report", "cited"]):
            score += 2  # Citation bonus
        if len(text) > 200:
            score += 2  # Information density bonus
    else:
        # Agent Quality: Focus on Structure and Insights
        if "financial summary" in text_lower or "summary" in text_lower: score += 1
        if "key insights" in text_lower or "highlights" in text_lower: score += 1
        if "|" in text: score += 1 # Markdown table check
        if "outlook" in text_lower or "recommendation" in text_lower: score += 1

    return min(score, 5) # Cap at 5 points

# =========================
# REPORT EXPORTING
# =========================

def export_evaluation_report(results_list: List[Dict]):
    if not results_list:
        print("⚠️ No results to export.")
        return

    df = pd.DataFrame(results_list)
    df.to_csv("evaluation_results_detailed.csv", index=False)
    
    summary = df.groupby("Difficulty").agg({
        "IsCorrect": "mean",
        "Latency": "mean",
        "FinancialScore": "mean"
    }).reset_index()
    
    summary.columns = ["Difficulty", "Avg Accuracy", "Avg Latency (s)", "Avg Fin Score"]
    summary.to_csv("accuracy_by_difficulty.csv", index=False)
    print("\n✅ Reports generated: evaluation_results_detailed.csv, accuracy_by_difficulty.csv")

# =========================
# MAIN EVALUATION FUNCTION
# =========================

def evaluate_system(dataset_path: str = "eval_dataset_demo.json"):
    if not os.path.exists(dataset_path):
        print(f"❌ Error: {dataset_path} not found.")
        return

    with open(dataset_path, "r") as f:
        dataset = json.load(f)

    total = 0
    correct = 0
    results_for_csv = []
    financial_scores = []
    latencies = []
    accuracy_list = []   # NEW

    difficulty_stats = {
        "easy": {"total": 0, "correct": 0},
        "medium": {"total": 0, "correct": 0},
        "hard": {"total": 0, "correct": 0}
    }

    print("\n🚀 Starting Semantic Evaluation...\n")

    for difficulty in ["easy", "medium", "hard"]:
        items = dataset.get(difficulty, [])

        for i, item in enumerate(items):
            query = item["query"]
            expected: Dict = item["expected"]

            # AUTOMATIC RAG TRIGGER
            doc_path = ""
            if difficulty == "hard":
                doc_path = "company_report.txt"
                if not os.path.exists(doc_path):
                    print(f"⚠️ Warning: {doc_path} missing.")

            print(f"🔍 [{difficulty.upper()}] Test {i+1}: {query}")

            # Run the system with 429 Rate Limit Retry Logic
            start_time = time.time()
            max_retries = 3
            retry_delay = 15  # Wait 15 seconds if a 429 is hit
            
            result = None
            debug = {}
            
            for attempt in range(max_retries):
                try:
                    result, debug = run_graph(query, doc_path)
                    break  # Success! Break out of the retry loop
                except Exception as e:
                    error_msg = str(e)
                    if "429" in error_msg or "RateLimit" in error_msg or "Too Many Requests" in error_msg:
                        print(f"⚠️ API Rate Limit (429) Hit! Pausing for {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                    else:
                        print(f"❌ Non-429 Error encountered: {error_msg}")
                        result = {"outputs": [f"Error: {error_msg}"]}
                        debug = {"latency_total": round(time.time() - start_time, 2)}
                        break  # Break out immediately if it's not a rate limit error
            
            # Fallback just in case all retries fail
            if result is None:
                result = {"outputs": ["Error: API blocked after max retries."]}
                debug = {"latency_total": round(time.time() - start_time, 2)}

            latency = debug.get("latency_total", round(time.time() - start_time, 2))
            latencies.append(latency)

            outputs = result.get("outputs", [])
            output_text = " ".join([o if isinstance(o, str) else getattr(o, "content", str(o)) for o in outputs])

            # --- SEMANTIC ACCURACY LOGIC ---
            local_correct = 0
            local_total = 0

            if "sentiment" in expected:
                pred = extract_sentiment(output_text)
                if pred == expected["sentiment"]: local_correct += 1
                local_total += 1
                print(f"   Sentiment → Pred: {pred} | True: {expected['sentiment']}")

            if "risk" in expected:
                pred = extract_risk(output_text)
                if pred == expected["risk"]: local_correct += 1
                local_total += 1
                print(f"   Risk → Pred: {pred} | True: {expected['risk']}")

            fin_score = None
            if "financial" in expected:
                fin_score = evaluate_financial_quality(output_text, difficulty)
                financial_scores.append(fin_score)
                print(f"   Financial Score: {fin_score}/5")

            # is_prompt_correct = (local_correct == local_total) if local_total > 0 else True
            # if is_prompt_correct: correct += 1
            # total += 1
            is_prompt_correct = (local_correct == local_total) if local_total > 0 else True

            # store per-question accuracy
            accuracy_list.append(1 if is_prompt_correct else 0)

            if is_prompt_correct:
                correct += 1

            total += 1

            difficulty_stats[difficulty]["total"] += 1
            if is_prompt_correct: difficulty_stats[difficulty]["correct"] += 1

            results_for_csv.append({
                "Difficulty": difficulty,
                "Query": query,
                "IsCorrect": is_prompt_correct,
                "Latency": latency,
                "FinancialScore": fin_score,
                "Predicted_Sentiment": extract_sentiment(output_text) if "sentiment" in expected else "N/A",
                "Predicted_Risk": extract_risk(output_text) if "risk" in expected else "N/A",
                "Response_Preview": output_text[:150].replace("\n", " ") + "..."
            })
            print(f"   Latency: {latency}s\n")

    accuracy = correct / total if total > 0 else 0
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    avg_financial_score = sum(financial_scores) / len(financial_scores) if financial_scores else 0

    print("\n" + "="*40 + "\n📊 FINAL SEMANTIC RESULTS\n" + "="*40)
    print(f"✅ Overall Accuracy: {accuracy * 100:.2f}%")
    print(f"⏱ Avg Latency: {avg_latency:.2f}s")
    print(f"📈 Avg Financial Score: {avg_financial_score:.2f}/5")

    for d in ["easy", "medium", "hard"]:
        d_stats = difficulty_stats[d]
        d_acc = (d_stats["correct"] / d_stats["total"]) if d_stats["total"] > 0 else 0
        print(f"{d.upper()}: {d_acc * 100:.2f}%")

    export_evaluation_report(results_for_csv)

    return {
    "accuracy": accuracy,
    "avg_latency": avg_latency,
    "financial_score": avg_financial_score,
    "financial_scores_list": financial_scores,
    "latencies": latencies,
    "accuracy_list": accuracy_list,
    "difficulty_stats": difficulty_stats,
    "detailed_results": results_for_csv
}

if __name__ == "__main__":
    evaluate_system()