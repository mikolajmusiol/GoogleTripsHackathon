from dotenv import load_dotenv
import google.generativeai as genai
import os

load_dotenv()

genai.configure(api_key=os.environ['GOOGLE_API_KEY'])
model = genai.GenerativeModel('gemini-2.5-pro')

def generate_llm_response(message_history):
    """
    Generates a streaming response from the Gemini model using the full conversation history.
    """
    # Translate our message format to the Gemini API's format.
    # The Gemini API uses 'user' and 'model' roles.
    gemini_history = [] 
    for message in message_history[:-1]: # Exclude the last message, which is the new prompt
        role = 'user' if message['sender'] == 'user' else 'model'
        gemini_history.append({
            'role': role,
            'parts': [message['text']]
        })

    # The last message in the history is the prompt for the model.
    prompt = message_history[-1]['text']

    # Start a chat session with the history
    chat = model.start_chat(history=gemini_history)
    
    # Send the new prompt and stream the response
    response = chat.send_message(prompt, stream=True)
    
    for chunk in response:
        yield chunk.text
