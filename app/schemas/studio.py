from pydantic import BaseModel, Field


class StudioScenePlan(BaseModel):
    scene_number: int
    scene_title: str
    duration_seconds: int
    scene_description: str
    frame_prompt: str
    transition_note: str


class StudioCampaignPlan(BaseModel):
    campaign_concept: str
    ad_script: str
    scene_descriptions: list[StudioScenePlan] = Field(default_factory=list)

