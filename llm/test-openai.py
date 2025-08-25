import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai_client import get_ai_response

def test_ai_response():
    """
    Test function that calls get_ai_response with a predefined prompt.
    Prints the AI's response or any errors that occur.
    """
    # Define the prompt as a variable
    prompt = "Explain the concept of artificial intelligence in one sentence."
    
    try:
        # Call the OpenAI API function
        response = get_ai_response(prompt)
        
        # Print the results
        print("--- AI Response Test ---")
        print(f"Prompt: {prompt}")
        print(f"Response: {response}")
        print("-----------------------")
        
        return response
        
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# Run the test function if this script is executed directly
if __name__ == "__main__":
    test_ai_response()