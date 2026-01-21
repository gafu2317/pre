from typing import List, Optional
from pydantic import BaseModel

class Node(BaseModel):
    id: str
    type: str       # issue, position, argument, decision
    content: str
    speaker: Optional[str] = None
    position_2d: Optional[List[float]] = None
    sequence: Optional[int] = None

class Edge(BaseModel):
    source: str
    target: str
    label: str      # supports, opposes, replies_to

class ArgumentGraph(BaseModel):
    nodes: List[Node]
    edges: List[Edge]
