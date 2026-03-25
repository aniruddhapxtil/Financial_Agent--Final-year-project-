import json
import time
from typing import Dict, List



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
    """
    Simple heuristic scoring (1–5)
    You can later replace this with LLM judge
    """

    score = 0

    # Check for key sections
    if "financial summary" in text.lower():
        score += 1
    if "key insights" in text.lower():
        score += 1
    if "investment outlook" in text.lower():
        score += 1

    # Check if numbers exist
    if any(char.isdigit() for char in text):
        score += 1

    # Check structure (table)
    if "|" in text:
        score += 1

    return score  # max = 5


# =========================
# MAIN EVALUATION FUNCTION
# =========================

def evaluate_system(dataset_path: str = "evaluation_dataset.json"):

    with open(dataset_path, "r") as f:
        dataset = json.load(f)

    total = 0
    correct = 0

    sentiment_true = []
    sentiment_pred = []

    risk_true = []
    risk_pred = []

    financial_scores = []
    latencies = []

    print("\n🚀 Starting Evaluation...\n")

    for i, item in enumerate(dataset):

        query = item["query"]
        expected: Dict = item["expected"]

        print(f"🔍 Test {i+1}: {query}")

        start = time.time()

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

        # =========================
        # SENTIMENT EVALUATION
        # =========================
        if "sentiment" in expected:
            pred = extract_sentiment(output_text)
            true = expected["sentiment"]

            sentiment_true.append(true)
            sentiment_pred.append(pred)

            if pred == true:
                correct += 1
            total += 1

            print(f"   Sentiment → Pred: {pred} | True: {true}")

        # =========================
        # RISK EVALUATION
        # =========================
        if "risk" in expected:
            pred = extract_risk(output_text)
            true = expected["risk"]

            risk_true.append(true)
            risk_pred.append(pred)

            if pred == true:
                correct += 1
            total += 1

            print(f"   Risk → Pred: {pred} | True: {true}")

        # =========================
        # FINANCIAL QUALITY
        # =========================
        if "financial" in expected:
            score = evaluate_financial_quality(output_text)
            financial_scores.append(score)

            print(f"   Financial Score: {score}/5")

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

    print("\n==============================")
    print("📊 FINAL RESULTS")
    print("==============================\n")

    print(f"✅ Accuracy: {accuracy * 100:.2f}%")
    print(f"⏱ Avg Latency: {avg_latency:.2f} sec")

    if financial_scores:
        print(f"📈 Avg Financial Quality Score: {avg_financial_score:.2f}/5")


    return {
        "accuracy": accuracy,
        "avg_latency": avg_latency,
        "financial_score": avg_financial_score
    }


# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    evaluate_system()