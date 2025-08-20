from __future__ import annotations

from graphviz import Digraph

from wordatlas.models import Graph

POS_COLOR = {
    "n": "lightblue",
    "v": "palegreen",
    "a": "khaki",
    "s": "khaki",
    "r": "plum",
}

REL_STYLE = {
    "synonym": ("gray40", "solid"),
    "hypernym": ("black", "solid"),
    "hyponym": ("black", "dashed"),
    "antonym": ("red", "bold"),
    "similar_to": ("blue", "dotted"),
}


def to_graphviz(g: Graph, *, allowed_relations: set[str] | None = None) -> Digraph:
    dot = Digraph(comment=f"WordAtlas: {g.center}")
    dot.attr(rankdir="LR", concentrate="true", splines="spline")

    for n in g.nodes:
        color = POS_COLOR.get(n.pos or "", "white")
        penwidth = "2" if n.id == g.center else "1"
        dot.node(n.id, label=n.label, style="filled", fillcolor=color, penwidth=penwidth)

    for e in g.edges:
        if allowed_relations is not None and e.relation not in allowed_relations:
            continue
        color, style = REL_STYLE.get(e.relation, ("black", "solid"))
        dot.edge(e.source, e.target, color=color, style=style)

    return dot
