import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def gql_client():
    os.environ.setdefault("API_TOKEN", "testtoken")
    from vpn_merger.web.graphql.app import create_graphql_app

    app = create_graphql_app()
    client = TestClient(app)
    yield client


def _auth_headers():
    return {"X-API-Token": "testtoken"}


def test_health_query(gql_client):
    query = """
    query { health }
    """
    r = gql_client.post("/graphql", json={"query": query}, headers=_auth_headers())
    assert r.status_code == 200
    data = r.json()
    assert data["data"]["health"] == "ok"


def test_configs_page_and_connection(gql_client):
    query = """
    query($limit:Int,$offset:Int){ configsPage(limit:$limit,offset:$offset){ page_info{ total has_more has_next_page end_cursor } items { id protocol } } }
    """
    r = gql_client.post(
        "/graphql",
        json={"query": query, "variables": {"limit": 5, "offset": 0}},
        headers=_auth_headers(),
    )
    assert r.status_code == 200
    data = r.json()["data"]["configsPage"]
    assert "page_info" in data and "items" in data

    conn = """
    query($first:Int){ configsConnection(first:$first){ page_info{ has_more end_cursor } edges { cursor node { id } } } }
    """
    r2 = gql_client.post(
        "/graphql", json={"query": conn, "variables": {"first": 3}}, headers=_auth_headers()
    )
    assert r2.status_code == 200
    d2 = r2.json()["data"]["configsConnection"]
    assert "edges" in d2
