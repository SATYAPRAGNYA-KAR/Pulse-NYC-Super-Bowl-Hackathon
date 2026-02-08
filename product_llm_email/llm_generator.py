import time
from openai import OpenAI
from .config import LLM_API_KEY

# Initialize OpenAI client
client = OpenAI(api_key=LLM_API_KEY)

# Build prompt
def build_prompt(product, event, angle):
    promo_dict = {
        "fumble": "20% off for the next 15 minutes",
        "touchdown": "Free delivery until halftime",
        "big_play": "Bonus deal unlocked"
    }
    promo = promo_dict.get(event['type'], "Special offer available now")
    
    prompt = f"""
You are a marketing assistant writing a short email for a small business.

Business:
- Name: {product['name']}
- Category: {product['category']}

Event:
- Type: {event['type'].upper()}
- Keywords: {', '.join(event['keywords'])}

Creative Angle:
- {angle}

Promotion:
- {promo}

Rules:
- Keep under 60 words
- Friendly, casual tone
- No jokes about injuries or sensitive topics
- Clear call to action

Generate:
1. Subject line
2. Email body
"""
    return prompt


# Generate content with retries & fallback
def generate_content(prompt):
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150
            )
            output = response.choices[0].message.content
            break
        except Exception as e:
            print(f"[Attempt {attempt+1}] LLM API error: {e}. Retrying in 2 sec...")
            time.sleep(2)
    else:
        print("All retries failed. Using demo content.")
        output = "Special Offer!\nOrder now and enjoy our latest deal."

    # -------- CLEAN SUBJECT & BODY --------
    if "\n" in output:
        subject_raw, body_raw = output.split("\n", 1)
    else:
        subject_raw = output
        body_raw = ""

    # Clean subject
    subject = subject_raw.strip()
    subject = subject.replace("**", "")
    subject = subject.replace("Subject Line:", "")
    subject = subject.replace("Subject:", "")
    subject = subject.strip()

    # Clean body
    body = body_raw.strip()
    body = body.replace("**", "")
    body = body.replace("Email Body:", "")
    body = body.strip()

    return {
        "subject": subject,
        "body": body,
        "cta": "Order Now"
    }
