"""
GraphQL Application
===================

GraphQL FastAPI application for StreamlineVPN.
"""

import os
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from .schema import schema

def create_graphql_app() -> FastAPI:
    """Create GraphQL FastAPI application."""
    app = FastAPI(title="StreamlineVPN GraphQL API")
    
    # Create GraphQL router
    graphql_app = GraphQLRouter(schema)
    
    # Add GraphQL endpoint
    app.include_router(graphql_app, prefix="/graphql")
    
    return app
