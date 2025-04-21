# Importing the Google Translate package
from googletrans import Translator
import time
import random

class TranslationService:
    def __init__(self):
        self.translator = Translator()
        
    def translate_text(self, text, source='en', target='ml'):
        """Translate text from source language to target language with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Add a small delay to avoid rate limiting
                time.sleep(random.uniform(0.5, 1.5))
                translation = self.translator.translate(text, src=source, dest=target)
                return translation.text
            except Exception as e:
                print(f"Translation attempt {attempt+1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    # Exponential backoff
                    time.sleep(2 ** attempt)
                    continue
                return f"Translation error: {str(e)}"

# For backward compatibility
def translate_to_malayalam(text):
    """Function to translate a given text to Malayalam."""
    service = TranslationService()
    return service.translate_text(text, source='en', target='ml')
