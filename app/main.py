from fastapi import FastAPI
from app.auth.routes import router as auth_router

app = FastAPI()

@app.get("/")
def root():
    return {"status": "backend is running"}

app.include_router(auth_router)

