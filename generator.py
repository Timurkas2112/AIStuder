from google.generativeai.types import HarmCategory, HarmBlockThreshold
import google.generativeai as genai
from os import getenv

genai.configure(api_key=getenv('API_GEMINI'))

model = genai.GenerativeModel(model_name='gemini-1.5-flash')


def get_request_gemini(request, assistant=None):
    messages = [
        {
            "role": "user",
            "parts": request
        },
    ]
    if assistant:
        messages.insert(0, {
            "role": "assistant",
            "parts": assistant
        })

    response = model.generate_content(
        contents=messages,
        safety_settings={
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
        }
    )
    return response.text

print(get_request_gemini('hello'))
