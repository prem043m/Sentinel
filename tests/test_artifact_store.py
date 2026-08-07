"""Tests for the ArtifactStore module."""

from __future__ import annotations

import pytest
from app.artifacts.models import Artifact, ExecutionArtifactType
from app.artifacts.store import ArtifactStore


def test_artifact_store_save_and_retrieve():
    store = ArtifactStore()
    artifact = Artifact(
        id="ART-001",
        request_id="REQ-1",
        type=ExecutionArtifactType.TEXT,
        name="test_doc.txt",
        content="Hello world",
        metadata={"key": "val"},
    )

    store.save(artifact)

    retrieved = store.get("ART-001")
    assert retrieved is not None
    assert retrieved.id == "ART-001"
    assert retrieved.content == "Hello world"
    assert retrieved.metadata == {"key": "val"}


def test_artifact_store_list_all():
    store = ArtifactStore()
    a1 = Artifact(
        id="ART-001",
        request_id="REQ-1",
        type=ExecutionArtifactType.TEXT,
        name="test1",
        content="Content 1",
    )
    a2 = Artifact(
        id="ART-002",
        request_id="REQ-1",
        type=ExecutionArtifactType.JSON,
        name="test2",
        content="{}",
    )

    store.save(a1)
    store.save(a2)

    all_artifacts = store.list_all()
    assert len(all_artifacts) == 2
    assert all_artifacts[0].id == "ART-001"
    assert all_artifacts[1].id == "ART-002"


def test_artifact_store_find_by_type():
    store = ArtifactStore()
    a1 = Artifact(
        id="ART-001",
        request_id="REQ-1",
        type=ExecutionArtifactType.TEXT,
        name="test1",
        content="Content 1",
    )
    a2 = Artifact(
        id="ART-002",
        request_id="REQ-1",
        type=ExecutionArtifactType.JSON,
        name="test2",
        content="{}",
    )

    store.save(a1)
    store.save(a2)

    json_artifacts = store.find_by_type(ExecutionArtifactType.JSON)
    assert len(json_artifacts) == 1
    assert json_artifacts[0].id == "ART-002"


def test_artifact_store_find_by_request_id():
    store = ArtifactStore()
    a1 = Artifact(
        id="ART-001",
        request_id="REQ-A",
        type=ExecutionArtifactType.TEXT,
        name="test1",
        content="Content 1",
    )
    a2 = Artifact(
        id="ART-002",
        request_id="REQ-B",
        type=ExecutionArtifactType.JSON,
        name="test2",
        content="{}",
    )

    store.save(a1)
    store.save(a2)

    req_a_artifacts = store.find_by_request_id("REQ-A")
    assert len(req_a_artifacts) == 1
    assert req_a_artifacts[0].id == "ART-001"


def test_artifact_store_clear():
    store = ArtifactStore()
    artifact = Artifact(
        id="ART-001",
        request_id="REQ-1",
        type=ExecutionArtifactType.TEXT,
        name="test1",
        content="Content 1",
    )

    store.save(artifact)
    assert len(store.list_all()) == 1

    store.clear()
    assert len(store.list_all()) == 0
