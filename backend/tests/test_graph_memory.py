import tempfile
import pytest
from graph_memory import GraphMemory


@pytest.fixture
def gm():
    with tempfile.TemporaryDirectory() as tmp:
        yield GraphMemory(graph_dir=tmp)


def test_create_and_load_graph(gm):
    g = gm.create_graph("chat-1")
    assert g.number_of_nodes() == 0
    loaded = gm.load_graph("chat-1")
    assert loaded.number_of_nodes() == 0


def test_add_triple(gm):
    gm.create_graph("chat-1")
    gm.add_triple("chat-1", "user", "likes", "pizza")
    g = gm.load_graph("chat-1")
    assert g.has_edge("user", "pizza")
    assert g["user"]["pizza"]["relation"] == "likes"


def test_query_context(gm):
    gm.create_graph("chat-1")
    gm.add_triple("chat-1", "user", "likes", "pizza")
    gm.add_triple("chat-1", "user", "likes", "coding")
    ctx = gm.query_context("chat-1", ["user"])
    assert "pizza" in ctx
    assert "coding" in ctx


def test_delete_graph(gm):
    gm.create_graph("chat-1")
    assert gm.delete_graph("chat-1") is True
    assert gm.load_graph("chat-1").number_of_nodes() == 0


def test_reset_graph(gm):
    gm.create_graph("chat-1")
    gm.add_triple("chat-1", "user", "likes", "pizza")
    gm.reset_graph("chat-1")
    assert gm.load_graph("chat-1").number_of_nodes() == 0


def test_get_graph_data(gm):
    gm.create_graph("chat-1")
    gm.add_triple("chat-1", "user", "likes", "pizza")
    data = gm.get_graph_data("chat-1")
    assert len(data.nodes) == 2
    assert len(data.edges) == 1


def test_prune_graph(gm):
    gm.create_graph("chat-1")
    for i in range(100):
        gm.add_triple("chat-1", f"entity{i}", "related_to", f"other{i}")
    gm.prune_graph("chat-1", max_nodes=50)
    assert gm.load_graph("chat-1").number_of_nodes() <= 50
