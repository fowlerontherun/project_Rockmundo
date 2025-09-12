from pydantic import BaseModel
from typing import Optional
from datetime import date

class EducationSessionCreate(BaseModel):
    student_id: int
    skill_id: int
    method: str  # 'lesson', 'tutorial', 'practice'
    teacher_id: Optional[int] = None
    location: Optional[str] = None
    duration_days: int

class EducationSessionResponse(EducationSessionCreate):
    id: int
    start_date: date
    completed: bool