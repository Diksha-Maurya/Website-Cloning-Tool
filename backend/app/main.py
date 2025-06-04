from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
import httpx # For making HTTP requests

# 1. Pydantic model for the request body
class CloneUrlRequest(BaseModel):
    target_url: HttpUrl # FastAPI will use this for validation

# 2. Initialize your FastAPI application
app = FastAPI(
    title="Orchids Website Cloner API",
    description="API for fetching website content to be cloned.",
    version="0.1.0",
)

# 3. Define your endpoint
@app.post("/clone_website", tags=["Cloning"]) # Added a tag for Swagger UI organization
async def process_url_for_cloning(request_data: CloneUrlRequest):
    """
    Receives a target URL, fetches its HTML content, and returns it.
    """
    url = str(request_data.target_url) # Convert HttpUrl to string for httpx
    print(f"Received URL to clone: {url}")

    try:
        # Standard headers to mimic a browser request
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive", # Often good to include
        }

        # Use httpx to make an asynchronous GET request
        async with httpx.AsyncClient(follow_redirects=True, timeout=20.0) as client:
            print(f"Attempting to fetch content from: {url}")
            response = await client.get(url, headers=headers)
            response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)

        html_content = response.text
        print(f"Successfully fetched content from {url}. Length: {len(html_content)} bytes.")

        # In the future, you will pass this html_content to an LLM for processing.
        # For now, we return it directly to the frontend for preview.
        return {
            "cloned_html": html_content,
            "message": f"Successfully fetched HTML from {url}."
        }

    except httpx.TimeoutException as exc:
        print(f"Timeout error while requesting {exc.request.url!r}: {exc}")
        raise HTTPException(status_code=408, detail=f"Request timed out while trying to fetch the URL: {url}. The site might be too slow or offline.")
    except httpx.RequestError as exc:
        print(f"An error occurred while requesting {exc.request.url!r}: {exc}")
        raise HTTPException(status_code=400, detail=f"Could not fetch URL: {url}. Error: {str(exc)}")
    except httpx.HTTPStatusError as exc:
        print(f"HTTP error {exc.response.status_code} while requesting {exc.request.url!r}: {exc}")
        raise HTTPException(status_code=exc.response.status_code, detail=f"Error fetching URL: {url}. Server responded with {exc.response.status_code}")
    except Exception as e:
        # Catch-all for any other unexpected errors
        print(f"An unexpected error occurred while processing {url}: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected server error occurred: {str(e)}")

# Optional: Add a root endpoint for basic API health check
@app.get("/", tags=["General"])
async def read_root():
    return {"message": "Welcome to the Orchids Website Cloner API!"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
