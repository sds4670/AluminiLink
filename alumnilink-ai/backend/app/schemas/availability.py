from datetime import date, time, datetime
from pydantic import BaseModel, model_validator


class AvailabilitySlotCreate(BaseModel):
    slot_date: date
    start_time: time
    end_time: time

    @model_validator(mode="after")
    def check_times(self) -> "AvailabilitySlotCreate":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        if self.slot_date < date.today():
            raise ValueError("slot_date cannot be in the past")
        return self


class AvailabilitySlotUpdate(BaseModel):
    slot_date: date
    start_time: time
    end_time: time

    @model_validator(mode="after")
    def check_times(self) -> "AvailabilitySlotUpdate":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class AvailabilitySlotResponse(BaseModel):
    id: int
    alumni_id: int
    slot_date: date
    start_time: time
    end_time: time
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
