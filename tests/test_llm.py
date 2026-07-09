from app.llm.client import LLMClient

def test_generate_returns_string():
    llm_client = LLMClient()
    
    response = llm_client.generate("Hello, Sentinal AI!")
    
    assert isinstance(response, str)