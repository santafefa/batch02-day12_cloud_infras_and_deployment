# d:\VIN\batch02-day12_cloud_infras_and_deployment\06-lab-complete\utils\mock_llm.py

def ask(question: str) -> str:
    """
    A mock LLM function that returns a canned response based on the question.
    """
    question = question.lower()
    if "hello" in question:
        return "Hello there! How can I assist you today?"
    elif "deployment" in question:
        return "Deployment is the process of getting an application ready for use."
    elif "docker" in question:
        return "Docker is a platform for developing, shipping, and running applications in containers."
    elif "microservices" in question:
        return "Microservices is an architectural style that structures an application as a collection of loosely coupled services."
    elif "jwt" in question:
        return "JWT (JSON Web Token) is a compact, URL-safe means of representing claims to be transferred between two parties."
    elif "alice" in question:
        return "Your name is Alice, if I recall correctly!"
    else:
        return f"This is a mock response to your question: '{question}'. I'm not a real LLM yet!"
