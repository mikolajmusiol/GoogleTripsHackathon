from dotenv import load_dotenv
import google.generativeai as genai
import os

load_dotenv()

genai.configure(api_key=os.environ['GOOGLE_API_KEY'])
model = genai.GenerativeModel('gemini-2.5-pro')

def generate_llm_response(prompt):
    """
    Generates a response from the Gemini model for the given prompt.
    """
    response = model.generate_content(prompt)
    return response.text


# The following lines were for testing purposes and can be removed or commented out
# prompt = "What is the capital of France?"
# response = generate_llm_response(prompt)
# print(response)
