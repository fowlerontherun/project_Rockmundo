from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from utils.i18n import _

from auth.dependencies import get_current_user_id
from backend.services.social_service import social_service

router = APIRouter(prefix="/social", tags=["social"])


# ----- Friend endpoints -----
class FriendRequestIn(BaseModel):
    to_user_id: int


@router.post("/friends/request")
async def send_friend_request(data: FriendRequestIn, user_id: int = Depends(get_current_user_id)):
    req = await social_service.send_friend_request(user_id, data.to_user_id)
    return req


@router.post("/friends/{request_id}/accept")
async def accept_friend_request(request_id: int, user_id: int = Depends(get_current_user_id)):
    try:
        await social_service.accept_friend_request(request_id, user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=_("Invalid friend request"))
    return {"status": "accepted"}


@router.post("/friends/{request_id}/reject")
async def reject_friend_request(request_id: int, user_id: int = Depends(get_current_user_id)):
    try:
        await social_service.reject_friend_request(request_id, user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=_("Invalid friend request"))
    return {"status": "rejected"}


@router.get("/friends")
async def list_friends(user_id: int = Depends(get_current_user_id)):
    return social_service.list_friends(user_id)


# ----- Group endpoints -----
class GroupCreateIn(BaseModel):
    name: str


@router.post("/groups")
async def create_group(data: GroupCreateIn, user_id: int = Depends(get_current_user_id)):
    grp = social_service.create_group(user_id, data.name)
    return grp


@router.post("/groups/{group_id}/join")
async def join_group(group_id: int, user_id: int = Depends(get_current_user_id)):
    try:
        social_service.join_group(group_id, user_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=_("Group not found"))
    return {"status": "joined"}


@router.post("/groups/{group_id}/leave")
async def leave_group(group_id: int, user_id: int = Depends(get_current_user_id)):
    try:
        social_service.leave_group(group_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "left"}


@router.get("/groups/{group_id}/members")
async def list_group_members(group_id: int, user_id: int = Depends(get_current_user_id)):
    # ensure group exists
    if group_id not in social_service._groups:
        raise HTTPException(status_code=404, detail=_("Group not found"))
    return social_service.list_group_members(group_id)


# ----- Forum endpoints -----
class ThreadCreateIn(BaseModel):
    title: str
    group_id: int | None = None


@router.post("/threads")
async def create_thread(data: ThreadCreateIn, user_id: int = Depends(get_current_user_id)):
    thread = social_service.create_thread(user_id, data.title, data.group_id)
    return thread


class PostCreateIn(BaseModel):
    content: str
    parent_post_id: int | None = None


@router.post("/threads/{thread_id}/posts")
async def add_post(thread_id: int, data: PostCreateIn, user_id: int = Depends(get_current_user_id)):
    try:
        post = await social_service.add_post(thread_id, user_id, data.content, data.parent_post_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return post


@router.get("/threads/{thread_id}")
async def get_thread(thread_id: int, user_id: int = Depends(get_current_user_id)):
    if thread_id not in social_service._threads:
        raise HTTPException(status_code=404, detail=_("Thread not found"))
    posts = social_service.get_thread_posts(thread_id)
    return {"thread": social_service._threads[thread_id], "posts": posts}
