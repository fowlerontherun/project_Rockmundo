from pydantic import BaseModel
from typing import Optional, List
from datetime import date

class EducationSession(BaseModel):
    id: int
    student_id: int
    skill_id: int
    method: str  # 'lesson', 'tutorial', 'practice'
    teacher_id: Optional[int]
    location: Optional[str]
    start_date: date
    duration_days: int
    completed: bool