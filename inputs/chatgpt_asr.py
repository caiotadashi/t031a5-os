import os
import sys
import time
import threading
import wave
import webrtcvad
import tempfile
from dotenv import load_dotenv
import pyaudio
import numpy as np
from openai import OpenAI
from ctypes import *
from contextlib import contextmanager
from leds.leds_g1 import UnitreeG1LEDs

# Initialize LED controller
led_controller = UnitreeG1LEDs("eth0")
led_controller.set_preset_color("cyan")  # Default state

# Global flag to control recording
should_stop_recording = False

def set_stop_recording():
    global should_stop_recording
    should_stop_recording = True
    led_controller.set_preset_color("cyan")  # Turn off LED when stopping

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

def get_supported_sample_rates(audio_interface, device_index, channels=1):
    """Get a list of supported sample rates for the given audio device."""
    supported_rates = []
    test_rates = [8000, 11025, 16000, 22050, 24000, 32000, 44100, 48000, 96000]
    
    for rate in test_rates:
        try:
            test_stream = audio_interface.open(
                format=pyaudio.paInt16,
                channels=channels,
                rate=rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=1024,
                start=False
            )
            test_stream.close()
            supported_rates.append(rate)
        except:
            continue
            
    return supported_rates

def record_audio(audio_interface, device_index, preferred_rate=16000, channels=1, silence_limit=1.0):
    """Record audio using VAD to detect speech and silence."""
    global should_stop_recording
    
    # Set LED to green when starting to listen
    led_controller.set_preset_color("green")
    print("Changing LED to green")
    
    vad = webrtcvad.Vad(3)  # Most aggressive filtering
    frames = []
    silence_frames = 0
    
    stream = None
    spinner = None
    sample_rate = preferred_rate
    
    try:
        # Get device info and supported rates
        device_info = audio_interface.get_device_info_by_index(device_index)
        print(f"\nUsing audio device: {device_info['name']}")
        
        # Get supported sample rates
        supported_rates = get_supported_sample_rates(audio_interface, device_index, channels)
        if not supported_rates:
            print("Could not determine supported sample rates. Trying default...")
            supported_rates = [int(device_info.get('defaultSampleRate', 44100))]
        
        # Find the best matching sample rate
        if preferred_rate not in supported_rates:
            print(f"Preferred rate {preferred_rate}Hz not supported. Supported rates: {supported_rates}")
            # Try to find the closest supported rate
            sample_rate = min(supported_rates, key=lambda x: abs(x - preferred_rate))
            print(f"Using closest supported rate: {sample_rate}Hz")
        
        silence_threshold = int(silence_limit * (sample_rate / 160))  # 10ms frames
        
        # Open the stream with the determined sample rate
        stream = audio_interface.open(
            format=pyaudio.paInt16,
            channels=channels,
            rate=sample_rate,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=int(sample_rate * 0.01),  # 10ms chunks
            start=False
        )
        
        print("\nListening... (speak now, press Ctrl+C to cancel)")
        spinner = Spinner("Recording")
        spinner.start()
        
        stream.start_stream()
        while not should_stop_recording:
            try:
                frame = stream.read(int(sample_rate * 0.01), exception_on_overflow=False)
                if should_stop_recording:
                    break
                    
                is_speech = vad.is_speech(frame, sample_rate)
                
                if is_speech:
                    frames.append(frame)
                    silence_frames = 0
                elif frames:  # Only count silence after speech has started
                    frames.append(frame)
                    silence_frames += 1
                    if silence_frames > silence_threshold:
                        break
                
            except IOError as e:
                print(f"\nError reading audio: {e}")
                break
                
    except Exception as e:
        print(f"\nError in recording: {e}")
        return None, None
        
    finally:
        if spinner:
            spinner.stop()
        if stream:
            try:
                stream.stop_stream()
                stream.close()
            except:
                pass
        # Set LED back to cyan after recording
        led_controller.set_preset_color("cyan")
        print("Changing LED to cyan")
    
    if not frames:
        return None, None
        
    return b''.join(frames), sample_rate

