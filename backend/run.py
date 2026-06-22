"""
Run script for the Running Shoe Deal Finder API
Run this from the backend directory: python run.py
"""
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    
    print(f"""
    🏃‍♂️ Running Shoe Deal Finder API
    ================================
    Starting server at http://{host}:{port}
    API Documentation: http://localhost:{port}/docs
    Alternative Docs: http://localhost:{port}/redoc
    
    Press Ctrl+C to stop the server
    """)
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True  # Enable hot reload for development
    )
