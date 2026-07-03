from openai import OpenAI
import logging
from django.conf import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def translate_text(text, target_language):
    """
    Translate a given text to the target language using OpenAI,
    skipping English and protecting proper nouns and names.
    """
    if not text or target_language.lower() == "english":
        return text  # skip translation

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are a precise translation assistant. "
                        f"Translate the text into {target_language}. "
                        f"DO NOT explain anything. "
                        f"DO NOT guess meaning. "
                        f"DO NOT add commentary. "
                        f"If the text appears to be a name, brand, username, or proper noun, "
                        f"KEEP IT UNCHANGED. Just translate normal human text naturally."
                    )
                },
                {"role": "user", "content": text},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.exception(f"Translation failed: {e}")
        return text
