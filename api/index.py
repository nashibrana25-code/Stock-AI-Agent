"""
Vercel serverless function handler for FastAPI
"""
from services.api_gateway.main import app

# Vercel expects a handler function
handler = app
