from pydantic import BaseModel


class RoadmapItem(BaseModel):
    skill: str
    description: str
    importance: str
    estimated_time: str
    difficulty: str
    free_resources: list[str]
    paid_resources: list[str]
    youtube: list[str]
    practice_sites: list[str]


class RoadmapOut(BaseModel):
    target_role: str
    roadmap: list[RoadmapItem]
