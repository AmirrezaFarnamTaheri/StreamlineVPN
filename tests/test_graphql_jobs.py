import asyncio
import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def gql_client():
    os.environ.setdefault("API_TOKEN", "testtoken")
    from vpn_merger.web.graphql.app import create_graphql_app

    app = create_graphql_app()
    client = TestClient(app)
    return client


def _auth_headers():
    return {"X-API-Token": "testtoken"}


@pytest.mark.asyncio
async def test_job_mutations_and_polling(gql_client):
    # start merge
    start_mut = """
    mutation($sources:[String!]){ startMerge(sources:$sources){ id } }
    """
    r = gql_client.post(
        "/graphql",
        json={"query": start_mut, "variables": {"sources": ["http://example.local/a.txt"]}},
        headers=_auth_headers(),
    )
    assert r.status_code == 200
    job_id = r.json()["data"]["startMerge"]["id"]
    assert job_id

    # poll job status
    job_q = """
    query($id:String!){ job(id:$id){ id status progress total_configs valid_configs } }
    """
    # wait a bit for runner
    await asyncio.sleep(0.2)
    r2 = gql_client.post(
        "/graphql", json={"query": job_q, "variables": {"id": job_id}}, headers=_auth_headers()
    )
    assert r2.status_code == 200
    d = r2.json()["data"]["job"]
    assert d["id"] == job_id
    assert d["status"] in ("running", "completed", "cancelled")

    # cleanup jobs manually (no assertion on count)
    cleanup = "mutation{ cleanupJobs }"
    gql_client.post("/graphql", json={"query": cleanup}, headers=_auth_headers())