def save_audio_to_temp(audio_data, sample_rate, channels=2):
    """Save audio data to a temporary WAV file."""
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        with wave.open(f.name, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(sample_rate)
            wf.writeframes(audio_data)
        return f.name
    return None

def transcribe_audio(api_key, audio_file_path):
    """Transcribe the given audio file using OpenAI's Whisper API and get a response with context."""
    try:
        client = OpenAI(api_key=api_key)
        
        # Get prompts from environment variables
        prompt_base = os.getenv("PROMPT_BASE", "")
        governance_base = os.getenv("GOVERNANCE_BASE", "")
        
        # First, transcribe the audio to text
        with open(audio_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
        
        if not transcript:
            return None, None
            
        transcript = transcript.strip()
        
        # If we have prompts, get a contextual response
        if prompt_base or governance_base:
            # Combine the base prompt, governance rules, and user's transcribed text
            full_prompt = f"""{prompt_base}
            
            {governance_base}
            
            User said: {transcript}"""
            
            # Get response from the chat model
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": full_prompt}
                ]
            )
            
            # Extract the response text
            response_text = response.choices[0].message.content.strip()
            return transcript, response_text
            
        return transcript, None
        
    except Exception as e:
        print(f"Error in transcription/processing: {e}")
        return None, None

def find_audio_device(audio_interface, device_name=None):
    """Find an audio input device by name or return default."""
    default_device = None
    for i in range(audio_interface.get_device_count()):
        dev_info = audio_interface.get_device_info_by_index(i)
        if dev_info['maxInputChannels'] > 0:  # It's an input device
            if device_name and device_name.lower() in dev_info['name'].lower():
                print(f"Found matching device: {dev_info['name']}")
                return i
            if default_device is None:
                default_device = i
    return default_device

def suppress_alsa_warnings():
    """Suppress ALSA debug messages by redirecting stderr."""
    @contextmanager
    def stderr_redirected():
        # Save the original stderr file descriptor
        stderr_fd = 2  # stderr is file descriptor 2
        new_stderr = os.open(os.devnull, os.O_WRONLY)
        old_stderr = os.dup(stderr_fd)
        try:
            # Replace stderr with /dev/null
            os.dup2(new_stderr, stderr_fd)
            yield
        finally:
            # Restore the original stderr
            os.dup2(old_stderr, stderr_fd)
            os.close(old_stderr)
            os.close(new_stderr)
    
    return stderr_redirected()

def transcribe_speech():
    """Record a single audio utterance and transcribe it using OpenAI's Whisper API."""
    load_dotenv()
    
    # Get API key from environment variables
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found in environment variables")
        led_controller.set_preset_color("red")  # Error state
        yield None, None
        return
    
    # Initialize audio interface with suppressed ALSA messages
    with suppress_alsa_warnings():
        audio_interface = pyaudio.PyAudio()
    
    try:
        # Try to find the audio device
        device_index = find_audio_device(audio_interface, 'DJI MIC')
        if device_index is None:
            print("No audio input device found")
            led_controller.set_preset_color("red")  # Error state
            audio_interface.terminate()
            yield None, None
            return
        
        # Get device info and supported rates
        device_info = audio_interface.get_device_info_by_index(device_index)
        supported_rates = get_supported_sample_rates(audio_interface, device_index, 1)
        
        if not supported_rates:
            print("Could not determine supported sample rates. Using default...")
            supported_rates = [int(device_info.get('defaultSampleRate', 48000))]
        
        # Use the highest supported sample rate for best quality
        sample_rate = max(supported_rates)
        print(f"Using sample rate: {sample_rate}Hz")
        
        while True:
            try:
                # Record audio with the determined sample rate
                audio_data, actual_sample_rate = record_audio(
                    audio_interface, 
                    device_index,
                    preferred_rate=sample_rate,
                    channels=1
                )
                
                if not audio_data:
                    print("No speech detected. Try again...")
                    continue
                
                # Save to temp file with the actual sample rate used
                temp_audio_file = save_audio_to_temp(audio_data, actual_sample_rate, 1)
                if not temp_audio_file:
                    print("Error saving audio to file")
                    continue
                
                try:
                    # Set LED to yellow while processing
                    led_controller.set_preset_color("yellow")
                    print("Changing LED to yellow")
                    
                    # Transcribe using OpenAI's Whisper API
                    print("\nTranscribing...")
                    transcript, response = transcribe_audio(api_key, temp_audio_file)
                    
                    if transcript:
                        yield transcript, response
                    else:
                        print("No transcription returned. Try again...")
                        
                except Exception as e:
                    print(f"Error during transcription: {e}")
                    led_controller.set_preset_color("red")  # Error state
                    print("Changing LED to red")
                    time.sleep(1)  # Show error state briefly
                    raise  # Re-raise the exception to be caught by the outer try-except
                    
                finally:
                    # Set LED back to cyan after processing
                    led_controller.set_preset_color("cyan")
                    print("Changing LED to cyan")
                    
                    # Clean up temp file
                    try:
                        os.unlink(temp_audio_file)
                    except:
                        pass
                    
            except KeyboardInterrupt:
                print("\nStopping...")
                break
            except Exception as e:
                print(f"Error: {e}")
                led_controller.set_preset_color("red")  # Error state
                print("Changing LED to red")
                time.sleep(1)  # Show error state briefly
                led_controller.set_preset_color("cyan")  # Return to default
                print("Changing LED to cyan")
                
    finally:
        # Clean up
        audio_interface.terminate()
        led_controller.set_preset_color("cyan")  
        print("Changing LED to cyan")

