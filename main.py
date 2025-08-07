import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from datetime import datetime
import bcrypt
from supabase import create_client, Client
import joblib
import secrets
from typing import Optional


# Load env variables from .env file
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")



if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env file")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

# Enable CORS - adjust allow_origins for your frontend URL in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load your ML model (make sure 'ticket_classifier.pkl' is present)
model = None

# Pydantic models
class SignupInput(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginInput(BaseModel):
    email: EmailStr
    password: str

class ForgotPasswordInput(BaseModel):
    email: EmailStr

class ResetPasswordInput(BaseModel):
    email: str
    new_password: str
    token: Optional[str] = None


class EmailCheckRequest(BaseModel):
    email: str

class TicketRequest(BaseModel):
    user_id: str
    ticket_text: str

# Simulated email sender for forgot password (just prints the reset link)
def send_reset_email(email: str, reset_token: str):
    reset_link = f"http://localhost:3000/reset-password?token={reset_token}&email={email}"
    print(f"Password reset email sent to {email} with link: {reset_link}")
    # Later: integrate a real email sender service here if you want

# Signup endpoint
@app.post("/signup")
async def signup(user: SignupInput):
    try:
        existing_user = supabase.table("users").select("*").eq("email", user.email).execute()
        if existing_user.data and len(existing_user.data) > 0:
            raise HTTPException(status_code=400, detail="Email already registered")

        hashed_pw = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        response = supabase.table("users").insert({
            "name": user.name,
            "email": user.email,
            "password": hashed_pw,
            "created_at": datetime.utcnow().isoformat()
        }).execute()

        if response.data is None:
            raise HTTPException(status_code=400, detail="Failed to create user")

        user_data = response.data[0]
        return {
            "message": "User registered successfully",
            "user_id": user_data["user_id"],
            "name": user_data["name"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Login endpoint
@app.post("/login")
async def login(credentials: LoginInput):
    try:
        response = supabase.table("users").select("*").eq("email", credentials.email).execute()
        users = response.data

        if not users:
            raise HTTPException(status_code=404, detail="User not found")

        user = users[0]
        stored_password = user.get("password")

        if not stored_password or not bcrypt.checkpw(credentials.password.encode('utf-8'), stored_password.encode('utf-8')):
            raise HTTPException(status_code=401, detail="Incorrect password")

        return {
            "message": f"Welcome {user['name']}",
            "user_id": user["user_id"],
            "name": user["name"],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Predict endpoint (unchanged)
class TicketInput(BaseModel):
    user_id: int
    ticket_text: str

from fastapi import HTTPException
from datetime import datetime

model = None  # at the top level, outside any function

@app.post("/predict")
async def predict_ticket(ticket: TicketInput):
    global model
    try:
        if model is None:
            print("Loading model inside /predict...")
            model = joblib.load("ticket_classifier.pkl")
            print("Model loaded.")

        prediction = model.predict([ticket.ticket_text])[0]
        confidence_scores = model.predict_proba([ticket.ticket_text])[0]
        confidence = max(confidence_scores)

        # Insert ticket
        ticket_response = supabase.table("tickets").insert({
            "user_id": ticket.user_id,
            "ticket_text": ticket.ticket_text,
            "actual_department": prediction,
            "confidence_score": confidence,
            "submitted_at": datetime.utcnow().isoformat()
        }).execute()

        if ticket_response.data is None:
            raise HTTPException(status_code=400, detail="Failed to save ticket")

        ticket_id = ticket_response.data[0]["ticket_id"]  # Get inserted ticket ID

        # Insert prediction
        prediction_response = supabase.table("predictions").insert({
            "ticket_id": ticket_id,
            "predicted_department": prediction,
            "confidence_score": confidence,
            "created_at": datetime.utcnow().isoformat()
        }).execute()

        if prediction_response.data is None:
            raise HTTPException(status_code=400, detail="Failed to save prediction")

        return {
            "department": prediction,
            "confidence": confidence
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# History endpoint (unchanged)
@app.get("/history/{user_id}")
async def get_history(user_id: int):
    try:
        response = supabase.table("tickets").select("*").eq("user_id", user_id).order("submitted_at", desc=True).execute()
        tickets = response.data or []
        return {"history": tickets}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Forgot Password endpoint
@app.post("/forgot-password")
async def forgot_password(data: ForgotPasswordInput, background_tasks: BackgroundTasks):
    try:
        response = supabase.table("users").select("*").eq("email", data.email).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="No user found with this email")

        user = response.data[0]

        reset_token = secrets.token_urlsafe(32)

        supabase.table("users").update({"reset_token": reset_token}).eq("user_id", user["user_id"]).execute()

        # Send reset email (simulated, prints reset link)
        background_tasks.add_task(send_reset_email, data.email, reset_token)

        return {"message": "Reset password instructions sent to your email."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Reset Password endpoint
@app.post("/reset-password")
async def reset_password(data: ResetPasswordInput):
    if data.token:
        # do token validation
        response = supabase.table("users").select("*").eq("email", data.email).eq("reset_token", data.token).execute()
    else:
        # skip token, just check email
        response = supabase.table("users").select("*").eq("email", data.email).execute()

    if not response.data:
        raise HTTPException(status_code=400, detail="Invalid email or token")

    user = response.data[0]

    hashed_pw = bcrypt.hashpw(data.new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    supabase.table("users").update({
        "password": hashed_pw,
        "reset_token": None
    }).eq("user_id", user["user_id"]).execute()

    return {"message": "Password has been reset successfully."}


@app.post("/check-email")
def check_email(data: EmailCheckRequest):
    response = supabase.table("users").select("*").eq("email", data.email).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Email not found")
    return {"message": "Email found"}



import openai

# Load OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

class ChatInput(BaseModel):
    message: str

@app.post("/chat")
async def chat_with_gpt(input: ChatInput):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",  # or "gpt-3.5-turbo" if you want cheaper responses
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": input.message}
            ]
        )
        reply = response["choices"][0]["message"]["content"]
        return {"reply": reply}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    



# from fastapi import FastAPI

# app = FastAPI()

# @app.get("/")
# def read_root():
#     return {"message": "It works"}

