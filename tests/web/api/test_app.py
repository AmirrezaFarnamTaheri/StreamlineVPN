"""
A simple FastAPI app for testing middleware.
"""

from fastapi import FastAPI, Request
from streamline_vpn.web.api.middleware import setup_middleware, setup_exception_handlers

def create_app():
    app = FastAPI()

    @app.get("/")
    async def read_root():
        return {"Hello": "World"}

    @app.get("/error/value")
    async def raise_value_error():
        raise ValueError("Test value error")

    @app.get("/error/filenotfound")
    async def raise_file_not_found_error():
        raise FileNotFoundError("Test file not found")

    @app.get("/error/generic")
    async def raise_generic_error():
        raise Exception("Test generic error")

    setup_middleware(app)
    setup_exception_handlers(app)
    return app

app = create_app()
