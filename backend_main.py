from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()


@app.get("/", response_class=JSONResponse)
async def root():
    """
    Simple health‑check endpoint.
    Returns a JSON payload confirming the service is up.
    """
    return {"message": "Hello, World!"}


# ---------------------------------------------------------------------------
# Test client
# ---------------------------------------------------------------------------
# The test suite expects a global ``client`` object that can be used to issue
# requests against the FastAPI application without having to spin up an
# external server.  By creating a ``TestClient`` instance at import time we
# provide that object directly from this module, allowing the tests to do:
#
#     from backend_main import client
#     response = client.get("/")
#
# This mirrors the typical pattern used in FastAPI documentation and keeps
# the test code simple.
# ---------------------------------------------------------------------------
from fastapi.testclient import TestClient

client = TestClient(app)
