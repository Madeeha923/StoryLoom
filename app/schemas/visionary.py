from pydantic import BaseModel


class VisionaryAnalysis(BaseModel):
    category: str
    fabric: str
    color: str
    pattern: str
    descriptive_paragraph: str

