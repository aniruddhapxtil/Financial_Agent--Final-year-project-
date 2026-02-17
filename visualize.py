# visualize.py

from langgraph.graph import StateGraph, END
from main import GraphState

# -------------------------
# Dummy nodes for visualization
# -------------------------
def dummy(state):
    return state

# =========================
# Build VISUAL GRAPH ONLY
# =========================
viz = StateGraph(GraphState)

viz.add_node("orchestrator", dummy)
viz.add_node("financial", dummy)
viz.add_node("news", dummy)
viz.add_node("risk", dummy)
viz.add_node("rag", dummy)
viz.add_node("performance", dummy)

viz.set_entry_point("orchestrator")

# ⭐ EXPLICIT EDGES (for clean diagram)
viz.add_edge("orchestrator", "financial")
viz.add_edge("orchestrator", "news")
viz.add_edge("orchestrator", "risk")
viz.add_edge("orchestrator", "rag")

viz.add_edge("financial", "performance")
viz.add_edge("news", "performance")
viz.add_edge("risk", "performance")
viz.add_edge("rag", "performance")

viz.add_edge("performance", END)

app_viz = viz.compile()

# =========================
# Export Mermaid Diagram
# =========================
mermaid_code = app_viz.get_graph().draw_mermaid()

with open("langgraph_clean.mmd", "w", encoding="utf-8") as f:
    f.write(mermaid_code)

print("✅ Clean graph generated!")
print("Open https://mermaid.live and paste langgraph_clean.mmd")
