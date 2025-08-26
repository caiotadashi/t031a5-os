import sys
import os
import json
import threading
from typing import Optional, Callable
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import necessary modules
from inputs.chatgpt_asr import transcribe_speech, set_stop_recording
from llm.openai_client import get_ai_response
from speak.elevenlabs_client import get_elevenlabs_client
from movements.unitree_g1 import UnitreeG1Movement
from leds.leds_g1 import UnitreeG1LEDs

# Global flag to control the main loop
should_exit = False

# Initialize the movement handler
movement_handler = UnitreeG1Movement("eth0")

# Initialize LED controller
led_controller = UnitreeG1LEDs("eth0")
led_controller.set_preset_color("cyan")

def signal_handler(sig, frame):
    global should_exit
    if not should_exit:
        print("\nStopping the system... (press Ctrl+C again to force exit)")
        should_exit = True
        set_stop_recording()
    else:
        print("\nForcefully exiting...")
        sys.exit(1)

def process_speech_input(text: str) -> None:
    """Process a single speech input and generate response with movement if needed."""
    if not text or should_exit:
        return
        
    print(f"You said: {text}")
    
    try:
        # Process with OpenAI
        print("Processing with OpenAI...")
        ai_response = get_ai_response(text)
        print(f"AI Response: {ai_response}")
        
        # Extract JSON from the response if it's wrapped in ```json ```
        try:
            if '```json' in ai_response:
                # Extract the JSON part between ```json and the next ```
                json_start = ai_response.find('```json') + 7
                json_end = ai_response.find('```', json_start)
                json_str = ai_response[json_start:json_end].strip()
            else:
                # If not wrapped in ```json, try to parse the whole response
                json_str = ai_response
                
            # Parse the JSON response
            response_data = json.loads(json_str)
            chat_response = response_data.get('chat-response', 'No response content found')
            movement = response_data.get('movement')
            print(f"Extracted chat response: {chat_response}")
        
            # Initialize elevenlabs client
            client = get_elevenlabs_client()
        
            # Start movement in a separate thread if specified
            movement_thread = None
            if movement:
                print(f"Executing movement: {movement}")
                movement_thread = threading.Thread(
                    target=movement_handler.execute_movement,
                    args=(movement,)
                )
                movement_thread.daemon = True
                movement_thread.start()
        
            # Convert response to speech and play
            print("Converting response to speech...")
            audio_data = client.text_to_speech(
                text=chat_response,
                voice_id=os.getenv("ELEVENLABS_VOICE_ID", "1eBtZhneFpMPiYsjVTGl"),
                model_id="eleven_flash_v2_5"
            )
        
            # Play the audio
            client.play_audio(audio_data)
            print("Response played successfully!")
        
            # Wait for movement to complete if it's still running
            if movement_thread and movement_thread.is_alive():
                movement_thread.join()
            
        except json.JSONDecodeError:
            print("Error: Failed to parse AI response as JSON")
    except Exception as e:
        print(f"Error processing speech input: {e}")

def main():
    """Main entry point for the cortex module."""
    import signal
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Load environment variables
    load_dotenv()
    
    print("Cortex system initialized. Press Ctrl+C to exit.")
    
    try:
        while not should_exit:
            # Release arm to default position
            print("Releasing arm to default position...")
            movement_handler.execute_movement("release_arm")
            
            # Listen for speech
            print("\nListening for speech input... (press Ctrl+C to exit)")
            
            # Get transcription from the generator
            for transcript, _ in transcribe_speech():
                if transcript and not should_exit:
                    process_speech_input(transcript)
                break  # Process only the first transcription
                
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error in main loop: {e}")
    finally:
        # Clean up
        movement_handler.cleanup()
        print("Cortex system shutdown complete.")

if __name__ == "__main__":
    main()