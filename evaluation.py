import json
import time
import pandas as pd
from typing import Dict, List

# Ensure main.py is in the same directory
from main import run_graph

# =========================
# OUTPUT PARSERS
# =========================

def extract_sentiment(text: str) -> str:
    text = text.lower()

    if "bullish" in text:
        return "Bullish"
    elif "bearish" in text:
        return "Bearish"
    elif "neutral" in text:
        return "Neutral"

    return "Unknown"


def extract_risk(text: str) -> str:
    text = text.lower()

    if "low" in text:
        return "Low"
    elif "medium" in text:
        return "Medium"
    elif "high" in text:
        return "High"

    return "Unknown"


# =========================
# FINANCIAL QUALITY CHECK
# =========================

def evaluate_financial_quality(text: str) -> int:
    score = 0
    text_lower = text.lower()

    if "financial summary" in text_lower:
        score += 1
    if "key insights" in text_lower:
        score += 1
    if "investment outlook" in text_lower:
        score += 1
    if any(char.isdigit() for char in text):
        score += 1
    if "|" in text:
        score += 1

    return score  # max = 5


# =========================
# REPORT EXPORTING
# =========================

def export_evaluation_report(results_list: List[Dict]):
    """
    Generates CSV reports based on the evaluation results.
    """
    if not results_list:
        print("⚠️ No results to export.")
        return

    df = pd.DataFrame(results_list)
    
    # 1. Detailed Report: Every single test case
    df.to_csv("evaluation_results_detailed.csv", index=False)
    
    # 2. Summary Report: Average Accuracy and Latency by Difficulty
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

def evaluate_system(dataset_path: str = "evaluation_dataset.json"):

    with open(dataset_path, "r") as f:
        dataset = json.load(f)

    total = 0
    correct = 0
    results_for_csv = [] # To store data for pandas

    financial_scores = []
    latencies = []

    difficulty_stats = {
        "easy": {"total": 0, "correct": 0},
        "medium": {"total": 0, "correct": 0},
        "hard": {"total": 0, "correct": 0}
    }

    print("\n🚀 Starting Evaluation...\n")

    # 🔥 LOOP THROUGH DIFFICULTY LEVELS
    for difficulty in ["easy", "medium", "hard"]:

        items = dataset.get(difficulty, [])

        for i, item in enumerate(items):

            query = item["query"]
            expected: Dict = item["expected"]

            print(f"🔍 [{difficulty.upper()}] Test {i+1}: {query}")

            start = time.time()

            # Execute the graph
            result, debug = run_graph(query, "")

            latency = debug.get("latency_total", 0)
            latencies.append(latency)

            outputs = result.get("outputs", [])
            formatted_outputs = []

            for o in outputs:
                if isinstance(o, str):
                    content = o
                else:
                    content = getattr(o, "content", str(o))
                formatted_outputs.append(content)

            output_text = " ".join(formatted_outputs)

            local_correct = 0
            local_total = 0

            # --- SENTIMENT CHECK ---
            if "sentiment" in expected:
                pred = extract_sentiment(output_text)
                true = expected["sentiment"]
                if pred == true:
                    local_correct += 1
                local_total += 1
                print(f"   Sentiment → Pred: {pred} | True: {true}")

            # --- RISK CHECK ---
            if "risk" in expected:
                pred = extract_risk(output_text)
                true = expected["risk"]
                if pred == true:
                    local_correct += 1
                local_total += 1
                print(f"   Risk → Pred: {pred} | True: {true}")

            # --- FINANCIAL CHECK ---
            fin_score = None
            if "financial" in expected:
                fin_score = evaluate_financial_quality(output_text)
                financial_scores.append(fin_score)
                print(f"   Financial Score: {fin_score}/5")

            # Determine if this specific prompt passed its checks
            is_prompt_correct = (local_correct == local_total) if local_total > 0 else True
            
            if is_prompt_correct:
                correct += 1
            total += 1

            # --- DIFFICULTY TRACKING ---
            difficulty_stats[difficulty]["total"] += 1
            if is_prompt_correct:
                difficulty_stats[difficulty]["correct"] += 1

            # --- STORE FOR CSV ---
            results_for_csv.append({
                "Difficulty": difficulty,
                "Query": query,
                "IsCorrect": is_prompt_correct,
                "Latency": latency,
                "FinancialScore": fin_score,
                "Predicted_Sentiment": extract_sentiment(output_text) if "sentiment" in expected else "N/A",
                "Predicted_Risk": extract_risk(output_text) if "risk" in expected else "N/A"
            })

            print(f"   Latency: {latency}s\n")

    # =========================
    # FINAL METRICS
    # =========================

    accuracy = correct / total if total > 0 else 0
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    avg_financial_score = (
        sum(financial_scores) / len(financial_scores)
        if financial_scores else 0
    )

    print("\n" + "="*30)
    print("📊 FINAL RESULTS")
    print("="*30 + "\n")

    print(f"✅ Overall Accuracy: {accuracy * 100:.2f}%")
    print(f"⏱ Avg Latency: {avg_latency:.2f} sec")

    if financial_scores:
        print(f"📈 Avg Financial Quality Score: {avg_financial_score:.2f}/5")

    print("\n🎯 Difficulty-wise Accuracy:")
    for d in ["easy", "medium", "hard"]:
        d_total = difficulty_stats[d]["total"]
        d_correct = difficulty_stats[d]["correct"]
        d_acc = (d_correct / d_total) if d_total > 0 else 0
        print(f"{d.upper()}: {d_acc * 100:.2f}%")

    # 🔥 GENERATE CSV REPORTS
    export_evaluation_report(results_for_csv)

# In evaluation.py - Ensure the return block looks exactly like this:
    return {
        "accuracy": accuracy,
        "avg_latency": avg_latency,
        "financial_score": avg_financial_score,
        "financial_scores_list": financial_scores,  # 👈 THIS WAS MISSING OR MISNAMED
        "latencies": latencies,                    # 👈 NEEDED FOR THE BAR CHART
        "difficulty_stats": difficulty_stats,
        "detailed_results": results_for_csv
    }


# =========================
# ENTRY POINT
# =========================

if __name__ == "__main__":
    evaluate_system()