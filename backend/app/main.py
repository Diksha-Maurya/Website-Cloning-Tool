# backend/app/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
import httpx
import os                  # For accessing environment variables
from dotenv import load_dotenv # To load variables from .env
import google.generativeai as genai # Google Gemini SDK
from fastapi.middleware.cors import CORSMiddleware

# --- Load environment variables from .env file ---
# This should be at the top level of your module to ensure variables are loaded on startup.
load_dotenv()

# --- Configure the Gemini API Key ---
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GEMINI_API_KEY:
    print("🔴 WARNING: GOOGLE_API_KEY not found in environment variables. LLM calls will fail.")
    # You might want to raise an error or exit if the API key is critical for startup,
    # but for now, we'll let it proceed and fail at runtime if used.
else:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        print("🟢 Gemini API Key configured successfully.")
    except Exception as e:
        print(f"🔴 ERROR: Failed to configure Gemini API: {e}")

# --- Pydantic Model for Request ---
class CloneUrlRequest(BaseModel):
    target_url: HttpUrl

# --- FastAPI App Instance ---
app = FastAPI(
    title="Orchids Website Cloner API",
    description="API for fetching website content and attempting an aesthetic clone using Google Gemini.",
    version="0.3.0", # Version bump
)

# --- Configure CORS ---
# Define the list of origins that are allowed to make requests.
# You should include the URL your frontend is served from.
# Using "http://localhost:3000" for local development is common.
# And specifically "http://192.168.0.237:3000" as seen in your browser.
origins = [
    "http://localhost:3000",        # For local Next.js dev default
    "http://127.0.0.1:3000",      # Another way to access localhost
    f"http://{os.getenv('HOSTNAME')}:3000", # If HOSTNAME is set and frontend runs there (less common for this setup)
    "http://192.168.0.237:3000",    # The IP address your browser is using for the frontend
    # You can add more origins if needed, or use ["*"] for development to allow all,
    # but be more specific for production.
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows specific origins
    # allow_origins=["*"],  # Allows all origins (use for development/testing if specific origins don't work immediately, but be cautious)
    allow_credentials=True, # Allows cookies (not strictly needed for this app yet, but good practice)
    allow_methods=["*"],    # Allows all methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],    # Allows all headers
)


# --- Helper Function for Gemini API Call ---
async def generate_html_with_gemini(original_html: str, site_url: str) -> str:
    if not GEMINI_API_KEY: # Double-check, though initial configuration should handle this
        raise HTTPException(status_code=500, detail="LLM API key not configured or missing.")

    print(f"Attempting to generate HTML clone for {site_url} using Gemini.")
    
    # Choose your model. 'gemini-1.5-flash-latest' is fast and capable.
    # 'gemini-1.0-pro-latest' or 'gemini-1.5-pro-latest' are more powerful options.
    model_name = 'gemini-1.5-flash-latest' 
    try:
        model = genai.GenerativeModel(model_name)
    except Exception as e:
        print(f"🔴 ERROR: Failed to initialize Gemini model '{model_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize LLM model: {str(e)}")

    # --- Constructing the Prompt (CRITICAL STEP!) ---
    # This is a starting point. You will need to iterate and refine this extensively.
    # Consider the ~128k token context window for gemini-1.5-flash.
    # Truncate original_html if it's too long.
    max_html_length = 70000  # Approx characters, adjust based on token limits and typical HTML size
    if len(original_html) > max_html_length:
        print(f"Original HTML is too long ({len(original_html)} chars), truncating to {max_html_length} chars for prompt.")
        truncated_html = original_html[:max_html_length] + "\n...[TRUNCATED]..."
    else:
        truncated_html = original_html

    # Inside generate_html_with_gemini function in main.py

    prompt = f"""
    You are an AI web designer tasked with creating an aesthetic HTML clone of a given website.
    Your goal is to replicate the visual appearance, layout, **original color scheme (including background and text colors)**, and typography using a *single, self-contained HTML file*.

    **Key Instructions for Color:**
    * Pay close attention to the **original background color** of the page (e.g., white, light gray, black, etc.).
    * Pay close attention to the **primary text color** used on that background.
    * Replicate this **exact background-text color pairing**. For instance, if the original is black text on a white background, your clone must also have black text on a white background.
    * Preserve the color of hyperlinks if discernible.

    **General Instructions:**
    1.  Analyze the provided HTML structure and content for its aesthetic qualities.
    2.  Generate a *new* HTML structure. Do NOT simply copy the input HTML.
    3.  Use inline CSS or a single `<style>` block within the `<head>` for all styling. Do not use external CSS files.
    4.  Do NOT include any JavaScript or `<script>` tags.
    5.  Focus on visual fidelity to the original, especially the color palette.
    6.  The output must be ONLY the complete HTML code, starting with `<!DOCTYPE html>` or `<html>` and ending with `</html>`.
    7.  Do not include any explanations, comments, or markdown formatting (like ```html) outside of the HTML code itself.

    **Original Website URL (for context only):** {site_url}

    **Original Website HTML (for aesthetic reference - may be truncated):**
    ```html
    {truncated_html}
    ```

    Now, generate the new, self-contained HTML code that aesthetically clones the site, ensuring the background and text colors match the original:
    """

    print(f"Sending prompt to Gemini (model: {model_name}). Prompt length: ~{len(prompt)} chars.")

    try:
        # Using await for async call within an async function
        response = await model.generate_content_async(
            prompt,
            # Optional: Add generation_config for more control
            # generation_config=genai.types.GenerationConfig(
            #     candidate_count=1,
            #     max_output_tokens=8192, # Max for gemini-1.5-flash
            #     temperature=0.7,
            # )
        )
        
        generated_html = response.text.strip()
        print(f"Received response from Gemini. Raw length: {len(generated_html)} chars.")

        # --- Basic Cleanup of LLM Output ---
        # LLMs sometimes wrap their output in markdown code blocks.
        if generated_html.startswith("```html"):
            generated_html = generated_html[len("```html"):].strip()
        if generated_html.startswith("```"): # More generic markdown fence
            generated_html = generated_html[len("```"):].strip()
        if generated_html.endswith("```"):
            generated_html = generated_html[:-len("```")].strip()
        
        if not generated_html:
            print("🔴 WARNING: LLM returned an empty response after cleanup.")
            # Consider what to do here. Maybe return an error or a default message.
            # For now, we'll let it pass and the frontend will show an empty preview.
            # raise HTTPException(status_code=500, detail="LLM returned an empty response.")

        print(f"Cleaned LLM HTML length: {len(generated_html)} chars.")
        return generated_html

    except Exception as e:
        print(f"🔴 ERROR: An error occurred during Gemini API call or processing: {e}")
        # Check for specific Gemini API errors if possible (e.g., content filtering, quota)
        # The SDK might raise specific exception types.
        # For example, if hasattr(e, 'prompt_feedback') and e.prompt_feedback.block_reason:
        #     reason = e.prompt_feedback.block_reason
        #     detail_msg = f"LLM content generation blocked. Reason: {reason}."
        #     if e.prompt_feedback.safety_ratings:
        #         detail_msg += f" Safety Ratings: {e.prompt_feedback.safety_ratings}"
        #     raise HTTPException(status_code=400, detail=detail_msg)
        raise HTTPException(status_code=500, detail=f"Failed to generate HTML with LLM: {str(e)}")


