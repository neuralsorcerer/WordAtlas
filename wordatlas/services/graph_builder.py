from __future__ import annotations

import logging
from collections import deque
from typing import cast

from wordatlas.config import settings
from wordatlas.models import Edge, Graph, Node
from wordatlas.models import Relation as RelationType
from wordatlas.services.wordnet_service import expand_word

log = logging.getLogger(__name__)


POS = str


def build_graph(
    center: str,
    depth: int | None = None,
    max_nodes: int | None = None,
    *,
    rel_depths: dict[RelationType, int] | None = None,
    pos_caps: dict[POS, int] | None = None,
    exclude: set[str] | None = None,
) -> Graph:
    """BFS expansion over WordNet relations.

    Parameters
    - depth: overall hop depth cap.
    - rel_depths: optional per-relation hop caps; each time an edge of that
      relation is traversed, its remaining budget is decremented along that path.
      Relations not listed are unconstrained (subject only to overall depth).
    - pos_caps: optional per-POS cap for how many nodes of that POS may be
      included (keys like 'n','v','a','s','r').
    - exclude: optional set of node ids (words) to exclude; the center is always
      included.
    """
    center = center.strip().lower()
    if not center:
        raise ValueError("center word must be non-empty")

    depth = settings.default_depth if depth is None else max(0, int(depth))
    max_nodes = settings.max_nodes if max_nodes is None else int(max_nodes)

    seen_nodes: dict[str, str] = {}
    expanded: set[str] = set()
    edges: set[tuple[str, str, RelationType]] = set()

    # pos caps tracking
    pos_counts: dict[POS, int] = {"n": 0, "v": 0, "a": 0, "s": 0, "r": 0}
    caps = pos_caps or {}

    # normalize exclude set
    excluded: set[str] = set(x.strip().lower() for x in (exclude or set()))

    # BFS queue carries remaining per-relation budgets
    # NOTE: Only relations explicitly present are constrained; others are unconstrained
    initial_budget: dict[RelationType, int] | None = None
    if rel_depths is not None:
        initial_budget = {k: max(0, int(v)) for k, v in rel_depths.items()}

    q: deque[tuple[str, int, dict[RelationType, int] | None]] = deque([(center, 0, initial_budget)])

    while q and len(seen_nodes) < max_nodes:
        word, d, budget = q.popleft()
        if word in expanded:
            continue
        expanded.add(word)

        nodes, new_edges_raw = expand_word(word)
        # map id->pos for this expansion
        pos_map: dict[str, str] = {nid: p for nid, p in nodes}

        # Always add the center first to ensure POS caps include it and avoid set-order issues
        if center not in seen_nodes:
            p_center = pos_map.get(center)
            if p_center is not None:
                seen_nodes[center] = p_center
                if p_center in pos_counts:
                    pos_counts[p_center] = pos_counts.get(p_center, 0) + 1

        # include nodes subject to pos caps, exclude set, and max_nodes
        for nid, p in nodes:
            if nid == center:
                continue
            if len(seen_nodes) >= max_nodes:
                break
            # exclusion
            if nid in excluded:
                continue
            # pos caps
            if pos_caps:
                cap_for = caps.get(p) if p is not None else None
                if cap_for is not None and pos_counts.get(p, 0) >= cap_for:
                    continue
            if nid not in seen_nodes:
                seen_nodes[nid] = p
                if p in pos_counts:
                    pos_counts[p] = pos_counts.get(p, 0) + 1

        # normalize and merge edges (we will filter by seen at the end)
        for s, t, r in new_edges_raw:
            if r in {"synonym", "hypernym", "hyponym", "antonym", "similar_to"}:
                edges.add((s, t, cast(RelationType, r)))

        # enqueue neighbors considering relation budgets, depth and exclusions
        if d >= depth:
            continue

        # gather outgoing edges from current word
        for src, tgt, rel in list(new_edges_raw):
            if src != word:
                continue
            # exclusions and caps prevented adding, skip traversal
            if tgt != center and tgt in excluded:
                continue
            tpos = pos_map.get(tgt)
            if pos_caps and tpos is not None:
                cap_for = caps.get(tpos)
                if cap_for is not None and pos_counts.get(tpos, 0) >= cap_for:
                    continue
            # relation budget check — only constrain relations present in the budget map
            next_budget: dict[RelationType, int] | None
            if budget is not None and cast(RelationType, rel) in budget:
                remaining = budget.get(cast(RelationType, rel), 0)
                if remaining <= 0:
                    continue
                next_budget = dict(budget)
                next_budget[cast(RelationType, rel)] = remaining - 1
            else:
                next_budget = budget  # propagate unchanged budget
            q.append((tgt, d + 1, next_budget))

    node_models = [Node(id=k, label=k, pos=v) for k, v in seen_nodes.items()]
    edge_models = [
        Edge(source=s, target=t, relation=r)
        for (s, t, r) in edges
        if s in seen_nodes and t in seen_nodes
    ]

    return Graph(center=center, nodes=node_models, edges=edge_models)
