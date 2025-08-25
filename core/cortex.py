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
from movements.unitree_g1 import UnitreeG1Movement

# Global flag to control the main loop
should_exit = False

# Initialize the movement handler
movement_handler = UnitreeG1Movement("eth0")

def signal_handler(sig, frame):
    global should_exit
    if not should_exit:
        print("\nStopping the system... (press Ctrl+C again to force exit)")
        should_exit = True
    else:
        print("\nForcefully exiting...")
        sys.exit(1)

def process_conversation() -> None:
    """
    Handle one iteration of the conversation flow.
    """
    global should_exit
    
    if should_exit:
        return False
        
    try:
        # Step 1: Get speech input
        print("\nListening for speech input... (press Ctrl+C to exit)")
        
        # Define a callback to handle each speech input
        def handle_speech(user_input: str) -> None:
            if not user_input or should_exit:
                return
                
            print(f"You said: {user_input}")
            
            # Step 2: Process with OpenAI
            print("Processing with OpenAI...")
            ai_response = get_ai_response(user_input)
            print(f"AI Response: {ai_response}")
            
# Then, in the handle_speech function, replace the JSON parsing section with:
            # Parse the JSON response
            try:
                import json
                response_data = json.loads(ai_response)
                chat_response = response_data.get('chat-response', 'No response content found')
                movement = response_data.get('movement')
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
            
            try:
                # Execute movement if specified in the response
                if movement:
                    print(f"Executing movement: {movement}")
                    movement_handler.execute_movement(movement)
            except json.JSONDecodeError:
                print("Warning: No movement")

            # Play the audio
            client.play_audio(audio_data)
            print("Response played successfully!")
        
        # Start continuous listening with our handler
        listen_continuously(handle_speech)
        return True
        
    except KeyboardInterrupt:
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return True

def main() -> None:
    """Main entry point for the cortex module."""
    import signal
    
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    load_dotenv()
    
    print("=== Sistema de Conversação Tobias ===")
    print("Pressione Ctrl+C para encerrar.\n")
    
    try:
        while not should_exit:
            if not process_conversation():
                break
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        print("\nEncerrando o sistema...")
        sys.exit(0)

if __name__ == "__main__":
    main()