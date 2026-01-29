#!/usr/bin/env python
"""Run the UserBot Hub server"""
import os
import sys
import asyncio

# Change to backend directory
backend_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(backend_dir)
sys.path.insert(0, backend_dir)

from hypercorn.config import Config
from hypercorn.asyncio import serve

if __name__ == "__main__":
    print(f"Starting server from: {os.getcwd()}")
    
    # Import app after setting up paths
    from app.main import app
    
    config = Config()
    config.bind = ["127.0.0.1:8001"]
    config.loglevel = "info"
    
    asyncio.run(serve(app, config))
