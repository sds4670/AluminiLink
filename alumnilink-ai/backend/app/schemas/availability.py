from datetime import date, time, datetime, timedelta
from zoneinfo import ZoneInfo
from pydantic import BaseModel, model_validator

MIN_LEAD_TIME = timedelta(hours=1)

# The backend container's system clock runs in UTC (confirmed: `date` on the
# host shows IST, `datetime.now()` in the container shows UTC), but
# slot_date/start_time are submitted by the browser as plain local wall-clock
# values with no timezone attached — they mean "10am for everyone at this
# university," i.e. IST, never UTC. Comparing them against UTC "now" was
# silently wrong by 5.5 hours in both directions (a slot minutes in the past
# could pass, and a genuinely valid near-term slot could get rejected).
# Single-timezone deployment, so this is hardcoded rather than configurable.
APP_TIMEZONE = ZoneInfo("Asia/Kolkata")


def _check_slot_times(slot_date: date, start_time: time, end_time: time) -> None:
    if end_time <= start_time:
        raise ValueError("end_time must be after start_time")
    now_local = datetime.now(APP_TIMEZONE)
    if slot_date < now_local.date():
        raise ValueError("slot_date cannot be in the past")
    slot_start = datetime.combine(slot_date, start_time, tzinfo=APP_TIMEZONE)
    if slot_start < now_local + MIN_LEAD_TIME:
        raise ValueError("start_time must be at least 1 hour from now")


class AvailabilitySlotCreate(BaseModel):
    slot_date: date
    start_time: time
    end_time: time

    @model_validator(mode="after")
    def check_times(self) -> "AvailabilitySlotCreate":
        _check_slot_times(self.slot_date, self.start_time, self.end_time)
        return self


class AvailabilitySlotUpdate(BaseModel):
    slot_date: date
    start_time: time
    end_time: time

    @model_validator(mode="after")
    def check_times(self) -> "AvailabilitySlotUpdate":
        _check_slot_times(self.slot_date, self.start_time, self.end_time)
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
