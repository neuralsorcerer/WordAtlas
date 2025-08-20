from wordatlas.services.graph_builder import build_graph


def test_build_graph_basic():
    g = build_graph("happiness", depth=1, max_nodes=150)
    assert g.center == "happiness"
    assert len(g.nodes) >= 1
    assert len(g.edges) >= 1


def test_per_relation_depth_and_pos_caps():
    g = build_graph("happy", depth=2, max_nodes=200, rel_depths={"synonym": 0, "hypernym": 1})
    assert g.nodes and g.edges

    g2 = build_graph("bright", depth=2, max_nodes=200, pos_caps={"a": 5, "n": 50})
    a_count = sum(1 for n in g2.nodes if n.pos == "a")
    assert a_count <= 5


def test_exclude_words():
    g = build_graph("run", depth=1, max_nodes=150, exclude={"sprint", "jog"})
    ex = {"sprint", "jog"}
    assert all(n.id not in ex for n in g.nodes)
