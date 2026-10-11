from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.password import validate_password

@app.get("/")
def read_root():
    return {"message": "Hello World"}


@app.post("/validate_password")
def validate_password_route(password: str):
    return {"is_valid": validate_password(password)}
