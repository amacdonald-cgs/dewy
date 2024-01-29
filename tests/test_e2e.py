import random
import string
import time
from typing import List

from pydantic import TypeAdapter

from dewy.chunks.models import Chunk, RetrieveRequest, RetrieveResponse
from dewy.documents.models import AddDocumentRequest

SKELETON_OF_THOUGHT_PDF = "https://arxiv.org/pdf/2307.15337.pdf"


async def create_collection(client, text_embedding_model: str) -> int:
    name = "".join(random.choices(string.ascii_lowercase, k=5))
    create_response = await client.put("/api/collections/", json={"name": name})
    assert create_response.status_code == 200

    return create_response.json()["id"]


async def ingest(client, collection: int, url: str) -> int:
    add_request = AddDocumentRequest(collection_id=collection, url=url)
    add_response = await client.put(
        "/api/documents/", data=add_request.model_dump_json()
    )
    assert add_response.status_code == 200

    document_id = add_response.json()["id"]

    # TODO(https://github.com/DewyKB/dewy/issues/34): Move waiting to the server
    # and eliminate need to poll.
    status = await client.get(f"/api/documents/{document_id}")
    while status.json()["ingest_state"] != "ingested":
        time.sleep(1)
        status = await client.get(f"/api/documents/{document_id}")

    return document_id

async def list_chunks(client, collection: int, document: int):
    response = await client.get("/api/chunks/", params = {
        'collection_id': collection,
        'document_id': document
    })
    assert response.status_code == 200
    ta = TypeAdapter(List[Chunk])
    return ta.validate_json(response.content)

async def retrieve(client, collection: int, query: str) -> RetrieveResponse:
    request = RetrieveRequest(
        collection_id=collection, query=query, include_image_chunks=False
    )

    response = await client.post("/api/chunks/retrieve", data=request.model_dump_json())
    assert response.status_code == 200
    return RetrieveResponse.model_validate_json(response.content)


async def test_e2e_openai_ada002(client):
    collection = await create_collection(client, "openai:text-embedding-ada-002")
    document = await ingest(client, collection, SKELETON_OF_THOUGHT_PDF)
    chunks = await list_chunks(client, collection, document)
    assert len(chunks) > 0
    assert chunks[0].document_id == document

    results = await retrieve(
        client, collection, "outline the steps to using skeleton-of-thought prompting"
    )
    assert len(results.text_results) > 0
    print(results.text_results)

    assert results.text_results[0].document_id == document
    assert "skeleton" in results.text_results[0].text.lower()


async def test_e2e_hf_bge_small(client):
    collection = await create_collection(client, "hf:BAAI/bge-small-en")
    document = await ingest(client, collection, SKELETON_OF_THOUGHT_PDF)
    chunks = await list_chunks(client, collection, document)
    assert len(chunks) > 0
    assert chunks[0].document_id == document

    results = await retrieve(
        client, collection, "outline the steps to using skeleton-of-thought prompting"
    )
    assert len(results.text_results) > 0
    print(results.text_results)

    assert results.text_results[0].document_id == document
    assert "skeleton" in results.text_results[0].text.lower()