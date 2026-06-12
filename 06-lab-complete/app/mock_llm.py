import time

def ask(question: str) -> str:
    """
    A mock LLM function that returns a canned response.
    Simulates a delay for LLM processing.
    """
    time.sleep(0.5) # Simulate LLM processing time
    question_lower = question.lower()
    if "hello" in question_lower:
        return "Hello there! How can I assist you today?"
    elif "docker" in question_lower:
        return "Docker is a platform for developing, shipping, and running applications in containers."
    elif "microservices" in question_lower:
        return "Microservices are an architectural style that structures an application as a collection of loosely coupled services."
    elif "what is my name" in question_lower:
        return "I do not have access to your personal information, so I don't know your name."
    elif "long task" in question_lower:
        time.sleep(2) # Simulate a longer task
        return "This was a long task, but I completed it!"
    else:
        return f"I received your question: '{question}'. This is a mock response."