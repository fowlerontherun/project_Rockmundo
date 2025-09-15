from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.models.skill import Skill
from routes import schedule_routes
from backend.services.plan_service import PlanService
from backend.services.skill_service import skill_service


def setup_function(_):
    skill_service._skills.clear()


def test_recommendations_use_skill_levels():
    user_id = 1
    skill_service._skills[(user_id, 1)] = Skill(id=1, name='guitar', category='music', xp=200, level=3)
    skill_service._skills[(user_id, 2)] = Skill(id=2, name='songwriting', category='creative', xp=600, level=7)
    svc = PlanService()
    recs = svc.recommend_activities(user_id, ['guitar', 'songwriting'])
    assert recs == ['practice guitar', 'perform songwriting']


def test_recommendation_endpoint():
    user_id = 2
    skill_service._skills[(user_id, 1)] = Skill(id=1, name='guitar', category='music', xp=50, level=1)
    app = FastAPI()
    app.include_router(schedule_routes.router)
    client = TestClient(app)
    resp = client.post('/schedule/recommend', json={'user_id': user_id, 'goals': ['guitar']})
    assert resp.status_code == 200
    assert resp.json()['recommendations'] == ['practice guitar']
