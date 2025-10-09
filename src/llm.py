# import libraries
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv() # Loads environment variables from .env
token = os.environ["GITHUB_TOKEN"]
endpoint = "https://models.github.ai/inference"
model = "openai/gpt-4.1-mini"
# A function to call an LLM model and return the response
def call_llm_model(model, messages, temperature=1.0, top_p=1.0):
    client = OpenAI(base_url=endpoint,api_key=token)
    response = client.chat.completions.create(
    messages=messages,
    temperature=temperature, top_p=top_p, model=model)
    return response.choices[0].message.content
# a function to translate text using the LLM model

system_prompt = r'''
        Extract the user's notes into the following structured fields:
        1. Title: A concise title of the notes less than 5 words
        2. Notes: The notes based on user input written in full sentences.
        3. Tags (A list): At most 3 Keywords or tags that categorize the content of the notes.
        Output in JSON format without ```json. Output title and notes in the language: {lang}.
        Example:
        Input: "Badminton tmr 5pm @polyu".
        Output:
        {{
            "Title": "Badminton at PolyU",
            "Notes": "Remember to play badminton at 5pm tomorrow at PolyU.",
            "Tags": ["badminton", "sports"]
        }} 
'''

def extract_structured_notes(text, lang="English"):
    prompt  = f"Extract the users' notes into structured fields in {lang}."
    messages = [
        {"role": "system", "content": system_prompt.format(lang=lang)},
        {"role": "user", "content": text}
    ]
    return call_llm_model(model, messages)


def translate(text, target_language):
    messages = [
        {"role": "system", "content": "You are a helpful assistant that translates text."},
        {"role": "user", "content": f"Translate the following text to {target_language}: {text}"}
    ]
    return call_llm_model(model, messages)

if __name__ == "__main__":
    # text = "Hello, how are you?"
    # target_language = "Chinese"
    # translated_text = translate(text, target_language)
    # print(translated_text)

    # test the extract notes feature
    sample_text = "Badminton tmr 5pm @polyu"
    extracted = extract_structured_notes(sample_text, lang="Chinese")
    print(extracted)

