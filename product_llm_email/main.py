import os
import json
import time
from event_processor import process_event

# Paths relative to this file
current_dir = os.path.dirname(__file__)
products_path = os.path.join(current_dir, "products.json")
event_json_path = os.path.join(current_dir, "event_from_prev_team.json")

# Load products
with open(products_path, "r") as f:
    products = json.load(f)

# Track last processed event to avoid duplicates
last_event = None

print("Watching for new events in real-time... Press Ctrl+C to stop.")

try:
    while True:
        if os.path.exists(event_json_path):
            with open(event_json_path, "r") as f:
                event = json.load(f)

            # Only process if it's new
            if event != last_event:
                print(f"New event detected: {event['type']}")
                process_event(products, event)
                last_event = event
        else:
            print(f"Waiting for event JSON file: {event_json_path}")

        time.sleep(3)  # check every 3 seconds

except KeyboardInterrupt:
    print("Stopped real-time watcher.")
