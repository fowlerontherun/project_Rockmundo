from pydantic import BaseModel
from typing import Optional, List
import datetime

# Example schema - customize fields as needed
class ExampleSchema(BaseModel):
    id: int
    name: str
