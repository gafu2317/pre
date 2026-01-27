from typing import List, Optional
from pydantic import BaseModel

class Node(BaseModel):
    id: str
    content: str
    speaker: str | None = None
    type: str
    sequence: int | None = None
    position_2d: list[float] | None = None # 2D座標 (PCAなどで削減された結果)
    embedding: list[float] | None = None # LLMによるベクトル表現
    cosine_sim_to_first: float | None = None # 最初のノードとのコサイン類似度 (色相決定用)

class Edge(BaseModel):
    source: str
    target: str
    label: str

class ArgumentGraph(BaseModel):
    nodes: List[Node]
    edges: List[Edge]
