import os
from openai import OpenAI
from dotenv import load_dotenv

def get_ai_response(prompt: str, model: str = "gpt-4o-mini") -> str:
    """
    Get a response from OpenAI's API based on the given prompt.
    
    Args:
        prompt (str): The input prompt to send to the AI
        model (str, optional): The OpenAI model to use. Defaults to "gpt-5-nano".
        
    Returns:
        str: The AI's generated response
        
    Raises:
        ValueError: If the OpenAI API key is not found in environment variables
        Exception: For any errors that occur during the API call
    """
    # Load environment variables from .env file
    load_dotenv()
    
    # Get the API key and other environment variables
    api_key = os.getenv("OPENAI_API_KEY")
    prompt_base = os.getenv("PROMPT_BASE", "")
    governance_base = os.getenv("GOVERNANCE_BASE", "")
    
    if not api_key:
        raise ValueError("OpenAI API key not found in environment variables")
    
    # Combine the base prompt, governance rules, and user prompt
    full_prompt = f"{prompt_base}\n\n{governance_base}\n\nUser prompt: {prompt}"
    
    try:
        # Initialize the OpenAI client
        client = OpenAI(api_key=api_key)
        
        # Debug print for the request
        print("\n=== OpenAI API Request ===")
        print(f"Model: {model}")
        print("Messages:")
        print(f"- role: system\n  content: {prompt_base}")
        print(f"- role: system\n  content: {governance_base}")
        print(f"- role: user\n  content: {prompt}")
        print("=========================\n")
        
        # Make the API call with the combined prompt
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "name": "prompt", "content": prompt_base},
                {"role": "system", "name": "governance", "content": governance_base},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Debug print for the response
        print("\n=== OpenAI API Response ===")
        print(f"Status: {response.choices[0].finish_reason}")
        print(f"Response: {response.choices[0].message.content}")
        print("==========================\n")
        
        # Return the generated text
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        # Re-raise any exceptions with a descriptive message
        raise Exception(f"Error calling OpenAI API: {str(e)}")


# Example usage
if __name__ == "__main__":
    try:
        test_prompt = "Tell me a short joke about artificial intelligence."
        response = get_ai_response(test_prompt)
        print(f"Prompt: {test_prompt}")
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")