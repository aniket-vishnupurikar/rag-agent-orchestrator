# src/agents/followup_detection.py

def refers_to_previous_docs(message: str) -> bool:
    msg = message.lower()
    return any(
        phrase in msg
        for phrase in [
            "first document",
            "that document",
            "this document",
            "these documents",
            "the document you referred",
            "the documents you referred",
            "the documents you used",
            "the document you used",
        ]
    )
