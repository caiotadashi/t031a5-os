import os
import requests
from typing import Optional, Union, BinaryIO
from dotenv import load_dotenv

class ElevenLabsClient:
    """
    A client for interacting with the ElevenLabs API for speech-to-text and text-to-speech.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the ElevenLabs client.
        
        Args:
            api_key (str, optional): Your ElevenLabs API key. If not provided, will try to load from ELEVENLABS_API_KEY environment variable.
        """
        load_dotenv()
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        self.base_url = "https://api.elevenlabs.io/v1"
        
        if not self.api_key:
            raise ValueError("ElevenLabs API key not found. Please set ELEVENLABS_API_KEY in your environment variables.")
    
    def text_to_speech(
        self,
        text: str,
        voice_id: str = "1eBtZhneFpMPiYsjVTGl",  # Default voice ID (Eduardo Hubi)
        model_id: str = "eleven_flash_v2_5",
        stability: float = 0.5,
        similarity_boost: float = 0.75,
        style: float = 0.0,
        speaker_boost: bool = True
    ) -> bytes:
        """
        Convert text to speech using ElevenLabs API.
        
        Args:
            text (str): The text to convert to speech
            voice_id (str): The ID of the voice to use
            model_id (str): The ID of the model to use
            stability (float): Stability parameter (0.0 to 1.0)
            similarity_boost (float): Similarity boost parameter (0.0 to 1.0)
            style (float): Style parameter (0.0 to 1.0)
            speaker_boost (bool): Whether to use speaker boost
            
        Returns:
            bytes: The audio data in MP3 format
            
        Raises:
            Exception: If the API request fails
        """
        url = f"{self.base_url}/text-to-speech/{voice_id}"
        
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        data = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
                "style": style,
                "speaker_boost": speaker_boost
            }
        }
        
        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error in ElevenLabs API request: {str(e)}")
    
    def speech_to_text(
        self,
        audio_data: Union[bytes, str, BinaryIO],
        model_id: str = "eleven_monolingual_v1"
    ) -> str:
        """
        Convert speech to text using ElevenLabs API.
        
        Args:
            audio_data: The audio data to transcribe. Can be:
                       - bytes: Raw audio data
                       - str: Path to audio file
                       - BinaryIO: File-like object containing audio data
            model_id (str): The ID of the model to use
            
        Returns:
            str: The transcribed text
            
        Raises:
            Exception: If the API request fails
        """
        url = f"{self.base_url}/speech-to-text"
        
        headers = {
            "xi-api-key": self.api_key
        }
        
        files = {
            'file': audio_data if isinstance(audio_data, (str, BinaryIO)) else ('audio.mp3', audio_data, 'audio/mpeg')
        }
        
        params = {
            'model_id': model_id
        }
        
        try:
            response = requests.post(url, headers=headers, files=files, params=params)
            response.raise_for_status()
            return response.json().get('text', '')
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error in ElevenLabs API request: {str(e)}")

    def play_audio(self, audio_data: bytes) -> None:
        """
        Play audio data using the system's default audio player.
        
        Args:
            audio_data (bytes): The audio data to play (MP3 format)
            
        Raises:
            Exception: If audio playback fails
        """
        import tempfile
        import os
        import platform
        import subprocess
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(audio_data)
            temp_filename = f.name
        
        try:
            # Different commands for different operating systems
            system = platform.system()
            if system == "Darwin":  # macOS
                os.system(f'afplay "{temp_filename}"')
            elif system == "Linux":  # Linux
                try:
                    # Try using mpg123 first (better for MP3)
                    subprocess.run(['mpg123', '-q', temp_filename], check=True)
                except (subprocess.SubprocessError, FileNotFoundError):
                    # Fall back to aplay if mpg123 is not available
                    os.system(f'aplay "{temp_filename}"')
            elif system == "Windows":
                import winsound
                winsound.PlaySound(temp_filename, winsound.SND_FILENAME)
            else:
                raise Exception(f"Unsupported OS for audio playback: {system}")
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_filename)
            except:
                pass

def get_elevenlabs_client() -> ElevenLabsClient:
    """
    Helper function to get an ElevenLabs client instance.
    
    Returns:
        ElevenLabsClient: An initialized ElevenLabs client
    """
    return ElevenLabsClient()

# Example usage
if __name__ == "__main__":
    # Initialize the client
    client = get_elevenlabs_client()
    
    # Example: Convert text to speech and play it
    try:
        audio_data = client.text_to_speech("Olá. Este é um áudio de teste da ElevenLabs API para o Tobias.")
        
        # Play the audio
        client.play_audio(audio_data)
        
    except Exception as e:
        print(f"Error in text-to-speech: {e}")
    
    # Example: Convert speech to text (uncomment and modify as needed)
    """
    try:
        with open("path_to_audio.mp3", "rb") as audio_file:
            text = client.speech_to_text(audio_file)
            print(f"Transcribed text: {text}")
    except Exception as e:
        print(f"Error in speech-to-text: {e}")
    """
