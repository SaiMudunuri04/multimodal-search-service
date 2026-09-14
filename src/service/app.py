"""CLIP image catalog search API."""

import os
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .multimodal import CLIPEncoder, build_index, load_catalog, search
from .observability import RequestLoggingMiddleware

app = FastAPI(title="Multimodal search", version="0.1.0")
app.add_middleware(RequestLoggingMiddleware)


class Query(BaseModel):
    text: str = Field(min_length=2, max_length=500)
    limit: int = Field(default=5, ge=1, le=20)


@lru_cache(maxsize=1)
def bundle():
    catalog = Path(os.getenv("CATALOG_PATH", "/data/catalog.jsonl"))
    root = Path(os.getenv("IMAGE_ROOT", "/data/images"))
    if not catalog.is_file() or not root.is_dir():
        raise FileNotFoundError("Catalog or image root unavailable")
    encoder = CLIPEncoder(os.getenv("CLIP_MODEL", "openai/clip-vit-base-patch32"))
    return encoder, build_index(load_catalog(catalog, root), encoder)


@app.get("/health/live")
def live():
    return {"status": "alive"}


@app.get("/health/ready")
def ready():
    try:
        bundle()
    except (FileNotFoundError, ValueError, OSError):
        raise HTTPException(503, "Search index unavailable")
    return {"status": "ready"}


@app.post("/search")
def query(request: Query):
    try:
        encoder, indexed = bundle()
    except (FileNotFoundError, ValueError, OSError):
        raise HTTPException(503, "Search index unavailable")
    return {"results": search(request.text, indexed, encoder, request.limit)}
