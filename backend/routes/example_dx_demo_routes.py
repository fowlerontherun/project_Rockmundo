from fastapi import APIRouter, status
from pydantic import BaseModel, Field, EmailStr
from typing import List
from ..core.responses import std_error_responses
from ..core.openapi import add_auth_example

router = APIRouter(prefix="/dx-demo", tags=["DX Demo"])


class CreateUserReq(BaseModel):
    email: EmailStr = Field(..., examples=["user@example.com"])
    name: str = Field(..., min_length=1, max_length=80, examples=["Pat Developer"])


class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: str


@router.post(
    "/users",
    summary="Create a user (demo)",
    response_model=UserOut,
    responses=std_error_responses(),
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "examples": {
                        "basic": {"value": {"email": "user@example.com", "name": "Pat Developer"}}
                    }
                }
            }
        },
        "responses": {
            "200": {
                "description": "Created user example",
                "content": {
                    "application/json": {
                        "examples": {"ok": {"value": {"id": 1, "email": "user@example.com", "name": "Pat Developer"}}}
                    }
                }
            }
        },
    },
)
async def create_user_demo(body: CreateUserReq) -> UserOut:
    return UserOut(id=1, email=body.email, name=body.name)


@router.get(
    "/users",
    summary="List users (demo)",
    response_model=list[UserOut],
    responses=std_error_responses(),
)
async def list_users_demo() -> List[UserOut]:
    return [UserOut(id=1, email="user@example.com", name="Pat Developer")]


def _attach_examples(router: APIRouter):
    for route in router.routes:
        if hasattr(route, "methods"):
            add_auth_example(route)


_attach_examples(router)
