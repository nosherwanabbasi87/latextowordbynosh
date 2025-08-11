
# LaTeX → Word (.docx) with Vertopal API (Beginner Friendly)

This version uses **Vertopal's File Conversion API** — no Pandoc or heavy server needed.

## What you need
1) A free **Vertopal** account.  
2) Create an **APP** in Vertopal to get:
   - **APP_ID**
   - **APP_TOKEN** (access token)

Where to find the docs: Vertopal API Quick Start and endpoints (Upload → Convert → Download).

- Quick Start: /en/developer/api/quick-start
- Upload: /en/developer/api/upload/file
- Convert File: /en/developer/api/convert/file
- Monitor Response of Task: /en/developer/api/task/response
- Generate Download URL: /en/developer/api/download/url
- Get File from Download URL: /en/developer/api/download/url/get

## Configure the app
Set two environment variables before running:

- `VERTOPAL_APP_ID` — your app id
- `VERTOPAL_APP_TOKEN` — your app token

On Windows PowerShell:
```
setx VERTOPAL_APP_ID "your-app-id"
setx VERTOPAL_APP_TOKEN "your-app-token"
```
On macOS/Linux (temporary for the current terminal):
```
export VERTOPAL_APP_ID="your-app-id"
export VERTOPAL_APP_TOKEN="your-app-token"
```

## Run locally (optional)
```
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```
Open http://localhost:8080

## Deploy (Render.com example)
- Push this folder to a GitHub repo.
- Create a new Web Service on Render → use **Docker** (it sees the Dockerfile).
- Add two **Environment Variables** in Render settings:
  - `VERTOPAL_APP_ID`
  - `VERTOPAL_APP_TOKEN`
- Start command: `python app.py` (Dockerfile already sets Python up).
- Port: 8080

## How to use
- Upload a single `.tex` (or `.latex`) file.  
  *Note:* Vertopal API is optimized for single-file conversions. If your project depends on many external images/packages, consider converting a simplified version or using our Pandoc self-hosted starter instead.
- Choose output **docx** (preselected).
- Click Convert → your browser downloads the `.docx`.

## Notes
- This app waits for the async conversion by **polling** the Vertopal `task/response` endpoint (simple and reliable).
- For production sites, add a privacy notice and rate-limiting.
