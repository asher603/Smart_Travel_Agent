import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Smart Travel Gateway")

# Service URLs (from Docker/Env)
APP_SERVER_URL = os.getenv("APP_SERVER_URL", "http://localhost:8003")
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8001")

# --- Helper Proxy Function ---
async def proxy_request(service_url: str, path: str, request: Request):
    """Forwards the incoming request to the target microservice."""
    client = httpx.AsyncClient()
    url = f"{service_url}{path}"
    
    try:
        # Forward method, headers, and body
        body = await request.body()
        resp = await client.request(
            method=request.method,
            url=url,
            headers=request.headers.raw,
            content=body,
            timeout=60.0 
        )
        return JSONResponse(content=resp.json(), status_code=resp.status_code)
    except httpx.RequestError as e:
        return JSONResponse(content={"error": f"Service unavailable: {str(e)}"}, status_code=503)
    finally:
        await client.aclose()

# --- Routes ---

# 1. AI Routes -> Direct to AI Service (Optional, usually goes via App Server)
@app.post("/generate_trip")
async def ai_proxy(request: Request):
    return await proxy_request(AI_SERVICE_URL, "/generate_trip", request)

# 2. App Server Routes (The main backend)
# Catches all other paths (auth, trips, weather, etc.)
@app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def catch_all(path_name: str, request: Request):
    return await proxy_request(APP_SERVER_URL, f"/{path_name}", request)