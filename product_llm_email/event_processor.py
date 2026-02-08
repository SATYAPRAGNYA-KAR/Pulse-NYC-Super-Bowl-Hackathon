from .config import BLOCKED_KEYWORDS, CONFIDENCE_THRESHOLD, RECIPIENT_LIST
from .llm_generator import build_prompt, generate_content

ANGLE_BY_EVENT = {
    "fumble": ["humor", "relief"],
    "touchdown": ["celebration", "urgency"],
    "big_play": ["hype"]
}

# Safety check
def is_safe(event):
    if event['confidence'] < CONFIDENCE_THRESHOLD:
        return False
    if any(k in BLOCKED_KEYWORDS for k in event['keywords']):
        return False
    return True

# Pick creative angle
def pick_angle(event, product):
    angles = ANGLE_BY_EVENT.get(event['type'], ["neutral"])
    if product.get("risk_tolerance","high") == "low":
        angles = [a for a in angles if a != "humor"]
    return angles[0]

# Mock email blast (for demo)
def send_email(recipient_list, content):
    for email in recipient_list:
        print(f"Sending to {email}:")
        print(f"Subject: {content['subject']}")
        print(f"Body: {content['body']}")
        print(f"CTA: {content['cta']}")
        print("-"*30)

# End-to-end processing function
def process_event(matched_products, event):
    if not is_safe(event):
        print("Event not safe. Skipping.")
        return
    
    for product in matched_products:
        angle = pick_angle(event, product)
        prompt = build_prompt(product, event, angle)
        content = generate_content(prompt)
        send_email(RECIPIENT_LIST, content)
