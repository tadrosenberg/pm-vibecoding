import os
import json
import logging
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Excuse Email Draft Tool",
    description="Generate professional excuse emails using Databricks Model Serving",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment configuration
DATABRICKS_API_TOKEN = os.getenv("DATABRICKS_API_TOKEN")
DATABRICKS_ENDPOINT_URL = os.getenv(
    "DATABRICKS_ENDPOINT_URL", 
    "https://dbc-32cf6ae7-cf82.staging.cloud.databricks.com/serving-endpoints/databricks-gpt-oss-120b/invocations"
)
PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")

# Request/Response models
class ExcuseRequest(BaseModel):
    category: str = Field(..., description="Category of excuse")
    tone: str = Field(..., description="Tone of the email")
    seriousness: int = Field(..., ge=1, le=5, description="Seriousness level 1-5")
    recipient_name: str = Field(..., description="Name of the recipient")
    sender_name: str = Field(..., description="Name of the sender")
    eta_when: str = Field(..., description="ETA or when information")

class ExcuseResponse(BaseModel):
    subject: str
    body: str
    success: bool
    error: Optional[str] = None

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    logger.info(f"Headers: {dict(request.headers)}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response

# Health check endpoints
@app.get("/health")
@app.get("/healthz")
@app.get("/ready")
@app.get("/ping")
async def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy", "service": "excuse-email-draft-tool"}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return "# HELP excuse_tool_requests_total Total number of requests\n# TYPE excuse_tool_requests_total counter\nexcuse_tool_requests_total 0"

@app.get("/debug")
async def debug():
    """Debug endpoint to check environment configuration"""
    return {
        "databricks_token_configured": bool(DATABRICKS_API_TOKEN),
        "databricks_endpoint": DATABRICKS_ENDPOINT_URL,
        "port": PORT,
        "host": HOST,
        "environment": os.getenv("ENVIRONMENT", "development")
    }

async def call_databricks_llm(request_data: ExcuseRequest) -> Dict[str, Any]:
    """Call Databricks Model Serving endpoint"""
    if not DATABRICKS_API_TOKEN:
        raise HTTPException(
            status_code=500, 
            detail="Databricks API token not configured"
        )
    
    # Create the prompt for the LLM
    prompt = f"""
Generate a professional excuse email based on the following parameters:

Category: {request_data.category}
Tone: {request_data.tone}
Seriousness Level: {request_data.seriousness}/5
Recipient: {request_data.recipient_name}
Sender: {request_data.sender_name}
ETA/When: {request_data.eta_when}

Please generate a JSON response with the following format:
{{
    "subject": "Email subject line",
    "body": "Dear {request_data.recipient_name},\\n\\n[Email body content]\\n\\nBest regards,\\n{request_data.sender_name}"
}}

The email should:
- Match the specified tone ({request_data.tone})
- Be appropriate for the seriousness level ({request_data.seriousness}/5)
- Include a professional greeting and sign-off
- Be concise but complete
- Sound natural and believable

Respond with ONLY the JSON object, no additional text.
"""

    # Prepare the request payload
    payload = {
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 500,
        "temperature": 0.7
    }

    headers = {
        "Authorization": f"Bearer {DATABRICKS_API_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                DATABRICKS_ENDPOINT_URL,
                json=payload,
                headers=headers
            )
            
            logger.info(f"Databricks API response status: {response.status_code}")
            logger.info(f"Databricks API response: {response.text}")
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=500,
                    detail=f"Databricks API error: {response.status_code} - {response.text}"
                )
            
            result = response.json()
            
            # Parse the response - handle different response formats
            if "choices" in result and len(result["choices"]) > 0:
                message_content = result["choices"][0]["message"]["content"]
                
                # Handle different content formats
                if isinstance(message_content, list):
                    # Extract text content from list format
                    text_content = None
                    for item in message_content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            text_content = item.get("text", "")
                            break
                    content = text_content if text_content else str(message_content)
                else:
                    content = message_content
                    
            elif "predictions" in result and len(result["predictions"]) > 0:
                content = result["predictions"][0]
            else:
                content = str(result)
            
            # Try to parse as JSON first
            try:
                parsed_content = json.loads(content)
                return parsed_content
            except json.JSONDecodeError:
                # If not JSON, create a structured response from text
                lines = content.strip().split('\n')
                subject = lines[0] if lines else f"Re: {request_data.category}"
                body = '\n'.join(lines[1:]) if len(lines) > 1 else content
                
                return {
                    "subject": subject,
                    "body": f"Dear {request_data.recipient_name},\n\n{body}\n\nBest regards,\n{request_data.sender_name}"
                }
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Request timeout to Databricks API")
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error calling Databricks API: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.post("/api/generate-excuse", response_model=ExcuseResponse)
async def generate_excuse(request: ExcuseRequest):
    """Generate an excuse email using Databricks Model Serving"""
    try:
        logger.info(f"Generating excuse for: {request.category} - {request.tone}")
        
        # Call the Databricks LLM
        result = await call_databricks_llm(request)
        
        return ExcuseResponse(
            subject=result.get("subject", f"Re: {request.category}"),
            body=result.get("body", "Email content could not be generated."),
            success=True,
            error=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating excuse: {str(e)}")
        return ExcuseResponse(
            subject="Error",
            body="Sorry, there was an error generating your email. Please try again.",
            success=False,
            error=str(e)
        )

# Static file serving for React app
def get_public_path():
    """Get the path to the public directory, handling different environments"""
    possible_paths = [
        Path(__file__).parent.parent / "public",
        Path("public"),
        Path("/app/public"),
        Path("/workspace/public")
    ]
    
    for path in possible_paths:
        if path.exists():
            logger.info(f"Found public directory at: {path}")
            return path
    
    logger.warning("Public directory not found, using current directory")
    return Path(__file__).parent.parent

@app.get("/", response_class=HTMLResponse)
async def serve_react_app():
    """Serve the React application"""
    public_path = get_public_path()
    index_file = public_path / "index.html"
    
    if index_file.exists():
        logger.info(f"Serving React app from: {index_file}")
        return FileResponse(index_file)
    else:
        logger.error(f"index.html not found at: {index_file}")
        return HTMLResponse("""
        <html>
            <head><title>Excuse Email Draft Tool</title></head>
            <body>
                <h1>Excuse Email Draft Tool</h1>
                <p>Frontend not found. Please ensure index.html exists in the public directory.</p>
                <p>API is available at <a href="/docs">/docs</a></p>
            </body>
        </html>
        """)

# Serve static files
public_path = get_public_path()
if public_path.exists():
    app.mount("/static", StaticFiles(directory=public_path), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
