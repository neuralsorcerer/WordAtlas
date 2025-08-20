from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

Relation = Literal["synonym", "hypernym", "hyponym", "antonym", "similar_to"]


class Node(BaseModel):
    id: str
    label: str
    pos: str | None = None  # n, v, a, r


class Edge(BaseModel):
    source: str
    target: str
    relation: Relation


class Graph(BaseModel):
    center: str
    nodes: list[Node]
    edges: list[Edge]
