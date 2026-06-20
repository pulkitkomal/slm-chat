import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import networkx as nx

from config import config
from models import GraphData, GraphEdge, GraphNode

_MAX_ENTITY_LENGTH = 40


def _is_valid_entity(name: str) -> bool:
    name = name.strip()
    if not name:
        return False
    if len(name) > _MAX_ENTITY_LENGTH:
        return False
    words = name.split()
    if len(words) > 5:
        return False
    if name.lower() in ("user", "assistant", "system"):
        return True
    if len(words) >= 3 and re.search(r"\b(is|are|was|were|have|has|had)\b", name):
        return False
    if name.lower() in ("object", "subject", "relation", "person", "thing"):
        return False
    return True


def _normalize(name: str) -> str:
    return name.strip().lower()


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
        subj = _normalize(subject)
        obj = _normalize(obj)
        if not _is_valid_entity(subj) or not _is_valid_entity(obj):
            return
        g = self.load_graph(chat_id)
        if subj not in g:
            g.add_node(subj, label=subj, node_type="entity", count=0)
        if obj not in g:
            g.add_node(obj, label=obj, node_type="entity", count=0)
        if g.has_edge(subj, obj):
            g[subj][obj]["weight"] = g[subj][obj].get("weight", 1) + 1
            g[subj][obj]["relation"] = relation
        else:
            g.add_edge(subj, obj, relation=relation, weight=1.0)
        g.nodes[subj]["count"] = g.nodes[subj].get("count", 0) + 1
        g.nodes[obj]["count"] = g.nodes[obj].get("count", 0) + 1
        self._save_graph(chat_id, g)

    def add_emotion(self, chat_id: str, emotion: str, intensity: float):
        g = self.load_graph(chat_id)
        ts = datetime.now(timezone.utc).isoformat()
        if "user" not in g:
            g.add_node("user", label="user", node_type="entity", count=0, emotion_history=[])
        history = list(g.nodes["user"].get("emotion_history", []))
        history.append({"emotion": emotion, "intensity": intensity, "timestamp": ts})
        g.nodes["user"]["emotion_history"] = history[-20:]
        if emotion not in g:
            g.add_node(emotion, label=emotion, node_type="emotion", count=0)
        if g.has_edge("user", emotion):
            g["user"][emotion]["weight"] += 1
            g["user"][emotion]["intensity"] = (g["user"][emotion].get("intensity", intensity) + intensity) / 2
            g["user"][emotion]["timestamp"] = ts
        else:
            g.add_edge("user", emotion, relation="feels", weight=1.0, intensity=intensity, timestamp=ts)
        g.nodes["user"]["count"] = g.nodes["user"].get("count", 0) + 1
        g.nodes[emotion]["count"] = g.nodes[emotion].get("count", 0) + 1
        self._save_graph(chat_id, g)

    def get_current_emotion(self, chat_id: str) -> Optional[dict]:
        g = self.load_graph(chat_id)
        if "user" not in g:
            return None
        history = g.nodes["user"].get("emotion_history", [])
        if not history:
            return None
        return dict(history[-1])

    def get_emotion_context(self, chat_id: str) -> str:
        g = self.load_graph(chat_id)
        if "user" not in g:
            return ""
        history = g.nodes["user"].get("emotion_history", [])
        if not history:
            return ""
        current = history[-1]
        recent = history[-5:]
        lines = [f"The user's current emotion seems to be: {current['emotion']} (intensity {current['intensity']:.1f})"]
        if len(recent) > 1:
            trend = " → ".join(e["emotion"] for e in recent)
            lines.append(f"Recent emotional trend: {trend}")
        return "\n".join(lines)

    def _tokenize(self, text: str) -> set[str]:
        words = re.findall(r"[a-zA-Z]+", text.lower())
        return {w for w in words if len(w) > 2}

    def query_context(self, chat_id: str, texts: list[str], max_results: int = 8) -> str:
        g = self.load_graph(chat_id)
        if g.number_of_nodes() == 0:
            return ""

        all_tokens = set()
        for t in texts:
            all_tokens.update(self._tokenize(t))

        matched_entities = set()
        for node in g.nodes:
            if not _is_valid_entity(node):
                continue
            node_tokens = self._tokenize(node)
            if node_tokens and all_tokens & node_tokens:
                matched_entities.add(node)

        fallback = not matched_entities
        if not matched_entities:
            node_counts = [(n, g.nodes[n].get("count", 0)) for n in g.nodes if _is_valid_entity(n)]
            node_counts.sort(key=lambda x: -x[1])
            matched_entities = {n for n, _ in node_counts[:3]}

        scored = []
        seen = set()
        for entity in matched_entities:
            for neighbor in list(g.successors(entity)) + list(g.predecessors(entity)):
                if not _is_valid_entity(neighbor):
                    continue
                edge_data = g.get_edge_data(entity, neighbor) or g.get_edge_data(neighbor, entity)
                if not edge_data:
                    continue
                pair = tuple(sorted([entity, neighbor]))
                if pair in seen:
                    continue
                seen.add(pair)
                weight = edge_data.get("weight", 1)
                count = g.nodes[neighbor].get("count", 0)
                scored.append((weight + count * 0.5, entity, edge_data["relation"], neighbor))

        if not scored and not fallback:
            node_counts = [(n, g.nodes[n].get("count", 0)) for n in g.nodes if _is_valid_entity(n)]
            node_counts.sort(key=lambda x: -x[1])
            for entity, _ in node_counts[:3]:
                for neighbor in list(g.successors(entity)) + list(g.predecessors(entity)):
                    if not _is_valid_entity(neighbor):
                        continue
                    edge_data = g.get_edge_data(entity, neighbor) or g.get_edge_data(neighbor, entity)
                    if not edge_data:
                        continue
                    pair = tuple(sorted([entity, neighbor]))
                    if pair in seen:
                        continue
                    seen.add(pair)
                    weight = edge_data.get("weight", 1)
                    count = g.nodes[neighbor].get("count", 0)
                    scored.append((weight + count * 0.5, entity, edge_data["relation"], neighbor))

        scored.sort(key=lambda x: -x[0])
        lines = [f"{e} --({r})--> {n}" for _, e, r, n in scored[:max_results]]
        return "\n".join(lines)

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
