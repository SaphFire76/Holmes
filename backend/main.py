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
            password=os.getenv("DB_PASSWORD"),
            port=int(os.getenv("DB_PORT", 3306))
        )
        return connection
    except Error as e:
        print(f"CRITICAL: Database connection failed: {e}")
        raise e

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

    def get_system_prompt(self) -> str:
        return """
            You are an expert cybersecurity analyst. Your only task is to analyze an email and determine if it is phishing or safe.
            
            CRITICAL RULES:
            1. ZERO TRUST POLICY: If an email contains ANY suspicious elements (e.g., unexpected links, slight urgency, unusual requests), flag it as phishing. Do not give the sender the benefit of the doubt.
            2. Flag subtle manipulation: Even if an email looks like standard corporate communication or an automated newsletter, flag it if it attempts to harvest credentials, bypass standard procedures, or manipulate the recipient.
            3. Do not assume an email is safe just because it lacks an obvious malicious link; pure social engineering attempts must be flagged.
            4. If ambiguous or you are unsure, default to Phishing ("is_phishing": true).
            5. You must return a raw JSON object and absolutely nothing else.
        """

    def get_prompt(self, email: str) -> str:
        return f"""
            Here are examples of how to classify emails:

            --- EXAMPLE 1: Safe Email ---
            Email: "Ok, Iknow this is blatantly OT but I'm beginning to go insane.\nHad an old Dell Dimension XPS sitting in the corner and decided to\nput it to use, I know it was working pre being stuck in the\ncorner, but when I plugged it in, hit the power nothing happened.\nI opened her up and had a look and say nothing much. A little orange\nLED comes on when I plug her in but that's it, after some googling\nI found some reference to re-seating all the parts, but no change.\nThe problem I'm having is that since the power supply is some Dell\nspecific one, ATX block with what looks like one of the old AT\npower connectors, I cant figure out weather this is a Mobo prob\nor a PSU prob. Just to futily try and drag this back OT, I want\nto install Linux on it when I get it working. If anyone knows\nwhat the problem might be give me a shout.Cheers,\nPeter.--\nPeter Aherne, Software Engineer, \nMotorola Ireland Ltd.\nPh: +353 21 4511234 Mobile: +353 87 2246834-- \nIrish Linux Users' Group: ilug@linux.ie\nhttp://www.linux.ie/mailman/listinfo/ilug for (un)subscription information.\nList maintainer: listmaster@linux.ie"
            Output:
            {{
                "explanation": "Technical support inquiry sent to a public mailing list. It contains a verifiable signature block with standard contact details, lacks any fabricated urgency or requests for sensitive information, and the included URL is a standard, safe mailing list administrative link. While the email has some spelling errors, it does not contain any of the common indicators of phishing such as suspicious links, requests for sensitive information, or unrealistic offers. The tone and content are consistent with a legitimate technical support request.",
                "risk_level": "Low",
                "is_phishing": false
            }}

            --- EXAMPLE 2: Phishing Email ---
            Email: 'emailing : mon , 30 aug 2004 19 : 28 : 52 - 0800 dear sir / madam ; from our records we understand that you are inquiring about a new profession . we have a limited , ont time offer . our university can offer you a pre - qualified degree in your field of choice . we offer signing bonuses of up to $ 15 , 000 in your profession . to obtain your degree with valid transcripts & information on new career bonusus , follow our link : sincerely , dr . julie paige administration office this communication is of private matter . if you have received this and ar enot the individual or group it may concern or show interest in this please follow so we know http : / / 1 highereducation . com / st . html and the proper measures will proficiently expidited in a timely manner .'
            Output:
            {{
                "explanation": "Uses a generic greeting, contains multiple spelling and grammatical errors ('ont time', 'bonusus', 'expidited'), offers highly big unrealistic financial incentive ('$ 15 , 000') for a 'pre-qualified degree'. Too good to be true. Directs the victim to a suspicious, unofficial domain. The email also mentions 'limited on time offer' which is a common tactic to create urgency and pressure the recipient into acting without due consideration. All of these are strong indicators of a phishing attempt.",
                "risk_level": "High",
                "is_phishing": true
            }}

            --- EXAMPLE 3: Phishing Email ---
            Email: "returned mail : see transcript for details the original message was received at tue , 19 jul 2005 07 : 06 : 09 - 0400 from root @ localhost - - - - - the following addresses had permanent fatal errors - - - - - antique ( reason : can \' t create ( user ) output file ) ( expanded from : ) - - - - - transcript of session follows - - - - - procmail : quota exceeded while writing " / var / spool / mail / antique " 550 5 . 0 . 0 antique . . . can \' t create output"
            Output:
            {{
                "explanation": "This is a classic 'Fake NDR' (Non-Delivery Report) or 'Quota Exceeded' spoof. The email mimics an automated server error ('fatal errors', 'quota exceeded') to create sudden panic or confusion. Phishers frequently spoof these administrative bounce messages to trick victims into clicking a malicious link to 'upgrade their quota' or 'view the undelivered message', bypassing the victim's natural skepticism of external emails.",
                "risk_level": "High",
                "is_phishing": true
            }}

            --- EXAMPLE 4: Safe Email ---
            Email: "please grant access : application request ( kker - 4 r 3 klb ) security resource line item request kker - 4 r 3 klb has been submitted for your processing . to view the request , click your left mouse button on the notes document link below ."
            Output:
            {{
                "explanation": "Appears to be a legitimate, automated internal IT or ticketing system notification. It includes a highly specific, standard-formatted reference tracking code ('kker - 4 r 3 klb') and uses dry, administrative language. It does not threaten negative consequences or create artificial urgency. The instruction to click a 'notes document link' is standard operational practice for legacy enterprise environments (like Lotus Notes).",
                "risk_level": "Low",
                "is_phishing": false
            }}
            
            --- EXAMPLE 5: Safe Email ---
            Email: 'hpl nom for may 11 , 2001 ( see attached file : hplno 511 . xls ) - hplno 511 . xls'
            Output:
            {{
                "explanation": "This is a routine, automated or highly abbreviated B2B transactional email. It uses specific operational shorthand ('hpl nom', indicating a daily business nomination) paired with a specific date. The attached spreadsheet ('hplno 511 . xls') directly correlates with the date (May 11 -> 5/11) and the context of the message. It contains zero social engineering indicators, no artificial urgency, and no requests for credentials, pointing to a standard, safe internal workflow.",
                "risk_level": "Low",
                "is_phishing": false
            }}

            --- ACTUAL TASK ---
            Analyse this email for phishing indicators.
            Email: "{email}"

            Return a raw JSON object with this exact structure:
            {{
                "explanation": "Step-by-step reasoning of the technical and social indicators...",
                "risk_level": "Low" | "Medium" | "High",
                "is_phishing": true/false
            }}
        """
    

# Concrete class for Google GenAI, implementing the AIModelAdaptor interface
class GoogleGenAIAdaptor(AIModelAdaptor):
    def __init__ (self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    def analyse(self, email: str) -> dict:
        system_rules = self.get_system_prompt()
        prompt = self.get_prompt(email)
        print(f"Generated prompt for Google GenAI:\n{prompt}\n")
        verdict = self.client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_rules,
                response_mime_type='application/json',
                temperature=0.0
            )
        )
        print(f"Received verdict from Google GenAI:\n{verdict.text}\n")
        return json.loads(verdict.text)


class LocalModelAdaptor(AIModelAdaptor):
    def __init__(self, model_name: str = 'llama3'):
        self.model_name = model_name
        self.api_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")

    def analyse(self, email: str) -> dict:
        system_rules = self.get_system_prompt()
        prompt = self.get_prompt(email)
        
        payload = {
            "model": self.model_name,
            "system": system_rules,
            "prompt": prompt,
            "format": "json",  # Forces local model into JSON mode
            "stream": False,
            "options": {
                "temperature": 0.0,
                "num_ctx": 4096
            }
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