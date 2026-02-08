"""
run_event.py

Exposes a single callable function `execute_event_from_file` for the previous team.
It:
1. Reads products.json and event_from_prev_team.json
2. Calls your existing process_event() function
3. Returns the results as a list of dicts
"""

import os
import json
from .event_processor import process_event
 # existing function

# Paths relative to this file
CURRENT_DIR = os.path.dirname(__file__)
PRODUCTS_JSON_FILE = os.path.join(CURRENT_DIR, "products.json")
EVENT_JSON_FILE = os.path.join(CURRENT_DIR, "event_from_prev_team.json")


def execute_event_from_file():
    """
    Reads the products and event JSON files,
    calls process_event() from your existing code,
    returns results.

    Returns:
        list of dicts: [{"product": ..., "content": {...}}, ...]
    """
    # Load products
    if not os.path.exists(PRODUCTS_JSON_FILE):
        raise FileNotFoundError(f"Products file not found: {PRODUCTS_JSON_FILE}")
    with open(PRODUCTS_JSON_FILE, "r") as f:
        products = json.load(f)

    # Load event
    if not os.path.exists(EVENT_JSON_FILE):
        raise FileNotFoundError(f"Event file not found: {EVENT_JSON_FILE}")
    with open(EVENT_JSON_FILE, "r") as f:
        event = json.load(f)

    # Call existing process_event function
    results = process_event(products, event)
    return results


# --- Optional demo ---
if __name__ == "__main__":
    print("Running demo using event_from_prev_team.json...")
    results = execute_event_from_file()
    if results:
        print("Generated content for products:")
        print(json.dumps(results, indent=2))
    else:
        print("No content generated.")
