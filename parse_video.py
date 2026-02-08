import os
import csv
import subprocess
import whisper
import librosa
import numpy as np

VIDEO_PATH = "assets/videoplayback (1).mp4"
AUDIO_PATH = "audio.wav"
CHUNK_DIR = "chunks"
CSV_PATH = "output.csv"
CHUNK_LENGTH = 5  # seconds

os.makedirs(CHUNK_DIR, exist_ok=True)

# ----------------------------
# 1. Extract audio from mp4
# ----------------------------
subprocess.run([
    "ffmpeg", "-y",
    "-i", VIDEO_PATH,
    "-ac", "1",
    "-ar", "16000",
    AUDIO_PATH
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# ----------------------------
# 2. Load audio + duration
# ----------------------------
y, sr = librosa.load(AUDIO_PATH, sr=16000)
duration = int(len(y) / sr)

# ----------------------------
# 3. Load Whisper model
# ----------------------------
model = whisper.load_model("base")  # use "tiny" for faster

# ----------------------------
# 4. Prepare CSV
# ----------------------------
with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["timestamp", "words", "average_amplitude"])

    # ----------------------------
    # 5. Process 5s chunks
    # ----------------------------
    for start in range(0, duration, CHUNK_LENGTH):
        end = min(start + CHUNK_LENGTH, duration)
        chunk_path = f"{CHUNK_DIR}/chunk_{start}.wav"

        # Extract chunk
        subprocess.run([
            "ffmpeg", "-y",
            "-i", AUDIO_PATH,
            "-ss", str(start),
            "-t", str(CHUNK_LENGTH),
            chunk_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Load chunk audio
        chunk_audio, _ = librosa.load(chunk_path, sr=16000)

        # ----------------------------
        # Average amplitude
        # ----------------------------
        avg_amplitude = int(np.mean(np.abs(chunk_audio)) * 1000)

        # ----------------------------
        # Speech → words
        # ----------------------------
        result = model.transcribe(chunk_path, fp16=False)
        words = result["text"].strip().lower()
        word_list = ";".join(words.split())

        # ----------------------------
        # Write CSV row
        # ----------------------------
        writer.writerow([
            f"{start}-{end}",
            word_list,
            avg_amplitude
        ])

print("✅ Done. CSV saved as:", CSV_PATH)
