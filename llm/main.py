from dotenv import load_dotenv
import google.generativeai as genai
import os

load_dotenv()

genai.configure(api_key=os.environ['GOOGLE_API_KEY'])
model = genai.GenerativeModel('gemini-2.5-pro')


prompt = "What is the capital of France?"
response = model.generate_content(prompt)

# Print the response
print(response.text)
