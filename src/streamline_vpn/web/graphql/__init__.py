"""
GraphQL Components
==================

GraphQL API for StreamlineVPN.
"""

from .app import create_graphql_app
from .schema import schema, Query, Mutation

__all__ = ["create_graphql_app", "schema", "Query", "Mutation"]
