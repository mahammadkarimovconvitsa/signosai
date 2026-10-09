from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import AutonomyLevel


class SettingsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    autonomy_level: AutonomyLevel


class SettingsUpdate(BaseModel):
    autonomy_level: AutonomyLevel


class BusinessConfigOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    key: str
    value: str
    description: str | None


class BusinessConfigUpdate(BaseModel):
    value: str
    description: str | None = None