def main():
    # Load environment variables first
    load_dotenv()
    
    print("Starting ChatGPT-based speech recognition. Press Ctrl+C to stop.")
    
    # Initialize audio interface with suppressed ALSA messages
    with suppress_alsa_warnings():
        audio_interface = pyaudio.PyAudio()
    
    try:
        # Get API key from environment variables
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("Error: OPENAI_API_KEY not found in environment variables")
            print("Please make sure you have a .env file with OPENAI_API_KEY=your_key_here")
            led_controller.set_preset_color("red")  # Error state
            return
        
        # Try to find the audio device
        device_index = find_audio_device(audio_interface, 'DJI MIC')
        if device_index is None:
            print("No audio input device found")
            led_controller.set_preset_color("red")  # Error state
            print("Changing LED to red")
            return
        
        # Get device info
        device_info = audio_interface.get_device_info_by_index(device_index)
        print(f"Using audio device: {device_info['name']}")
        
        # Get supported sample rates
        supported_rates = get_supported_sample_rates(audio_interface, device_index, 1)
        print(f"Supported sample rates: {supported_rates}")
        
        # Start the main loop
        for transcript, response in transcribe_speech():
            if transcript:
                print(f"\nYou said: {transcript}")
                if response:
                    print("\nResponse:")
                    # Try to find a JSON object in the response
                    try:
                        import json
                        import re
                        
                        # First, try to parse the entire response as JSON
                        try:
                            parsed = json.loads(response)
                            if isinstance(parsed, dict):
                                # If it's a JSON object, print the chat response if it exists
                                if "chat-response" in parsed:
                                    print(parsed["chat-response"])
                                # Print the structured data
                                print("\nAction Data:")
                                print(json.dumps(parsed, indent=2, ensure_ascii=False))
                                continue
                        except json.JSONDecodeError:
                            pass  # Not a pure JSON response, try pattern matching
                        
                        # If we get here, try to find a JSON object in the response
                        json_match = re.search(r'\{.*\}', response, re.DOTALL)
                        if json_match:
                            # Print the natural language part (everything before the JSON)
                            print(response[:json_match.start()].strip())
                            # Parse and pretty print the JSON part
                            json_str = json_match.group(0)
                            try:
                                parsed = json.loads(json_str)
                                print("\nAction Data:")
                                print(json.dumps(parsed, indent=2, ensure_ascii=False))
                            except json.JSONDecodeError as e:
                                print(f"\nCould not parse JSON: {e}")
                                print(f"JSON string: {json_str}")
                        else:
                            print(response)
                    except Exception as e:
                        print(f"Error parsing response: {e}")
                        print(response)
    
    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        audio_interface.terminate()
        led_controller.set_preset_color("cyan") 
        print("Changing LED to cyan")
    
    print("Goodbye!")

if __name__ == "__main__":
    main()
