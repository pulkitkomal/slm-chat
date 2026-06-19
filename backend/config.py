from pydantic_settings import BaseSettings


class Config(BaseSettings):
    ollama_base_url: str = "http://localhost:11434"
    model_name: str = "floxy/LFM2.5-Instruct:1.2b"
    db_path: str = "data/slm-chat.db"
    graph_dir: str = "data/graphs"
    max_graph_nodes: int = 5000
    context_window: int = 4096

    class Config:
        env_prefix = "SLM_"


config = Config()
