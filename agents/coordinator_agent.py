from agents.data_analysis_agent import analyze_question_with_trace
from agents.decision_agent import generate_advice
from agents.memory_agent import build_contextual_question
from agents.narrative_agent import generate_narrative_answer
from agents.review_insight_agent import extract_review_insights
from agents.visualization_agent import create_charts
from agents.what_if_agent import seller_removal_simulation


def run_agent(question, memory=None):
    memory = memory or []
    question_with_context = build_contextual_question(question, memory)

    state = analyze_question_with_trace(question_with_context)
    state["memory"] = memory[-5:]
    state["review_insights"] = extract_review_insights(state)
    state["charts"] = create_charts(state["queries"], state.get("forecast"))
    state["advice"] = generate_advice(state)
    state["what_if"] = seller_removal_simulation()

    first_chart = state["charts"][0]["figure"] if state["charts"] else None
    state["data"] = state["primary"]["data"]
    state["chart"] = first_chart

    state["advice_detail"] = state["advice"]
    state["final_answer"] = generate_narrative_answer(question, state)
    state["advice"] = (
        [state["final_answer"]]
        + state["advice_detail"]["highlights"]
        + state["advice_detail"]["recommendations"]
    )

    state["workflow"] = [
        "Coordinator Agent: receives the natural-language question and dispatches subtasks",
        "Memory Agent: injects recent conversation context for follow-up questions",
        (
            "Natural Language Understanding Agent: identifies intent as "
            f"{state['intent']['label']} with confidence {state['intent']['confidence']}"
        ),
        "Data Analysis Agent: prioritizes pre-aggregated views and falls back to base tables when needed",
        *state.get("query_strategy", {}).get("trace", []),
        "Review Insight Agent: extracts sentiment, keywords, and negative category reasons",
        "Visualization Agent: selects chart types, renders figures, and saves image files",
        "What-if Agent: simulates Top 20 high-negative-review seller removal",
        "Decision Intelligence Agent: combines metrics, forecast, NLP, anomaly, and what-if outputs",
        "Narrative Answer Agent: turns all structured results into a natural Chinese business answer",
    ]

    return state
