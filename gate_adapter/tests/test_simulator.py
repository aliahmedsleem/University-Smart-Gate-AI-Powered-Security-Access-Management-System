import pytest
from gate_adapter.simulator import GateSimulator

def test_fail_closed():
    sim = GateSimulator()
    assert sim.status(1).locked
    with pytest.raises(PermissionError):
        sim.request_open(1, operator_confirmed=False, permitted=True)
    with pytest.raises(PermissionError):
        sim.request_open(1, operator_confirmed=True, permitted=False)
    assert sim.status(1).locked

def test_operator_open_and_lock():
    sim = GateSimulator()
    assert not sim.request_open(1, operator_confirmed=True, permitted=True).locked
    assert sim.lock(1).locked

def test_invalid_interval():
    with pytest.raises(ValueError):
        GateSimulator().request_open(1, operator_confirmed=True, permitted=True, seconds=100)
