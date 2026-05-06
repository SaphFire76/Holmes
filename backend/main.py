from fastapi import FastAPI, HTTPException
import requests
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from google.genai import types
import json
from abc import ABC, abstractmethod
import bcrypt
import mysql.connector
from mysql.connector import Error
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

allowed_origins = os.getenv("CORS_ORIGINS", "").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 # Token expires in 1 hour

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def create_access_token(data: dict):
    """Creates the JWT token with an expiration date"""
    to_encode = data.copy()
    
    # Calculate expiration time using timezone-aware datetime!
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    # Generate the actual token string
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# 1. Setup the FastAPI security scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# 2. THE BOUNCER: A dependency function that checks the token on protected routes
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        # Decode the token using your secret key
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


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
        self.api_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")

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



# ---------------------------------------------MODEL SWITCH--------------------------------------------------

env_use_local = os.getenv("USE_LOCAL_MODEL", "False").lower()
use_local_model = (env_use_local == "true")
if use_local_model:
    model_name = os.getenv("MODEL_NAME", "gemma3:4b")
    ai_detector = LocalModelAdaptor(model_name=model_name) # Default to llama3, can specify other local models if needed
    print("Using local model")
else:
    print("Using Google GenAI model")
    api_key = os.getenv("GOOGLE_API_KEY")
    ai_detector = GoogleGenAIAdaptor(api_key=api_key)

# -----------------------------------------------------------------------------------------------------------



class Query(BaseModel):
    email: str

# class PhishingVerdict(BaseModel):
#     is_phishing: bool
#     risk_level: str
#     explanation: str

@app.post("/analyse")
async def analyse_email(query: Query, user_id: str = Depends(get_current_user)):
    print(f"DEBUG - User ID from token: {user_id}")
    # 1. Run the AI processing
    try:
        verdict_dict = ai_detector.analyse(query.email)
        print(f"DEBUG - Verdict Dict: {verdict_dict}")
    except Exception as e:
        print(f"Error during AI analysis: {e}")
        raise HTTPException(status_code=500, detail="AI processing failed.")

    # 2. Save using the Stored Procedure
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor(dictionary=True)
        current_time = datetime.now()
        print(f"DEBUG - Current Time: {current_time}")

        # Create a quick title (first 50 characters)
        generated_title = query.email[:47].strip() + "..." if len(query.email) > 50 else query.email

        # Call our new stored procedure
        cursor.callproc('InsertNewScan', (
            int(user_id),
            generated_title,
            query.email,
            verdict_dict.get('is_phishing'),
            verdict_dict.get('risk_level'),
            verdict_dict.get('explanation'),
            current_time
        ))
        
        # Grab the new scan_id that the procedure returned
        new_scan_id = None
        for result in cursor.stored_results():
            row = result.fetchone()
            if row:
                new_scan_id = row['new_scan_id']

        # Commit the transaction!
        conn.commit()

        if not new_scan_id:
            raise Exception("Failed to retrieve new scan ID from database")

        # 3. Build the full object to send back to React
        full_scan = {
            "scan_id": new_scan_id,
            "user_id": int(user_id),
            "title": generated_title,
            "email": query.email,
            "is_phishing": verdict_dict.get('is_phishing'),
            "risk_level": verdict_dict.get('risk_level'),
            "explanation": verdict_dict.get('explanation'),
            "date": current_time.isoformat()
        }
        
        return {"scan": full_scan}
        
    except Exception as e:
        conn.rollback() # Cancel the transaction if it failed
        print(f"Database Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save scan to database.")
        
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
    

def get_password_hash(password: str) -> str:
    # Convert to bytes, hash it, convert back to string for the DB
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_password.decode('utf-8')


class UserRegister(BaseModel):
    email: str
    username: str
    password: str


# --- Registration Endpoint ---
@app.post("/register")
async def register_user(user: UserRegister):
    print(f"DEBUG - Received Password: {user.password}")
    print(f"DEBUG - Password Length: {len(user.password)}")

    # 1. Hash the plain-text password from the frontend IMMEDIATELY
    hashed_password = get_password_hash(user.password)
    
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor()
        
        # 2. Call your stored procedure
        # callproc takes the procedure name and a tuple of arguments.
        # We pass 0 as a placeholder for the OUT parameter (p_new_user_id)
        result_args = cursor.callproc(
            'RegisterUser', 
            (user.email, user.username, hashed_password, 0)
        )
        
        # 3. Commit the transaction to save it to the DB
        conn.commit()
        
        # 4. Extract the OUT parameter (it's the 4th item in the tuple, so index 3)
        new_user_id = result_args[3]
        
        # Create the exact same JWT payload you use in /login
        token_payload = {"sub": str(new_user_id)}
        
        # Generate the token
        access_token = create_access_token(token_payload)
        
        # Return the token along with the success message!
        return {
            "message": "User created successfully!",
            "user_id": new_user_id,
            "access_token": access_token,
            "token_type": "bearer"
        }

    except mysql.connector.IntegrityError as e:
        # DB schema set email as UNIQUE. 
        # If someone tries to register with an existing email, it throws an IntegrityError.
        raise HTTPException(status_code=400, detail="Email already registered")
        
    except Exception as e:
        print(f"Registration Error: {e}")
        raise HTTPException(status_code=500, detail="An error occurred during registration")
        
    finally:
        # Always close the connection to prevent memory leaks!
        if conn.is_connected():
            cursor.close()
            conn.close()



