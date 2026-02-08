from flask import Flask
import matplotlib.pyplot as plt
import csv
from collections import defaultdict

app = Flask(__name__)

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


@app.route("/")
def home():
    return "Hello from Flask on PythonAnywhere 🚀"

if __name__ == "__main__":
    event_detector = EventDetector()
    with open('output.csv', newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            print(row)
            event_detector.feed_new_event((row[1], int(row[2])))


