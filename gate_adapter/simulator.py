"""Fail-closed, in-memory gate simulator with explicit operator confirmation."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

@dataclass
class GateState:
    gate_id: int
    locked: bool = True
    opened_until: datetime | None = None

class GateSimulator:
    def __init__(self):
        self.gates: dict[int, GateState] = {}

    def status(self, gate_id: int) -> GateState:
        state = self.gates.setdefault(gate_id, GateState(gate_id))
        if state.opened_until and datetime.now(timezone.utc) >= state.opened_until:
            state.locked = True
            state.opened_until = None
        return state

    def request_open(self, gate_id: int, *, operator_confirmed: bool, permitted: bool, seconds: int = 3) -> GateState:
        if not isinstance(gate_id, int) or gate_id < 1:
            raise ValueError("Invalid gate")
        if not operator_confirmed or not permitted:
            raise PermissionError("Gate requires confirmed operator approval and valid permission")
        if not 1 <= seconds <= 10:
            raise ValueError("Open interval must be 1-10 seconds")
        state = self.status(gate_id)
        state.locked = False
        state.opened_until = datetime.now(timezone.utc) + timedelta(seconds=seconds)
        return state

    def lock(self, gate_id: int) -> GateState:
        state = self.status(gate_id)
        state.locked = True
        state.opened_until = None
        return state