# --- FastAPI Endpoint ---
@app.post("/clone_website", tags=["Cloning"])
async def process_url_for_cloning(request_data: CloneUrlRequest):
    url_to_clone = str(request_data.target_url)
    print(f"🚀 Received request to clone URL: {url_to_clone}")

    # 1. Scrape original HTML
    original_html = ""
    try:
        print(f"Attempting to scrape: {url_to_clone}")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        # Increased timeout for potentially slower sites
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            response = await client.get(url_to_clone, headers=headers)
            response.raise_for_status()  # Raise HTTPStatusError for bad responses (4xx or 5xx)
        original_html = response.text
        print(f"✅ Successfully scraped HTML from {url_to_clone}. Length: {len(original_html)} bytes.")
    except httpx.HTTPStatusError as exc:
        print(f"🔴 HTTP error {exc.response.status_code} while scraping {exc.request.url!r}.")
        raise HTTPException(status_code=exc.response.status_code, detail=f"Error scraping original URL: Server responded with {exc.response.status_code}")
    except httpx.RequestError as exc:
        print(f"🔴 An error occurred while scraping {exc.request.url!r}: {exc}")
        raise HTTPException(status_code=400, detail=f"Could not scrape original URL. Error: {str(exc)}")
    except Exception as e: # Catch any other unexpected error during scraping
        print(f"🔴 Unexpected error during scraping of {url_to_clone}: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error scraping URL: {str(e)}")

    # 2. Call LLM to generate cloned HTML
    if not original_html: # Should not happen if scraping was successful and raised no error
        raise HTTPException(status_code=500, detail="Scraping yielded no content.")
        
    try:
        llm_generated_html = await generate_html_with_gemini(original_html, url_to_clone)
        print(f"✅ LLM processing complete for {url_to_clone}.")
        return {
            "cloned_html": llm_generated_html,
            "message": f"Successfully generated aesthetic clone for {url_to_clone} using LLM."
        }
    except HTTPException: # Re-raise HTTPExceptions from the LLM helper directly
        raise
    except Exception as e: # Catch any other unexpected error during LLM call
        print(f"🔴 Unexpected error during LLM processing for {url_to_clone}: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected server error during LLM processing: {str(e)}")


# --- Root Endpoint ---
@app.get("/", tags=["General"])
async def read_root():
    return {"message": "Welcome to the Orchids Website Cloner API! Powered by Google Gemini."}