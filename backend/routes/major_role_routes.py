from fastapi import APIRouter
from schemas.major_role_schema import MajorCreate, RoleAssignmentCreate
from models.major_role import Major, RoleAssignment
from typing import List

router = APIRouter()
majors: List[Major] = []
roles: List[RoleAssignment] = []
major_id = 1

@router.post("/majors/", response_model=Major)
def create_major(data: MajorCreate):
    global major_id
    new_major = Major(
        id=major_id,
        name=data.name,
        description=data.description,
        perks=data.perks,
        members=[],
        leader_id=None
    )
    majors.append(new_major)
    major_id += 1
    return new_major

@router.post("/majors/assign_role/")
def assign_role(data: RoleAssignmentCreate):
    for major in majors:
        if major.id == data.major_id:
            major.members.append(data.user_id)
            roles.append(RoleAssignment(**data.dict()))
            return {"message": "Role assigned"}
    return {"error": "Major not found"}

@router.get("/majors/", response_model=List[Major])
def get_all_majors():
    return majors