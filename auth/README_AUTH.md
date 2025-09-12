# Auth & RBAC (JWT + Refresh)

## Env (.env)
```
ROCKMUNDO_JWT_SECRET=change-me
ROCKMUNDO_JWT_ISS=rockmundo
ROCKMUNDO_JWT_AUD=rockmundo-app
ROCKMUNDO_ACCESS_TTL_MIN=30
ROCKMUNDO_REFRESH_TTL_DAYS=30
```
## Wire-up
```python
from auth.routes import router as auth_router
app.include_router(auth_router)
```
## Migrate
Run `backend/migrations/010_auth_and_rbac.sql`
