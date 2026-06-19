import json
from pathlib import Path
from typing import Optional

import networkx as nx

from config import config
from models import GraphData, GraphEdge, GraphNode


class GraphMemory:
    def __init__(self, graph_dir: str = config.graph_dir):
        self.graph_dir = Path(graph_dir)
        self.graph_dir.mkdir(parents=True, exist_ok=True)
        self._graphs: dict[str, nx.DiGraph] = {}

    def _graph_path(self, chat_id: str) -> Path:
        return self.graph_dir / f"{chat_id}.json"

    def create_graph(self, chat_id: str) -> nx.DiGraph:
        g = nx.DiGraph()
        self._graphs[chat_id] = g
        self._save_graph(chat_id, g)
        return g

    def load_graph(self, chat_id: str) -> nx.DiGraph:
        if chat_id in self._graphs:
            return self._graphs[chat_id]
        path = self._graph_path(chat_id)
        if path.exists():
            data = json.loads(path.read_text())
            g = nx.node_link_graph(data, directed=True, edges="edges")
            self._graphs[chat_id] = g
            return g
        return self.create_graph(chat_id)

    def _save_graph(self, chat_id: str, g: nx.DiGraph):
        data = nx.node_link_data(g, edges="edges")
        self._graph_path(chat_id).write_text(json.dumps(data, indent=2))

    def add_triple(self, chat_id: str, subject: str, relation: str, obj: str, properties: Optional[dict] = None):
        g = self.load_graph(chat_id)
        if subject not in g:
            g.add_node(subject, label=subject, node_type="entity", count=0)
        if obj not in g:
            g.add_node(obj, label=obj, node_type="entity", count=0)
        if g.has_edge(subject, obj):
            g[subject][obj]["weight"] = g[subject][obj].get("weight", 1) + 1
            g[subject][obj]["relation"] = relation
            g[subject][obj]["count"] = g[subject][obj].get("count", 1) + 1
        else:
            g.add_edge(subject, obj, relation=relation, weight=1.0, count=1)
        g.nodes[subject]["count"] = g.nodes[subject].get("count", 0) + 1
        g.nodes[obj]["count"] = g.nodes[obj].get("count", 0) + 1
        if properties:
            g.nodes[subject].update(properties)
            g.nodes[obj].update(properties)
        self._save_graph(chat_id, g)

    def query_context(self, chat_id: str, entities: list[str], max_results: int = 10) -> str:
        g = self.load_graph(chat_id)
        context_parts = []
        seen = set()
        for entity in entities:
            if entity not in g:
                continue
            neighbors = list(g.successors(entity)) + list(g.predecessors(entity))
            for neighbor in neighbors[:max_results]:
                edge_data = g.get_edge_data(entity, neighbor) or g.get_edge_data(neighbor, entity)
                if edge_data and (entity, neighbor) not in seen:
                    seen.add((entity, neighbor))
                    rel = edge_data.get("relation", "related_to")
                    context_parts.append(f"{entity} --({rel})--> {neighbor}")
        return "\n".join(context_parts[:max_results])

    def delete_graph(self, chat_id: str) -> bool:
        self._graphs.pop(chat_id, None)
        path = self._graph_path(chat_id)
        if path.exists():
            path.unlink()
            return True
        return False

    def reset_graph(self, chat_id: str) -> nx.DiGraph:
        self.delete_graph(chat_id)
        return self.create_graph(chat_id)

    def get_graph_data(self, chat_id: str) -> GraphData:
        g = self.load_graph(chat_id)
        nodes = [
            GraphNode(id=n, label=data.get("label", n), node_type=data.get("node_type", "entity"), properties=dict(data))
            for n, data in g.nodes(data=True)
        ]
        edges = [
            GraphEdge(source=u, target=v, relation=data.get("relation", "related_to"), weight=data.get("weight", 1.0))
            for u, v, data in g.edges(data=True)
        ]
        return GraphData(nodes=nodes, edges=edges)

    def prune_graph(self, chat_id: str, max_nodes: int = 5000):
        g = self.load_graph(chat_id)
        if g.number_of_nodes() <= max_nodes:
            return
        nodes_sorted = sorted(g.nodes(data=True), key=lambda x: x[1].get("count", 0))
        to_remove = [n for n, _ in nodes_sorted[: g.number_of_nodes() - max_nodes]]
        g.remove_nodes_from(to_remove)
        self._save_graph(chat_id, g)


graph_memory = GraphMemory()
