import io
import time

import numpy as np
import soundfile as sf
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from kokoro import KPipeline
from phonemizer.backend.espeak.wrapper import EspeakWrapper
from pydantic import BaseModel

app = FastAPI()

EspeakWrapper.set_library("/usr/lib/libespeak-ng.so")

print("Loading Kokoro TTS model... (this may take a minute first time)")
device = "cpu"
pipeline = KPipeline(lang_code="b", device=device)
print(f"Model loaded on {device}.")


class TTSRequest(BaseModel):
    text: str
    voice: str = "af_bella"
    speed: float = 1.0


@app.post("/tts")
async def generate_audio(request: TTSRequest):
    """
    Receives text, generates audio, and returns the WAV file bytes.
    """
    try:
        start = time.time()
        generator = pipeline(
            request.text, voice=request.voice, speed=request.speed, split_pattern=r"\n+"
        )

        all_audio = []
        for _, (_, _, audio) in enumerate(generator):
            all_audio.append(audio)

        if not all_audio:
            raise HTTPException(
                status_code=400, detail="Could not generate audio from text."
            )

        final_audio = np.concatenate(all_audio)
        buffer = io.BytesIO()
        sf.write(buffer, final_audio, 24000, format="WAV")
        buffer.seek(0)

        print(f"Took: {time.time() - start}")
        return Response(content=buffer.read(), media_type="audio/wav")

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
