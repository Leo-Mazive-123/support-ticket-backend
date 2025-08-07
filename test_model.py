from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class User(BaseModel):
    user_id: str
    name: str
    email: str
    created_at: Optional[datetime]

class Ticket(BaseModel):
    ticket_id: Optional[int]
    user_id: str
    ticket_text: str
    submitted_at: Optional[datetime]
    actual_department: Optional[str]

class Prediction(BaseModel):
    prediction_id: Optional[int]
    ticket_id: int
    predicted_department: str
    confidence_score: float
    predicted_at: Optional[datetime]

class Department(BaseModel):
    department_id: Optional[int]
    name: str
