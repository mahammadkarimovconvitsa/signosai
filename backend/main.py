import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "main.json"

app = FastAPI(title="SignalOS API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_data() -> dict:
    with DATA_PATH.open() as f:
        return json.load(f)


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/api/data")
def get_data():
    return load_data()


@app.get("/api/users")
def get_users():
    return load_data()["users"]


@app.get("/api/items")
def get_items():
    return load_data()["items"]


@app.get("/api/users/{user_id}")
def get_user(user_id: int):
    users = load_data()["users"]
    for user in users:
        if user["id"] == user_id:
            return user
    raise HTTPException(status_code=404, detail="User not found")
