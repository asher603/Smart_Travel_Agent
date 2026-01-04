import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os

app = FastAPI(title="Smart Travel Gateway")

# --- FIX: Default to the Docker Service Name ---
APP_SERVER_URL = os.getenv("APP_SERVER_URL", "http://travel_app_server:8000")

async def proxy_request(service_url: str, path: str, request: Request):
    client = httpx.AsyncClient()
    url = f"{service_url}{path}"
    try:
        body = await request.body()
        resp = await client.request(
            method=request.method,
            url=url,
            headers=request.headers.raw,
            content=body,
            timeout=60.0 
        )
        return JSONResponse(content=resp.json(), status_code=resp.status_code)
    except Exception as e:
        return JSONResponse(content={"detail": f"Gateway Error: {str(e)}"}, status_code=503)
    finally:
        await client.aclose()

# Catch-all Route (Proxies everything to App Server)
@app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def catch_all(path_name: str, request: Request):
    # This forwards "/trips/generate" -> "http://travel_app_server:8000/trips/generate"
    return await proxy_request(APP_SERVER_URL, f"/{path_name}", request)