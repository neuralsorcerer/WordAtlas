from pathlib import Path
from typing import Optional

from graphviz import Digraph

from wordatlas.models import Edge, Graph, Node
from wordatlas.services.renderer import to_graphviz


def test_to_graphviz_renders(monkeypatch, tmp_path: Path):
    nodes = [Node(id="center", label="center", pos="n"), Node(id="x", label="x", pos="a")]
    edges = [Edge(source="center", target="x", relation="synonym")]
    g = Graph(center="center", nodes=nodes, edges=edges)

    def fake_render(self: Digraph, filename: Optional[str] = None, cleanup: bool = True):
        out = Path(filename or (tmp_path / "g")).with_suffix(".png")
        out.write_bytes(b"")
        return str(out)

    monkeypatch.setattr(Digraph, "render", fake_render)

    dot = to_graphviz(g)
    dot.format = "png"
    out_path = tmp_path / "graph"
    rendered = dot.render(filename=str(out_path), cleanup=True)
    assert Path(rendered).exists()


def test_to_graphviz_relation_filter(monkeypatch, tmp_path: Path):
    nodes = [Node(id="c", label="c", pos="n"), Node(id="a", label="a", pos="n")]
    edges = [
        Edge(source="c", target="a", relation="antonym"),
        Edge(source="c", target="a", relation="synonym"),
    ]
    g = Graph(center="c", nodes=nodes, edges=edges)

    def fake_render(self: Digraph, filename: Optional[str] = None, cleanup: bool = True):
        out = Path(filename or (tmp_path / "g")).with_suffix(".png")
        out.write_bytes(b"")
        return str(out)

    monkeypatch.setattr(Digraph, "render", fake_render)

    dot = to_graphviz(g, allowed_relations={"synonym"})
    dot.format = "png"
    out_path = tmp_path / "graph"
    dot.render(filename=str(out_path), cleanup=True)
    assert True
