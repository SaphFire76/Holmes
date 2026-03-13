from fastapi import FastAPI, HTTPException
import requests
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from google.genai import types
import json
from abc import ABC, abstractmethod


# Abstract class for AI model adaptor, allowing for future integration of different models without changing the API logic
class AIModelAdaptor(ABC):
    @abstractmethod
    def analyse(self, email:str) -> dict:
        pass

    def get_prompt(self, email: str) -> str:
        return f"""
        Analyse this email for phishing indicators.
        Email: "{email}"
        
        Return a raw JSON object with this structure:
        {{
            "is_phishing": boolean,
            "risk_level": "Low" | "Medium" | "High",
            "explanation": "Concise reason why."
        }}
        """
    

# Concrete class for Google GenAI, implementing the AIModelAdaptor interface
class GoogleGenAIAdaptor(AIModelAdaptor):
    def __init__ (self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    def analyse(self, email: str) -> dict:
        prompt = self.get_prompt(email)
        print(f"Generated prompt for Google GenAI:\n{prompt}\n")
        verdict = self.client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json' 
            )
        )
        print(f"Received verdict from Google GenAI:\n{verdict.text}\n")
        return json.loads(verdict.text)


class LocalModelAdaptor(AIModelAdaptor):
    def __init__(self, model_name: str = 'llama3'):
        self.model_name = model_name
        self.api_url = "http://localhost:11434/api/generate"

    def analyse(self, email: str) -> dict:
        prompt = self.get_prompt(email)
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "format": "json",  # Forces local model into JSON mode
            "stream": False
        }
        
        response = requests.post(self.api_url, json=payload)
        response.raise_for_status()
        
        verdict = response.json().get("response", "")
        return json.loads(verdict)



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------MODEL SWITCH--------------------------------------------------

use_local_model = False  # Set to TRUE to use local model, FALSE to use Google GenAI
if use_local_model:
    ai_detector = LocalModelAdaptor(model_name='gemma3:4b') # Default to llama3, can specify other local models if needed
    print("Using local model")
else:
    print("Using Google GenAI model")
    ai_detector = GoogleGenAIAdaptor(api_key="AIzaSyA5AqpScGW4hs6fEIeExuV61OOo9T4l_xg")

# -----------------------------------------------------------------------------------------------------------



class Query(BaseModel):
    email: str

class PhishingVerdict(BaseModel):
    is_phishing: bool
    risk_level: str
    explanation: str

@app.post("/analyse", response_model=PhishingVerdict)
async def analyse_email(query: Query):
    try:
        verdict_dict = ai_detector.analyse(query.email)
        return verdict_dict
    except Exception as e:
        print(f"Error during analysis: {e}")
        raise HTTPException(status_code=500, detail="AI processing failed.")