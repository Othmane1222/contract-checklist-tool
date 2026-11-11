from fastapi.testclient import TestClient
from starlette.formparsers import MultiPartParser

import main


def test_uploads_stay_in_memory_up_to_the_size_limit():
    assert MultiPartParser.spool_max_size >= main.MAX_FILE_SIZE


def test_upload_without_declared_size_is_rejected():
    client = TestClient(main.app)
    response = client.post("/api/check", content=iter([b"x"]))
    assert response.status_code == 411
    assert response.json()["code"] == "length_required"