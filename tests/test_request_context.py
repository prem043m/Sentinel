"""Tests for request context tracking and ID generation."""

from __future__ import annotations

import re
from app.core.request_context import generate_request_id, get_request_id, request_id_scope


def test_generate_request_id_format():
    req_id = generate_request_id()
    # Format: REQ-YYYYMMDD-NNNNN
    assert re.match(r"^REQ-\d{8}-\d{5}$", req_id)


def test_request_id_scope():
    assert get_request_id() == "REQ-system-default"

    with request_id_scope("REQ-20260807-12345") as scoped_id:
        assert scoped_id == "REQ-20260807-12345"
        assert get_request_id() == "REQ-20260807-12345"

    assert get_request_id() == "REQ-system-default"
