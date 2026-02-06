"""
Vercel Serverless Function Entry Point
Routes all requests to FastAPI backend
"""
from backend.main import app
from mangum import Mangum

# Mangum adapter converts FastAPI to ASGI for Vercel
handler = Mangum(app, lifespan="off")
