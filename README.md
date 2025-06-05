# Orchids SWE Intern Challenge: AI Website Cloner

This project is a submission for the Orchids Software Engineering Internship Challenge. It's a web application that takes a public website URL, scrapes its content (including JavaScript-rendered parts), and then uses a Large Language Model (Google Gemini) to attempt an aesthetic clone of the original website in HTML.

## Project Overview

The goal is to create a minimal version of a website cloning feature. The application consists of:
* A Next.js + TypeScript frontend where users can input a URL.
* A Python + FastAPI backend that handles:
    * Scraping the target website using local Playwright to ensure JavaScript-rendered content is captured.
    * Interfacing with the Google Gemini API to generate an HTML clone based on the scraped content.
* A preview area in the frontend to display the LLM-generated HTML clone.

## Tech Stack

* **Frontend:** Next.js, TypeScript, React
* **Backend:** Python, FastAPI, Uvicorn
* **Scraping:** Playwright (local instance)
* **LLM:** Google Gemini API (via `google-generativeai` SDK)
* **Package Management (Backend):** `uv`
* **Environment Management (Backend):** `python-dotenv`

## Setup Instructions

### Prerequisites

* Node.js (v18 or later recommended)
* Python (v3.8 or later recommended. This project was developed with Python 3.13.3, see "Important Notes" for Windows users)
* `uv` (Python package manager, `pip install uv`)
* Git (for cloning, if applicable)

### Backend Setup

1.  **Navigate to the Backend Directory:**
    ```bash
    cd backend
    ```

2.  **Create Virtual Environment (Recommended):**
    ```bash
    uv venv
    ```
    Activate it:
    * Windows: `.venv\Scripts\activate`
    * macOS/Linux: `source .venv/bin/activate`

3.  **Install Dependencies:**
    ```bash
    uv sync
    ```

4.  **Set Up Environment Variables:**
    * Create a file named `.env` in the `backend` directory.
    * Add your Google Gemini API key to this file:
        ```env
        GOOGLE_API_KEY="YOUR_GOOGLE_GEMINI_API_KEY"
        ```
        Replace `YOUR_GOOGLE_GEMINI_API_KEY` with your actual key.

5.  **Install Playwright Browser Binaries:**
    Run this command once to download necessary browser binaries for Playwright:
    ```bash
    uv run python -m playwright install
    ```
    (If `uv run` doesn't work before `uv sync` or outside an active `uv` managed venv, activate the venv first then run `python -m playwright install`)


### Frontend Setup

1.  **Navigate to the Frontend Directory:**
    ```bash
    cd frontend 
    ```
    (If you are in the `backend` directory, you'd do `cd ../frontend`)

2.  **Install Dependencies:**
    ```bash
    npm install
    ```

## Running the Application

You'll need to run both the backend and frontend servers.

### 1. Running the Backend

* Navigate to the `backend` directory.
* Ensure your virtual environment (if you created one with `uv venv`) is activated.
* Run the FastAPI server using Uvicorn:
    ```bash
    python -m uvicorn app.main:app --port 8000
    ```
    The backend server will typically start on `http://localhost:8000`.

    **Note for Windows Users with Playwright:** The command above runs Uvicorn without the `--reload` flag. The `--reload` flag was found to cause issues (`NotImplementedError`) with Playwright's subprocess management on Windows with certain Python 3.8+ versions due to asyncio event loop conflicts. The `main.py` includes a workaround for the asyncio event loop policy, and running without `--reload` provides the most stable experience for Playwright on Windows. If you need auto-reloading during development, you may need to stop and restart the server manually after changes.

### 2. Running the Frontend

* Navigate to the `frontend` directory.
* Start the Next.js development server:
    ```bash
    npm run dev
    ```
    The frontend will typically start on `http://localhost:3000`.

## How to Use

1.  Open your browser and go to the frontend URL (usually `http://localhost:3000`).
2.  Enter a full public website URL (e.g., `http://info.cern.ch/hypertext/WWW/TheProject.html` or other sites you wish to test) into the input field.
3.  Click the "Clone Website" button.
4.  The backend will scrape the website using Playwright, send its content to the Gemini LLM, and the LLM will generate an aesthetic HTML clone.
5.  A preview of the LLM-generated HTML will be displayed on the page.

## Important Considerations & Acknowledgements

* **Scraping Reliability & Approach:**
    * This project uses a **local Playwright instance** for website scraping. This allows the tool to process JavaScript-heavy websites and retrieve fully rendered HTML, which is crucial for providing accurate design context to the LLM.
    * **Acknowledgement regarding Production Environments:** The Orchids Challenge guidelines wisely caution that "Spinning up local browsers can be a slow and expensive process in production settings" and suggest considering cloud-hosted solutions. While local Playwright demonstrates the technical capability to handle complex sites for this challenge, for a production-grade system, a cloud-hosted browser solution (such as Browserbase or Hyperbrowser, as suggested in the challenge) would be implemented. This would enhance scalability, manage resources efficiently, and offer better resilience against IP blocks or firewalls.

* **LLM-Based Cloning:**
    * The goal is **aesthetic similarity**, not a pixel-perfect or fully functional replica.
    * The quality of the clone depends heavily on the LLM's interpretation and the **prompt engineering** used. Results can vary, and further refinement of the prompt can yield different and potentially improved outcomes. The current prompt focuses on replicating structure and the original color palette.

* **Windows Users & Asyncio (for Playwright):**
    * To enable Playwright to function correctly with `asyncio` on Windows (specifically to avoid a `NotImplementedError` related to subprocess creation with certain Python versions like 3.13), the `main.py` file in the backend includes a conditional check to set the `asyncio.WindowsProactorEventLoopPolicy()` at the beginning of the script. This ensures compatibility.

---