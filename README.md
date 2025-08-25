# Unitree G1 AI Assistant

This project implements an AI assistant for the Unitree G1 humanoid robot, featuring voice interaction using ElevenLabs for speech synthesis, OpenAI for natural language processing, and Google Cloud Speech-to-Text for voice recognition.

## 📋 Prerequisites

### Hardware
- Unitree G1 Humanoid Robot
- External microphone (if not using robot's built-in mic)
- Speakers (if not using robot's built-in speakers)

### Software
- Ubuntu 20.04/22.04 LTS (recommended)
- Python 3.10
- ROS 2 Humble (if integrating with ROS)

## 🚀 Installation

### 1. System Dependencies

```bash
# Update package lists
sudo apt-get update

# Install required system packages
sudo apt-get install -y \
    python3.10-dev \
    gfortran \
    portaudio19-dev \
    python3-pyaudio \
    git \
    python3-pip \
    python3-venv
```

### 2. Clone the Repository

```bash
git clone <repository-url>
cd t031a5-os
```

### 3. Set Up Python Environment

```bash
# Create and activate virtual environment
python3.10 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt
```

## 🔑 API Keys Configuration

Create a `.env` file in the project root with the following content:

```env
# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# ElevenLabs API Key
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# Google Cloud Credentials (if using Google Speech-to-Text)
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json
```

## 🤖 Running the Application

### Basic Voice Interaction

```bash
# Activate virtual environment if not already activated
source venv/bin/activate

# Run the main application
python -m core.cortex
```

### Available Commands

- Start voice interaction: The system will listen for your voice command
- Press `Ctrl+C` to exit the application

## 🧩 Project Structure

```
.
├── core/
│   ├── cortex.py       # Main application logic
│   └── nldb.py         # Natural language processing utilities
├── llm/
│   └── openai_client.py  # OpenAI API client
├── speak/
│   └── elevenlabs_client.py  # ElevenLabs TTS client
├── inputs/
│   └── googleasr.py    # Google Speech-to-Text integration
├── src/
│   └── unitree/        # Unitree SDK and robot control
├── .env                # Environment variables
└── requirements.txt    # Python dependencies
```

## 🤖 Unitree G1 Integration

### Connecting to the Robot

1. Ensure the robot is powered on and connected to the same network as your computer
2. Verify connection by pinging the robot's IP address

### Running Robot-Specific Commands

```python
# Example: Make the robot wave
from src.unitree.unitree.testes.g1_wave_hello import wave_hello
wave_hello()
```

## 🛠 Troubleshooting

### Audio Issues
- If you encounter audio device errors, verify your default audio input/output devices:
  ```bash
  # List audio devices
  arecord -l  # For input devices
  aplay -l    # For output devices
  ```
- Update the audio device index in the code if necessary

### API Connection Issues
- Verify your API keys are correctly set in the `.env` file
- Check your internet connection
- Ensure you have sufficient credits/quotas for the API services

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Unitree Robotics for the G1 humanoid platform
- OpenAI for the language model API
- ElevenLabs for text-to-speech capabilities
- Google Cloud for speech recognition
