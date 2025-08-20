from __future__ import annotations

import logging
import time
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Annotated, Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from fastapi.staticfiles import StaticFiles
from nltk import data as nltk_data

from wordatlas.config import settings
from wordatlas.logging_config import configure_logging
from wordatlas.models import Graph
from wordatlas.services.graph_builder import build_graph
from wordatlas.services.wordnet_service import cache_info, clear_caches

configure_logging(settings.log_level)
log = logging.getLogger("wordatlas.api")

app = FastAPI(title="WordAtlas", default_response_class=ORJSONResponse)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


STARTED_AT = time.time()


@app.get("/api/health")
def health() -> dict[str, Any]:
    try:
        ver = version("wordatlas")
    except PackageNotFoundError:
        ver = "unknown"

    # dependency checks (non-blocking, no downloads)
    def has_corpus(name: str) -> bool:
        try:
            nltk_data.find(f"corpora/{name}")
            return True
        except LookupError:
            return False
        except Exception:
            return False

    corpora = {c: has_corpus(c) for c in ("wordnet", "omw-1.4")}

    # static UI check
    static_ok = Path(__file__).with_name("static").exists()

    return {
        "ok": True,  # keep compatibility with tests
        "status": "ok",
        "version": ver,
        "uptime_sec": int(time.time() - STARTED_AT),
        "checks": {
            "nltk": corpora,
            "static": static_ok,
            "cache": cache_info(),
        },
    }


@app.get("/api/graph", response_model=Graph)
def api_graph(
    word: Annotated[str, Query(min_length=1)],
    depth: Annotated[int | None, Query(ge=0, le=5)] = None,
    max_nodes: Annotated[int | None, Query(ge=10, le=2000)] = None,
    relation: Annotated[list[str] | None, Query()] = None,
) -> Graph:
    try:
        # fall back to settings when not supplied
        d = settings.default_depth if depth is None else depth
        m = settings.max_nodes if max_nodes is None else max_nodes
        g = build_graph(word, depth=d, max_nodes=m)
        if relation:
            allowed = {r for r in relation}
            g.edges = [e for e in g.edges if e.relation in allowed]
        return g
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:  # pragma: no cover
        log.exception("graph-build-failed: %s", e)
        raise HTTPException(status_code=500, detail="internal error") from e


@app.post("/api/cache/clear")
def api_cache_clear() -> dict[str, bool]:
    try:
        clear_caches()
        return {"ok": True}
    except Exception as e:  # pragma: no cover
        log.exception("cache-clear-failed: %s", e)
        raise HTTPException(status_code=500, detail="internal error") from e


_static_dir = Path(__file__).with_name("static")
app.mount("/", StaticFiles(directory=str(_static_dir), html=True), name="static")
