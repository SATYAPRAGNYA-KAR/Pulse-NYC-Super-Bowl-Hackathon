from .config import BLOCKED_KEYWORDS, CONFIDENCE_THRESHOLD, RECIPIENT_LIST
from .llm_generator import build_prompt, generate_content
from .email_sender import send_email  # real SMTP sender

# Map event types to creative angles
ANGLE_BY_EVENT = {
    "fumble": ["humor", "relief"],
    "touchdown": ["celebration", "urgency"],
    "big_play": ["hype"]
}

# Safety check
def is_safe(event):
    """
    Check if event passes confidence and blocked keywords filter
    """
    if event.get('confidence', 0) < CONFIDENCE_THRESHOLD:
        return False
    if any(k in BLOCKED_KEYWORDS for k in event.get('keywords', [])):
        return False
    return True

# Pick a creative angle for this product + event
def pick_angle(event, product):
    angles = ANGLE_BY_EVENT.get(event.get('type'), ["neutral"])
    if product.get("risk_tolerance", "high") == "low":
        angles = [a for a in angles if a != "humor"]
    return angles[0]

# End-to-end processing function
def process_event(matched_products, event, demo_mode=False):
    """
    matched_products: list of product dicts
    event: dict containing event info
    demo_mode: if True, prints email instead of sending
    """
    if not is_safe(event):
        print("Event not safe. Skipping.")
        return

    for product in matched_products:
        angle = pick_angle(event, product)
        prompt = build_prompt(product, event, angle)
        content = generate_content(prompt)

        # Ensure LLM output has subject/body/cta
        subject = content.get("subject", f"{product.get('name', 'Product')} Deal!")
        body = content.get("body", "Check out this offer!")
        cta = content.get("cta", "Shop Now!")

        if demo_mode:
            # Demo mode: just print
            print(f"[DEMO] Would send email to {RECIPIENT_LIST}")
            print(f"Subject: {subject}")
            print(f"Body: {body}")
            print(f"CTA: {cta}")
            print("-"*40)
        else:
            # Send real email
            send_email(subject, body, RECIPIENT_LIST)
