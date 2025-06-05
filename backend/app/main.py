# backend/app/main.py
import sys
import asyncio
if sys.platform == "win32" and sys.version_info >= (3, 8):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
import httpx 
import os
from dotenv import load_dotenv
import google.generativeai as genai
from fastapi.middleware.cors import CORSMiddleware
from playwright.async_api import async_playwright


print(f"--- Main.py Top Level ---")
print(f"Python version: {sys.version_info}")
print(f"Platform: {sys.platform}")
print(f"Initial asyncio event loop policy: {type(asyncio.get_event_loop_policy()).__name__}")


load_dotenv()
print("Environment variables loaded (or attempted).")

GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")


if not GEMINI_API_KEY:
    print("🔴 WARNING: GOOGLE_API_KEY not found. LLM calls will fail.")
else:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        print("🟢 Gemini API Key configured successfully.")
    except Exception as e:
        print(f"🔴 ERROR: Failed to configure Gemini API: {e}")

class CloneUrlRequest(BaseModel):
    target_url: HttpUrl

app = FastAPI(
    title="Orchids Website Cloner API",
    description="API for fetching website content using local Playwright and aesthetic cloning using Google Gemini.",
    version="0.6.0",
)
origins = [
    "http://localhost:3000", "http://127.0.0.1:3000",
    f"http://{os.getenv('HOSTNAME')}:3000", "http://192.168.0.237:3000",
]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

async def scrape_with_local_playwright(target_url: str) -> str:
    print(f"Attempting to scrape {target_url} using local Playwright.")
    html_content = ""
    pw_instance = None
    browser = None
    try:
        pw_instance = await async_playwright().start()

        browser = await pw_instance.chromium.launch(headless=True) 
        page = await browser.new_page()

        print(f"Navigating to {target_url} with local Playwright...")
        await page.goto(target_url, wait_until="networkidle", timeout=60000) # 60 seconds

        page_title = await page.title()
        print(f"Page title from local Playwright: '{page_title}'")

        html_content = await page.content()

        if not html_content:
            print("🔴 WARNING: Local Playwright returned empty HTML content.")
            raise HTTPException(status_code=500, detail="Local Playwright returned empty HTML content.")

        print(f"✅ Successfully scraped with local Playwright. HTML length: {len(html_content)}")
        return html_content

    except Exception as e:
        import traceback
        detailed_error_trace = traceback.format_exc()
        error_type = type(e).__name__
        print(f"🔴 ERROR during local Playwright operation: {error_type} - {e}")
        print(f"🔴 Full Traceback for Playwright error:\n{detailed_error_trace}")
        raise HTTPException(status_code=500, detail=f"Error during local Playwright scraping: {error_type} - {str(e)}")

    finally:
        if browser:
            await browser.close()
            print("Playwright browser closed.")
        if pw_instance:
            await pw_instance.stop() 
            print("Playwright instance stopped.")


async def generate_html_with_gemini(original_html: str, site_url: str) -> str:
    if not GEMINI_API_KEY: raise HTTPException(status_code=500, detail="LLM API key not configured or missing.")
    print(f"Attempting to generate HTML clone for {site_url} using Gemini.")
    model_name = 'gemini-1.5-flash-latest'; model = genai.GenerativeModel(model_name)
    max_html_length = 70000
    truncated_html = original_html[:max_html_length] + "\n...[TRUNCATED]..." if len(original_html) > max_html_length else original_html
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
    print(f"Sending prompt to Gemini (model: {model_name}).")
    response = await model.generate_content_async(prompt)
    generated_html = response.text.strip()
    if generated_html.startswith("```html"): generated_html = generated_html[len("```html"):].strip()
    if generated_html.startswith("```"): generated_html = generated_html[len("```"):].strip()
    if generated_html.endswith("```"): generated_html = generated_html[:-len("```")].strip()
    if not generated_html: print("🔴 WARNING: LLM returned an empty response after cleanup.")
    print(f"Cleaned LLM HTML length: {len(generated_html)} chars.")
    return generated_html

@app.post("/clone_website", tags=["Cloning"])
async def process_url_for_cloning(request_data: CloneUrlRequest):
    url_to_clone = str(request_data.target_url)
    print(f"🚀 Received request to clone URL (using local Playwright): {url_to_clone}")

    original_html = ""
    try:
        original_html = await scrape_with_local_playwright(url_to_clone)
    except HTTPException:
        raise
    except Exception as e:
        print(f"🔴 Unexpected error during local Playwright scraping dispatch for {url_to_clone}: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error preparing to scrape URL with local Playwright: {str(e)}")

    if not original_html: 
        raise HTTPException(status_code=500, detail="Scraping via local Playwright yielded no content.")

    try:
        llm_generated_html = await generate_html_with_gemini(original_html, url_to_clone)
        print(f"✅ LLM processing complete for {url_to_clone}.")
        return {
            "cloned_html": llm_generated_html,
            "message": f"Successfully generated aesthetic clone for {url_to_clone} using LLM and local Playwright."
        }
    except HTTPException: 
        raise
    except Exception as e: 
        print(f"🔴 Unexpected error during LLM processing for {url_to_clone}: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected server error during LLM processing: {str(e)}")

@app.get("/", tags=["General"])
async def read_root():
    return {"message": "Welcome to the Orchids Website Cloner API! Powered by local Playwright and Google Gemini."}