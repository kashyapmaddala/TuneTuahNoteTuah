from fastapi import FastAPI, Form
from fastapi.responses import FileResponse
from transformers import MusicgenForConditionalGeneration, AutoProcessor
import torch
import tempfile
import torchaudio
from basic_pitch.inference import predict_and_save # type: ignore

app = FastAPI()

# Load the model and processor
processor = AutoProcessor.from_pretrained("facebook/musicgen-medium")
model = MusicgenForConditionalGeneration.from_pretrained("facebook/musicgen-medium")
model = model.to("cuda" if torch.cuda.is_available() else "cpu")

@app.post("/generate_music/")
async def generate_music(text: str = Form(...)):
    inputs = processor(text=[text], return_tensors="pt").to(model.device)
    audio_values = model.generate(**inputs, max_new_tokens=512)  # Adjust token length as needed

    # Save WAV file
    temp_audio_path = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    torchaudio.save(temp_audio_path, torch.tensor(audio_values[0]), 44100)

    # Convert WAV to MIDI using Basic Pitch
    temp_midi_path = temp_audio_path.replace(".wav", ".mid")
    predict_and_save(temp_audio_path, temp_midi_path)

    return {"audio": FileResponse(temp_audio_path, media_type="audio/wav", filename="generated_music.wav"),
            "midi": FileResponse(temp_midi_path, media_type="audio/midi", filename="generated_music.mid")}
