import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inputs.googleasr import transcribe_speech

def get_speech_input():
    """
    Get speech input from the user.
    Returns:
        str: The transcribed text or None if no speech was detected.
    """
    try:
        # Get the first transcription from the generator
        for text in transcribe_speech():
            if text:
                return text
        return None
    except Exception as e:
        print(f"Error in speech recognition: {e}")
        return None

def listen_continuously(callback):
    """
    Continuously listen for speech and call the callback with each transcription.
    Args:
        callback: A function that takes a string (the transcribed text) as an argument.
    """
    try:
        for text in transcribe_speech():
            if text:
                callback(text)
    except KeyboardInterrupt:
        print("\nStopping continuous listening...")
    except Exception as e:
        print(f"Error in continuous listening: {e}")

def main():
    """Main function for testing speech recognition."""
    print("Starting speech recognition. Press Ctrl+C to stop.")
    listen_continuously(lambda text: print(f"You said: {text}"))

if __name__ == "__main__":
    main()
