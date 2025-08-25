import sys
import os
from typing import Optional, Callable
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import necessary modules
from core.nldb import listen_continuously
from llm.openai_client import get_ai_response
from speak.elevenlabs_client import get_elevenlabs_client

def process_conversation() -> None:
    """
    Handle one iteration of the conversation flow.
    """
    try:
        # Step 1: Get speech input
        print("\nListening for speech input... (press Ctrl+C to exit)")
        
        # Define a callback to handle each speech input
        def handle_speech(user_input: str) -> None:
            if not user_input:
                print("No speech detected or an error occurred during speech recognition.")
                return
                
            print(f"You said: {user_input}")
            
            # Step 2: Process with OpenAI
            print("Processing with OpenAI...")
            ai_response = get_ai_response(user_input)
            print(f"AI Response: {ai_response}")
            
            # Parse the JSON response
            try:
                import json
                response_data = json.loads(ai_response)
                chat_response = response_data.get('chat-response', 'No response content found')
                print(f"Extracted chat response: {chat_response}")
            except json.JSONDecodeError:
                print("Warning: Response is not valid JSON, using full response as is")
                chat_response = ai_response
            
            # Step 3: Convert response to speech
            print("Converting response to speech...")
            client = get_elevenlabs_client()
            
            # Get audio data
            audio_data = client.text_to_speech(
                text=chat_response,
                voice_id=os.getenv("ELEVENLABS_VOICE_ID", "1eBtZhneFpMPiYsjVTGl"),  # Default voice ID (Eduardo Hubi)
                model_id="eleven_flash_v2_5"
            )
            
            # Play the audio
            client.play_audio(audio_data)
            print("Response played successfully!")
        
        # Start continuous listening with our handler
        listen_continuously(handle_speech)
        
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        raise
    except Exception as e:
        print(f"An error occurred: {e}")

def main() -> None:
    """Main entry point for the cortex module."""
    load_dotenv()
    
    print("=== Sistema de Conversação Tobias ===")
    print("Pressione Ctrl+C para encerrar.\n")
    
    try:
        while True:
            process_conversation()
    except KeyboardInterrupt:
        print("\nEncerrando o sistema...")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        print("\nEncerrando o sistema...")

if __name__ == "__main__":
    main()