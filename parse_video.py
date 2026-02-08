import os
import csv
import subprocess
import time
from collections import defaultdict

import whisper
import librosa
import numpy as np



SCALING_EVENT_WORD = 1000
DECIBLE_DECAY_FACTOR = 0.2

class EventDetector:
    def __init__(self):
        self.tokens_so_far = [] # list of tuples
        self.consider_last_n = 5
        self.events = {
            "touchdown" : ["touchdown", "watchdown", "countdown"]
        }
        self.count = 0

        # something for testing
        self.score_logs = []

    def decide_event(self):
        last_events = self.tokens_so_far[-self.consider_last_n:][::-1]
        full_text_list = []
        for last_event in last_events:
            full_text_list.append(last_event[0])


        scores = defaultdict(lambda: 0)
        # for event in self.events:
        #     for event_word in self.events[event]:
        #         scores[event] += full_text.count(event_word) * SCALING_EVENT_WORD
        decay = SCALING_EVENT_WORD
        for chunk_text in full_text_list:
            print("chunk", chunk_text)
            for event_key in self.events:
                match_count = 0
                for key_word in self.events[event_key]:
                    match_count += chunk_text.count(key_word)

                print("match count", match_count)
                scores[event_key] += match_count*decay
            decay = decay * DECIBLE_DECAY_FACTOR

        decay = 1
        for chunk in last_events:
            for event in scores:
                scores[event] += chunk[1] * decay

            decay = decay * DECIBLE_DECAY_FACTOR

        decay = 1000
        for chunk in last_events:
            for event in scores:
                scores[event] += len(chunk[0])
            decay = decay * DECIBLE_DECAY_FACTOR

        print("SCOREWS", self.count, scores['touchdown'])
        self.score_logs.append(scores['touchdown'])


    def feed_new_event(self, new_event):
        text, decible = new_event
        print("text and decible value", text, decible)
        self.tokens_so_far.append((text.replace(";", ""), decible))

        self.decide_event()

        self.count += 1


event_detector = EventDetector()

# ----------------------------
# CONFIG
# ----------------------------
VIDEO_PATH = "./videoplayback.mp4"
AUDIO_PATH = "audio.wav"
CHUNK_DIR = "chunks"
CSV_PATH = "output.csv"
CHUNK_LENGTH = 5  # seconds

os.makedirs(CHUNK_DIR, exist_ok=True)

# ----------------------------
# 1. Extract mono 16kHz audio
# ----------------------------
subprocess.run(
    [
        "ffmpeg", "-y",
        "-i", VIDEO_PATH,
        "-ac", "1",
        "-ar", "16000",
        AUDIO_PATH
    ],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)

# ----------------------------
# 2. Load audio to get duration
# ----------------------------
y, sr = librosa.load(AUDIO_PATH, sr=16000)
duration = int(len(y) / sr)

# ----------------------------
# 3. Load Whisper ONCE
# ----------------------------
model = whisper.load_model("base")  # use "tiny" if CPU is slow

# ----------------------------
# 4. Prepare CSV
# ----------------------------
with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["timestamp", "words", "average_amplitude"])

    # ----------------------------
    # 5. REAL-TIME SYNC START
    # ----------------------------
    start_wall_time = time.time()

    for i, start in enumerate(range(0, duration, CHUNK_LENGTH)):
        end = min(start + CHUNK_LENGTH, duration)
        chunk_path = f"{CHUNK_DIR}/chunk_{start}.wav"

        # ----------------------------
        # Extract 5s chunk
        # ----------------------------
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", AUDIO_PATH,
                "-ss", str(start),
                "-t", str(CHUNK_LENGTH),
                chunk_path
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # ----------------------------
        # Load chunk
        # ----------------------------
        chunk_audio, _ = librosa.load(chunk_path, sr=16000)

        # ----------------------------
        # Average amplitude
        # ----------------------------
        avg_amplitude = int(np.mean(np.abs(chunk_audio)) * 1000)

        # ----------------------------
        # Speech → text
        # ----------------------------
        result = model.transcribe(chunk_path, fp16=False)
        text = result["text"].strip().lower()
        word_list = ";".join(text.split())

        # ----------------------------
        # Write CSV row
        # ----------------------------
        writer.writerow([
            f"{start}-{end}",
            word_list,
            avg_amplitude
        ])
        print("Step", f"{start}-{end}")
        event_detector.feed_new_event((word_list, avg_amplitude))
        f.flush()  # ensure real-time write

        # ----------------------------
        # ⏱️ HARD REAL-TIME SYNC
        # ----------------------------
        target_time = start_wall_time + (i + 1) * CHUNK_LENGTH
        sleep_time = target_time - time.time()

        if sleep_time > 0:
            time.sleep(sleep_time)


print("✅ Done. CSV saved as:", CSV_PATH)
