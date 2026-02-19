import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from core.config import settings 

app = FastAPI(title=settings.APP_NAME)

async def proxy_request(service_url: str, path: str, request: Request):
    """
    Helper function to forward a request to another service.
    """
    client = httpx.AsyncClient()
    url = f"{service_url}{path}"
    
    print(f"🔄 Proxying request to: {url}")

    # Strip problematic headers (like 'host', 'content-length')
    filtered_headers = {
        k.decode("utf-8"): v.decode("utf-8") 
        for k, v in request.headers.raw 
        if k.decode("utf-8").lower() not in ("host", "content-length")
    }

    try:
        body = await request.body()
        
        # Forward the request to the internal service
        resp = await client.request(
            method=request.method,
            url=url,
            headers=filtered_headers,
            content=body,
            timeout=300.0 
        )
        
        # Return the response from the internal service back to the client
        return JSONResponse(content=resp.json(), status_code=resp.status_code)

    except httpx.ConnectError:
        # Error handling if the internal service is down or unreachable
        return JSONResponse(
            content={"detail": f"Gateway Error: Could not connect to {service_url}"}, 
            status_code=502
        )
    except Exception as e:
        # General error handling
        return JSONResponse(
            content={"detail": f"Gateway Error: {str(e)}"}, 
            status_code=500
        )
    finally:
        await client.aclose()

# ---------------------------------------------------------
# Routes
# ---------------------------------------------------------

@app.get("/health")
async def health_check():
    """
    Simple health check to verify the Gateway is running.
    """
    return {"status": "alive", "service": "gateway"}

@app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def catch_all(path_name: str, request: Request):
    """
    Catch-all route.
    Forwards all incoming requests to the main Server Service.
    Example: /trips/generate -> http://server:8001/trips/generate
    """
    # Using settings.SERVER_URL (which is http://server:8001)
    return await proxy_request(settings.SERVER_URL, f"/{path_name}", request)