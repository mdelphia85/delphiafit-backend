from fastapi import FastAPI

app = FastAPI()

from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"status": "backend is running"}