# --- Helper Functions ---
def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Convert both to bytes and compare
    password_byte_enc = plain_password.encode('utf-8')
    hashed_password_byte_enc = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_byte_enc, hashed_password_byte_enc)

# --- Pydantic Model for Login ---
class UserLogin(BaseModel):
    email: str
    password: str

# --- The Login Endpoint ---
@app.post("/login")
async def login_user(user: UserLogin):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor(dictionary=True) 
        cursor.callproc('GetUserByEmail', (user.email,))
        
        db_user = None
        for result in cursor.stored_results():
            db_user = result.fetchone()
            
        if not db_user or not verify_password(user.password, db_user['password']):
            raise HTTPException(status_code=401, detail="Invalid email or password")
            
        # Create token
        token_payload = {"sub": str(db_user['user_id'])}
        access_token = create_access_token(token_payload)

        print(access_token)
        
        # JUST return the token!
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "message": "Login successful"
        }
    
    except mysql.connector.Error as e:
        print(f"Database Error: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
        
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


@app.get("/users/me")
async def get_user_profile(user_id: str = Depends(get_current_user)):
    # The 'user_id' is automatically extracted from the token by your 'get_current_user' function
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        print(f"DEBUG - Fetching profile for User ID: {user_id}")
        cursor = conn.cursor(dictionary=True) 
        cursor.callproc('GetUserById', (user_id,))
        
        user_data = None
        for result in cursor.stored_results():
            user_data = result.fetchone()

        print(f"DEBUG - User Data from DB: {user_data}")
            
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")
            
        return {"user": user_data}

    except mysql.connector.Error as e:
        print(f"Database Error: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
        
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


@app.get("/history")
async def get_history(user_id: str = Depends(get_current_user)):
    print(f"DEBUG - User ID from token: {user_id}")
    # Notice the 'Depends(get_current_user)' above? 
    # FastAPI will automatically reject anyone without a valid token before this code even runs!
    
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
        
    try:
        cursor = conn.cursor(dictionary=True)
        # We pass the user_id extracted safely from the JWT!
        cursor.callproc('GetUserScansSummary', (int(user_id),))
        
        scan_history = []
        for result in cursor.stored_results():
            scan_history = result.fetchall()
            
        return {"history": scan_history}
        
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


@app.get("/scans/{scan_id}")
async def get_full_scan_verdict(scan_id: int, user_id: str = Depends(get_current_user)):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
        
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 1. Call the stored procedure, passing the ID from the URL and the ID from the JWT token
        cursor.callproc('GetScanDetails', (scan_id, int(user_id)))
        
        # 2. Extract the result
        full_scan = None
        for result in cursor.stored_results():
            full_scan = result.fetchone() # We only expect ONE record, so fetchone() is perfect
            
        # 3. Security Check: If the scan doesn't exist or doesn't belong to them, reject it
        if not full_scan:
            raise HTTPException(status_code=404, detail="Scan not found or unauthorized")
            
        return {"scan": full_scan}
        
    except mysql.connector.Error as e:
        print(f"Database Error: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
        
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


@app.get("/search")
async def search_scans(q: str, user_id: str = Depends(get_current_user)):
    # If they send an empty search, just return an empty list instantly
    if not q or len(q.strip()) == 0:
        return {"results": []}

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
        
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Call the new stored procedure
        cursor.callproc('SearchScans', (int(user_id), q.strip()))
        
        search_results = []
        for result in cursor.stored_results():
            search_results = result.fetchall()
            
        return {"results": search_results}
        
    except mysql.connector.Error as e:
        print(f"Database Error: {e}")
        raise HTTPException(status_code=500, detail="Database search failed")
        
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


class RenameRequest(BaseModel):
    new_title: str

@app.patch("/scans/{scan_id}/rename")
async def rename_scan(scan_id: int, request: RenameRequest, user_id: str = Depends(get_current_user)):
    print(f"DEBUG - User ID from token: {user_id}. Attempting to rename scan {scan_id} to '{request.new_title}'")

    # 1. Enforce the 50-character database limit so it doesn't crash!
    safe_title = request.new_title[:50].strip()
    if not safe_title:
        raise HTTPException(status_code=400, detail="Title cannot be empty")

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
        
    try:
        cursor = conn.cursor()
        
        # 2. Call the stored procedure
        cursor.callproc('RenameScan', (int(user_id), scan_id, safe_title))
        
        # 3. MUST commit to save the UPDATE!
        conn.commit()
        
        return {"message": "Scan renamed", "new_title": safe_title}
        
    except mysql.connector.Error as e:
        conn.rollback()
        print(f"Database Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to rename scan")
        
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


@app.delete("/scans/{scan_id}")
async def delete_scan(scan_id: int, user_id: str = Depends(get_current_user)):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
        
    try:
        cursor = conn.cursor()
        
        # 1. Call the stored procedure
        cursor.callproc('DeleteScan', (int(user_id), scan_id))
        
        # 2. MUST commit to finalize the deletion!
        conn.commit()
        
        return {"message": "Scan deleted successfully"}
        
    except mysql.connector.Error as e:
        conn.rollback()
        print(f"Database Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete scan")
        
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()