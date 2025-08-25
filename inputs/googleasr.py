import os
import sys
import time
import threading
from dotenv import load_dotenv
import pyaudio
from google.cloud import speech

class Spinner:
    def __init__(self, message=""):
        self.busy = False
        self.delay = 0.1
        self.message = message
        self.spinner_generator = self.spinning_cursor()
        self.spinner_thread = None
        self._stop_event = threading.Event()

    @staticmethod
    def spinning_cursor():
        while True:
            for cursor in '|/-\\':
                yield cursor

    def spinner_task(self):
        while not self._stop_event.is_set():
            sys.stdout.write(f"\r{self.message} {next(self.spinner_generator)}")
            sys.stdout.flush()
            time.sleep(self.delay)
        sys.stdout.write('\r' + ' ' * (len(self.message) + 2) + '\r')
        sys.stdout.flush()

    def start(self):
        if not self.busy:
            self.busy = True
            self._stop_event.clear()
            self.spinner_thread = threading.Thread(target=self.spinner_task)
            self.spinner_thread.daemon = True
            self.spinner_thread.start()

    def stop(self):
        if self.busy:
            self.busy = False
            self._stop_event.set()
            if (self.spinner_thread and 
                self.spinner_thread.is_alive() and 
                self.spinner_thread != threading.current_thread()):
                self.spinner_thread.join(timeout=0.5)

def transcribe_speech():
    """
    Continuously captures speech from the microphone and yields transcribed text.
    """
    load_dotenv()
    RATE = 16000
    CHUNK = 1024  # Smaller chunk size
    
    # Initialize PyAudio
    audio_interface = pyaudio.PyAudio()
    
    # Configure Google Cloud client
    client = speech.SpeechClient()
    
    # Configure recognition
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code="pt-BR",
        enable_automatic_punctuation=True,
        model="latest_long",  
        use_enhanced=True,
    )

    streaming_config = speech.StreamingRecognitionConfig(
        config=config,
        interim_results=True,
        single_utterance=False
    )

    # Open microphone stream
    stream = audio_interface.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK,
        start=True
    )

    def request_generator():
        try:
            while True:
                data = stream.read(CHUNK, exception_on_overflow=False)
                if not data:
                    break
                yield speech.StreamingRecognizeRequest(audio_content=data)
        except Exception as e:
            print(f"\nError in audio stream: {e}")
            raise

    spinner = Spinner("🎤 Waiting for speech...")
    spinner.start()
    
    try:
        # Start the streaming recognize
        requests = request_generator()
        responses = client.streaming_recognize(streaming_config, requests, timeout=300)
        
        # Process responses
        for response in responses:
            if not response.results:
                continue
                
            result = response.results[0]
            if not result.alternatives:
                continue
                
            transcript = result.alternatives[0].transcript.strip()
            
            if result.is_final and transcript:
                spinner.stop()
                yield transcript
                spinner = Spinner("🎤 Waiting for speech...")
                spinner.start()
                
    except Exception as e:
        print(f"\nError in speech recognition: {e}")
    finally:
        spinner.stop()
        stream.stop_stream()
        stream.close()
        audio_interface.terminate()

if __name__ == "__main__":
    print("Starting continuous speech recognition. Press Ctrl+C to stop.")
    try:
        for text in transcribe_speech():
            if text:
                print(f"\nYou said: {text}")
    except KeyboardInterrupt:
        print("\nStopping speech recognition...")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        print("Speech recognition stopped.")
