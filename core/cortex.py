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
interaction_active = False
interaction_thread = None

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

def start_interaction():
    """Start the interaction mode."""
    global interaction_active, interaction_thread
    
    if interaction_active:
        return {'status': 'already_running', 'message': 'Interaction is already active'}
    
    interaction_active = True
    
    # Create and start interaction thread
    interaction_thread = threading.Thread(target=interaction_loop, daemon=True)
    interaction_thread.start()
    
    return {'status': 'started', 'message': 'Interaction started successfully'}

def stop_interaction():
    """Stop the interaction mode."""
    global interaction_active, interaction_thread, should_exit
    
    if not interaction_active:
        return {'status': 'not_running', 'message': 'Interaction is not active'}
    
    print("Stopping interaction...")
    
    # Signal the interaction loop to stop
    interaction_active = False
    should_exit = True
    set_stop_recording()
    
    # Wait for the thread to finish with a timeout
    if interaction_thread and interaction_thread.is_alive():
        print("Waiting for interaction thread to stop...")
        interaction_thread.join(timeout=3.0)
        
        # If thread is still alive after timeout, it's likely stuck
        if interaction_thread.is_alive():
            print("Warning: Interaction thread did not stop gracefully")
    
    # Reset state
    interaction_thread = None
    should_exit = False
    
    # Reset LED to indicate system is idle
    led_controller.set_preset_color("cyan")
    
    print("Interaction stopped successfully")
    return {'status': 'stopped', 'message': 'Interaction stopped successfully'}

def get_interaction_status():
    """Get the current interaction status."""
    return {
        'is_interacting': interaction_active,
        'status': 'active' if interaction_active else 'inactive'
    }

def interaction_loop():
    """Main interaction loop that processes speech input."""
    global should_exit
    
    print("Interaction loop started")
    
    while not should_exit and interaction_active:
        try:
            for transcript, _ in transcribe_speech():
                if transcript and interaction_active:  # Check if still active
                    process_speech_input(transcript)
                
                # Check if we should exit after processing each transcript
                if should_exit or not interaction_active:
                    break
                    
        except Exception as e:
            print(f"Error in interaction loop: {e}")
            # Small delay to prevent tight loop on errors
            import time
            time.sleep(1)
    
    print("Interaction loop stopped")

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
    global should_exit, interaction_active
    
    # Load environment variables
    load_dotenv()
    
    # Set up signal handler
    import signal
    signal.signal(signal.SIGINT, signal_handler)
    
    print("Cortex system initialized. Press Ctrl+C to exit.")
    
    # Start in non-interactive mode by default
    # The web interface will control when to start/stop interaction
    while not should_exit:
        try:
            # Just sleep and keep the process alive
            # The web interface will control the interaction
            import time
            time.sleep(1)
            
        except KeyboardInterrupt:
            signal_handler(signal.SIGINT, None)
    
    # Clean up
    movement_handler.cleanup()
    led_controller.set_preset_color("off")
    print("Cortex system shutdown complete.")

if __name__ == "__main__":
    main()