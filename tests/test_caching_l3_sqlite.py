import asyncio
import json
import time
import pytest

from streamline_vpn.core.caching.l3_sqlite import L3DatabaseCache


@pytest.mark.asyncio
async def test_l3_sqlite_set_get_delete_and_ttl(tmp_path):
    db = tmp_path / "l3.db"
    l3 = L3DatabaseCache(str(db))
    # set and get
    assert await l3.set("a", json.dumps({"n": 1}), ttl=1)
    assert await l3.get("a") == json.dumps({"n": 1})
    # ttl expiry
    time.sleep(1.1)
    assert await l3.get("a") is None
    # delete non-existent ok
    assert await l3.delete("a") is False
    # clear no error
    await l3.clear()

