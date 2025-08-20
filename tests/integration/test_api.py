from fastapi.testclient import TestClient

from wordatlas.api.app import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_graph_endpoint_basic():
    r = client.get("/api/graph", params={"word": "happiness", "depth": 1})
    assert r.status_code == 200
    data = r.json()
    assert data["center"] == "happiness"
    assert len(data["nodes"]) >= 1
    assert len(data["edges"]) >= 1


def test_graph_endpoint_depth_and_nodes():
    r = client.get("/api/graph", params={"word": "run", "depth": 2, "max_nodes": 120})
    assert r.status_code == 200
    data = r.json()
    assert data["center"] == "run"
    assert len(data["nodes"]) >= 1


def test_graph_endpoint_relation_filter_only_synonym():
    r = client.get(
        "/api/graph",
        params={
            "word": "happiness",
            "depth": 1,
            "relation": ["synonym"],
        },
    )
    assert r.status_code == 200
    data = r.json()
    rels = {e["relation"] for e in data.get("edges", [])}
    assert rels.issubset({"synonym"})


def test_graph_endpoint_multiple_relation_filters():
    r = client.get(
        "/api/graph",
        params={
            "word": "happiness",
            "depth": 1,
            "relation": ["synonym", "hypernym"],
        },
    )
    assert r.status_code == 200
    data = r.json()
    rels = {e["relation"] for e in data.get("edges", [])}
    assert rels.issubset({"synonym", "hypernym"})


def test_cache_clear_endpoint():
    r = client.post("/api/cache/clear")
    assert r.status_code == 200
    assert r.json().get("ok") is True


def test_graph_validation_empty_word():
    r = client.get("/api/graph", params={"word": "", "depth": 1})
    assert r.status_code == 422


def test_graph_validation_depth_upper_bound():
    # depth has le=5 in the API signature
    r = client.get("/api/graph", params={"word": "run", "depth": 6})
    assert r.status_code == 422


def test_static_root_served():
    r = client.get("/")
    assert r.status_code == 200
    assert "WordAtlas" in r.text
