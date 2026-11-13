"""Schema for data extracted from a lab report. Also the ground-truth format for evals."""

from datetime import date, datetime
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, Field, field_validator, model_validator


class Sex(StrEnum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class ResultStatus(StrEnum):
    NORMAL = "normal"
    LOW = "low"
    HIGH = "high"
    CRITICAL_LOW = "critical_low"
    CRITICAL_HIGH = "critical_high"


class ReferenceRange(BaseModel):
    """Normal range. One side is None for ranges like '<100' (high only) or '>40' (low only)."""

    low: float | None = None
    high: float | None = None

    @model_validator(mode="after")
    def _check_bounds(self) -> Self:
        if self.low is None and self.high is None:
            raise ValueError("reference range needs low, high, or both")
        if self.low is not None and self.high is not None and self.low > self.high:
            raise ValueError("low must not exceed high")
        return self


class LabResult(BaseModel):
    name: str = Field(description="Test name as printed, e.g. 'Hemoglobin'")
    value: float
    unit: str | None = Field(default=None, description="Unit as printed, e.g. 'g/dL'")
    reference_range: ReferenceRange | None = None
    status: ResultStatus = Field(
        description="Interpretation of value against range. "
        "If the report prints no flag, derive it from value and range."
    )
    panel: str | None = Field(default=None, description="Section heading, e.g. 'Lipid Panel'")


class Patient(BaseModel):
    name: str
    sex: Sex | None = None
    date_of_birth: date | None = None
    patient_id: str | None = None


class LabReport(BaseModel):
    lab_name: str
    accession_number: str | None = Field(
        default=None, description="Lab's ID for this specimen or report"
    )
    patient: Patient
    ordering_physician: str | None = None
    collected_at: datetime | None = None
    reported_at: datetime | None = None
    results: list[LabResult] = Field(min_length=1)

    @field_validator("collected_at", "reported_at")
    @classmethod
    def _naive(cls, v: datetime | None) -> datetime | None:
        """Reports print local time with no timezone. Drop any 'Z' or offset an LLM adds."""
        return v.replace(tzinfo=None) if v else v
