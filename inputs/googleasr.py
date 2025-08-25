import os
import sys
import time
import threading
import wave
import webrtcvad
import tempfile
from dotenv import load_dotenv
import pyaudio
from google.cloud import speech
import numpy as np

# Global flag to control recording
should_stop_recording = False

def set_stop_recording():
    global should_stop_recording
    should_stop_recording = True

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

def record_audio(audio_interface, device_index, sample_rate, channels=2, silence_limit=1.0):
    """Record audio using VAD to detect speech and silence."""
    global should_stop_recording
    should_stop_recording = False
    
    vad = webrtcvad.Vad(3)  # Most aggressive filtering
    frames = []
    silence_frames = 0
    silence_threshold = int(silence_limit * (sample_rate / 160))  # 10ms frames
    
    stream = None
    try:
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
                if e.errno == -9981:  # Input overflowed, skip this frame
                    continue
                raise
            except Exception as e:
                if not should_stop_recording:  # Only log if we didn't request stop
                    print(f"\nError during recording: {e}")
                break
                
        spinner.stop()
        
    except KeyboardInterrupt:
        print("\nRecording cancelled by user")
        return None
    except Exception as e:
        print(f"\nError during recording setup: {e}")
        return None
    finally:
        if stream is not None:
            try:
                stream.stop_stream()
                stream.close()
            except:
                pass
    
    if not frames or should_stop_recording:
        if should_stop_recording:
            print("\nRecording stopped by user")
        else:
            print("No speech detected")
        return None
        
    return b''.join(frames)

def save_audio_to_temp(audio_data, sample_rate, channels=2):
    """Save audio data to a temporary WAV file."""
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        with wave.open(f.name, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(2)  # 16-bit audio
            wf.setframerate(sample_rate)
            wf.writeframes(audio_data)
        return f.name

def transcribe_file(speech_client, config, file_path):
    """Transcribe the given audio file using Google Speech-to-Text."""
    with open(file_path, 'rb') as audio_file:
        content = audio_file.read()
    
    audio = speech.RecognitionAudio(content=content)
    response = speech_client.recognize(config=config, audio=audio)
    
    for result in response.results:
        yield result.alternatives[0].transcript

def find_audio_device(audio_interface, device_name='DJI MIC'):
    """Find an audio input device by name."""
    print("\nSearching for audio devices...")
    for i in range(audio_interface.get_device_count()):
        try:
            dev = audio_interface.get_device_info_by_index(i)
            print(f"Device {i}: {dev['name']} (Input channels: {dev['maxInputChannels']}, Default Sample Rate: {dev['defaultSampleRate']})")
            if device_name.lower() in dev['name'].lower() and dev['maxInputChannels'] > 0:
                print(f"\nFound {device_name} at device index {i}")
                print(f"Device details: {dev}")
                return i, dev
        except Exception as e:
            print(f"Error checking device {i}: {e}")
    
    # If preferred device not found, try to find any available input device
    print("\nPreferred device not found. Searching for any available input device...")
    for i in range(audio_interface.get_device_count()):
        try:
            dev = audio_interface.get_device_info_by_index(i)
            if dev['maxInputChannels'] > 0:
                print(f"\nUsing available input device: {dev['name']} (index {i})")
                print(f"Device details: {dev}")
                return i, dev
        except:
            continue
    
    return None, None

def transcribe_speech():
    """Record a single audio utterance and transcribe it using Google Speech-to-Text.
    
    Yields:
        str: The transcribed text if successful, or None if no speech was detected.
    """
    load_dotenv()
    
    # Initialize PyAudio
    audio_interface = pyaudio.PyAudio()
    
    try:
        # Find audio device
        dji_device_index, dji_device = find_audio_device(audio_interface)
                
        if dji_device_index is None:
            print("\nError: No suitable audio input device found!")
            print("Please check your audio devices and make sure a microphone is connected.")
            return
            
        # Configure Google Cloud client
        client = speech.SpeechClient()
        
        # Configure recognition
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=int(dji_device['defaultSampleRate']),
            language_code="pt-BR",
            enable_automatic_punctuation=True,
            model="latest_long",
            use_enhanced=True,
            audio_channel_count=min(2, dji_device['maxInputChannels']),
            enable_separate_recognition_per_channel=False
        )
        
        # Record audio with VAD (single utterance)
        audio_data = record_audio(
            audio_interface=audio_interface,
            device_index=dji_device_index,
            sample_rate=int(dji_device['defaultSampleRate']),
            channels=min(2, dji_device['maxInputChannels'])
        )
        
        if not audio_data:
            yield None
            return
            
        # Save to temporary file
        temp_file = save_audio_to_temp(
            audio_data=audio_data,
            sample_rate=int(dji_device['defaultSampleRate']),
            channels=min(2, dji_device['maxInputChannels'])
        )
        
        # Transcribe the file and yield results
        try:
            for transcript in transcribe_file(client, config, temp_file):
                yield transcript
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_file)
            except:
                pass
                
    except Exception as e:
        print(f"\nError in speech recognition: {e}")
        yield None
    finally:
        audio_interface.terminate()

if __name__ == "__main__":
    print("Starting speech recognition. Press Ctrl+C to stop.")
    try:
        for text in transcribe_speech():
            print(f"\nTranscription: {text}")
    except KeyboardInterrupt:
        set_stop_recording()
        print("\nStopped by user")
