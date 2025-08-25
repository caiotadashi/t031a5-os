import pyaudio
from google.cloud import speech
from dotenv import load_dotenv

load_dotenv()

# ----------------------------------------
# CONFIGURAÇÃO GOOGLE ASR
# ----------------------------------------
client = speech.SpeechClient()

RATE = 48000            # taxa nativa da DJI MIC
CHUNK = 1024            # tamanho do buffer (~21ms)
FORMAT = pyaudio.paInt16
CHANNELS = 1             # mono

# Configura reconhecimento
config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=RATE,
    language_code="pt-BR",
)
streaming_config = speech.StreamingRecognitionConfig(
    config=config,
    interim_results=True,
)

# ----------------------------------------
# INICIALIZAÇÃO PY AUDIO
# ----------------------------------------
pa = pyaudio.PyAudio()

# Tenta localizar DJI MIC automaticamente
device_index = None
for i in range(pa.get_device_count()):
    info = pa.get_device_info_by_index(i)
    if "DJI MIC" in info["name"]:
        device_index = i
        print(f"🎤 Usando DJI MIC no índice {i}")
        break

# Se não encontrar, usa microfone padrão
if device_index is None:
    print("⚠️ DJI MIC não encontrado, usando microfone padrão")
    
# Abre stream de áudio
stream = pa.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=CHUNK,
    input_device_index=device_index,  # None para default
)

# ----------------------------------------
# GERADOR DE ÁUDIO PARA GOOGLE
# ----------------------------------------
def request_generator():
    while True:
        try:
            data = stream.read(CHUNK, exception_on_overflow=False)
            if not data:
                continue
            yield speech.StreamingRecognizeRequest(audio_content=data)
        except Exception as e:
            print("Erro no stream de áudio:", e)
            break

# ----------------------------------------
# INICIA STREAMING DE RECONHECIMENTO
# ----------------------------------------
responses = client.streaming_recognize(streaming_config, request_generator())

print("🎧 Escutando... pressione Ctrl+C para sair")

try:
    for response in responses:
        for result in response.results:
            if result.is_final:
                print("Transcrição:", result.alternatives[0].transcript)
except KeyboardInterrupt:
    print("\n⏹️ Finalizando")
finally:
    stream.stop_stream()
    stream.close()
    pa.terminate()
