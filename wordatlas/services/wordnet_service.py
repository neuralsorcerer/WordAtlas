from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

import nltk
from nltk import data as nltk_data
from nltk.corpus import wordnet as wn

log = logging.getLogger(__name__)

_CORPORA = ["wordnet", "omw-1.4"]


def _ensure_corpora() -> None:
    missing: list[str] = []
    for c in _CORPORA:
        try:
            nltk_data.find(f"corpora/{c}")
        except LookupError:
            missing.append(c)
    for c in missing:
        log.info("Downloading NLTK corpus: %s", c)
        nltk.download(c, quiet=True)


@lru_cache(maxsize=4096)
def synsets_for(word: str) -> list[Any]:
    _ensure_corpora()
    return list(wn.synsets(word))


def cache_info() -> dict[str, Any]:
    """Return cache size/load metrics for introspection."""
    info = synsets_for.cache_info()
    return {
        "synsets_for": {
            "hits": info.hits,
            "misses": info.misses,
            "maxsize": info.maxsize,
            "currsize": info.currsize,
        }
    }


def clear_caches() -> None:
    """Clear LRU caches to release memory."""
    try:
        synsets_for.cache_clear()
    except Exception:
        pass


def lemma_key(lemma: Any) -> str:
    # Normalize a lemma name to a node id
    name = getattr(lemma, "name", lambda: "")()
    return str(name).replace("_", " ")


def expand_word(word: str) -> tuple[set[tuple[str, str]], set[tuple[str, str, str]]]:
    """
    Returns (nodes, edges) for immediate neighborhood of `word` based on WordNet.
    - nodes: set of (id, pos)
    - edges: set of (src, dst, relation)
    """
    nodes: set[tuple[str, str]] = set()
    edges: set[tuple[str, str, str]] = set()

    syns = synsets_for(word)

    # Infer a reasonable POS for the center word (most frequent POS across synsets)
    pos_infer = ""
    if syns:
        counts: dict[str, int] = {}
        for s in syns:
            p = str(getattr(s, "pos", lambda: "")())
            if p:
                counts[p] = (counts.get(p) or 0) + 1
        if counts:
            pos_infer = max(counts.items(), key=lambda kv: kv[1])[0]

    for s in syns:
        pos = str(getattr(s, "pos", lambda: "")())
        # synonyms (lemmas in the same synset)
        for lemma in list(getattr(s, "lemmas", lambda: [])() or []):
            target = lemma_key(lemma)
            nodes.add((target, pos))
            if target != word:
                edges.add((word, target, "synonym"))
            # antonyms via lemma
            for ant in list(getattr(lemma, "antonyms", lambda: [])() or []):
                ant_name = lemma_key(ant)
                syn = getattr(ant, "synset", lambda: lambda: None)()
                ant_pos = str(getattr(syn, "pos", lambda: "")())
                nodes.add((ant_name, ant_pos))
                if ant_name != word:
                    edges.add((word, ant_name, "antonym"))

        # hypernyms
        for h in list(getattr(s, "hypernyms", lambda: [])() or []):
            for lemma in list(getattr(h, "lemmas", lambda: [])() or []):
                target = lemma_key(lemma)
                nodes.add((target, str(getattr(h, "pos", lambda: "")())))
                if target != word:
                    edges.add((word, target, "hypernym"))

        # hyponyms
        for h in list(getattr(s, "hyponyms", lambda: [])() or []):
            for lemma in list(getattr(h, "lemmas", lambda: [])() or []):
                target = lemma_key(lemma)
                nodes.add((target, str(getattr(h, "pos", lambda: "")())))
                if target != word:
                    edges.add((word, target, "hyponym"))

        # similar_tos (adjectives)
        for sim in list(getattr(s, "similar_tos", lambda: [])() or []):
            for lemma in list(getattr(sim, "lemmas", lambda: [])() or []):
                target = lemma_key(lemma)
                nodes.add((target, str(getattr(sim, "pos", lambda: "")())))
                if target != word:
                    edges.add((word, target, "similar_to"))

    nodes.add((word, pos_infer))
    return nodes, edges
