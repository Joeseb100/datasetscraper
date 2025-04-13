# Importing the Google Translate package
from googletrans import Translator

# Initialize the translator object
translator = Translator()

def translate_to_malayalam(text):
    """Function to translate a given text to Malayalam."""
    try:
        translation = translator.translate(text, src='en', dest='ml')
        return translation.text
    except Exception as e:
        return f"Translation error: {str(e)}"
