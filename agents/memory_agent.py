from datetime import datetime


MAX_MEMORY_TURNS = 10
CONTEXT_TURNS = 5


def summarize_result_preview(response):
    try:
        data = response.get("primary", {}).get("data")
        if data is None or data.empty:
            return []
        return data.head(3).to_dict("records")
    except Exception:
        return []


def remember_turn(memory, question, response):
    memory = memory or []
    intent = response.get("intent", {}).get("label", "unknown")
    view_name = response.get("primary", {}).get("view", "")
    advice = response.get("advice", [])

    memory.append(
        {
            "question": question,
            "intent": intent,
            "view": view_name,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "result_preview": summarize_result_preview(response),
            "advice_preview": advice[:3] if isinstance(advice, list) else [],
        }
    )

    return memory[-MAX_MEMORY_TURNS:]


def build_memory_context(memory):
    memory = memory or []

    if not memory:
        return ""

    context_lines = []

    for index, item in enumerate(memory[-CONTEXT_TURNS:], start=1):
        context_lines.append(
            "\n".join(
                [
                    f"Turn {index}:",
                    f"Question: {item.get('question', '')}",
                    f"Intent: {item.get('intent', '')}",
                    f"View: {item.get('view', '')}",
                    f"Result preview: {item.get('result_preview', '')}",
                    f"Advice preview: {item.get('advice_preview', '')}",
                ]
            )
        )

    return "\n\n".join(context_lines)


def build_contextual_question(question, memory):
    memory_context = build_memory_context(memory)

    if not memory_context:
        return question

    return f"""
Conversation memory:
{memory_context}

Current question:
{question}

Use the conversation memory only when the current question refers to previous
analysis, for example with phrases like "that", "above", "continue", or
"compare with the previous result".
"""
