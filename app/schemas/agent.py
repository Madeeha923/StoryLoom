from typing import Any

from pydantic import BaseModel, Field


class AgentResponse(BaseModel):
    agent: str
    status: str = "success"
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)

