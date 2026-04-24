from datetime import datetime
from typing import Literal, Optional
from uuid import UUID
from pydantic import BaseModel, Field


AssetClass = Literal[
    "Silo", "Tank", "Blower", "Filler", "Capper", "Labeler", "Inspector",
    "Packer", "Palletizer", "Compressor", "Chiller", "Dryer", "CIP",
    "WaterTreatment", "ControlRoom", "LoadDock", "Pipe", "Valve",
    "Instrument", "Motor", "Conveyor",
]

State = Literal["operating", "idle", "alarm", "maintenance", "offline"]
Criticality = Literal["A", "B", "C"]


class Geometry(BaseModel):
    mesh_uri: str
    lod: int = Field(500, ge=100, le=600)
    bbox: tuple[float, float, float, float, float, float]


class Position(BaseModel):
    x: float; y: float; z: float
    rx: float = 0; ry: float = 0; rz: float = 0
    scale: float = 1


class ProcessAttrs(BaseModel):
    fluid: Optional[str] = None
    flow_rate_nominal: Optional[float] = None
    flow_rate_unit: Optional[str] = None
    pressure_nominal: Optional[float] = None
    temperature_nominal: Optional[float] = None


class MaintenanceAttrs(BaseModel):
    criticality: Criticality = "C"
    mtbf_hours: Optional[float] = None
    mttr_minutes: Optional[float] = None
    next_pm: Optional[datetime] = None
    cmms_id: Optional[str] = None


class SensorRef(BaseModel):
    tag: str
    kind: str
    unit: str
    threshold_low: Optional[float] = None
    threshold_high: Optional[float] = None


class DocRef(BaseModel):
    id: UUID
    kind: Literal["MANUAL", "PID", "ISO", "SPEC", "CERT", "MSDS", "SOP", "PHOTO", "PM"]
    name: str
    uri: str
    pages: Optional[int] = None


class Lifecycle(BaseModel):
    installed: Optional[datetime] = None
    warranty_ends: Optional[datetime] = None
    expected_eol: Optional[datetime] = None


class Asset(BaseModel):
    id: UUID
    tag: str
    name: str
    cls: AssetClass
    parent_id: Optional[UUID] = None
    geometry: Geometry
    position: Position
    process: Optional[ProcessAttrs] = None
    maintenance: MaintenanceAttrs = MaintenanceAttrs()
    sensors: list[SensorRef] = []
    documents: list[DocRef] = []
    lifecycle: Optional[Lifecycle] = None
    cost_ytd_usd: Optional[float] = None
    cost_center: Optional[str] = None
    state: State = "operating"
    source: str = "manual"
    updated_at: datetime
