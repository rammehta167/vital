from fastapi import APIRouter, HTTPException, Depends
from ..schemas import SimulatorControlRequest, SimulatorStatusResponse, MessageResponse
from ..security import get_optional_current_user
from simulator.simulator import global_simulator

router = APIRouter(prefix="/api/v1/simulator", tags=["Hardware Simulator Control"])


@router.get("/status", response_model=SimulatorStatusResponse)
def get_simulator_status():
    return {
        "is_running": global_simulator.is_running,
        "current_scenario": global_simulator.scenario,
        "device_id": global_simulator.device_id,
        "buffered_count": len(global_simulator.buffered_readings),
        "target_url": global_simulator.target_url,
        "last_sent_at": global_simulator.last_sent_at
    }


@router.post("/control", response_model=SimulatorStatusResponse)
def control_simulator(req: SimulatorControlRequest):
    action = req.action.lower()
    if action == "start":
        global_simulator.start()
    elif action == "stop":
        global_simulator.stop()
    elif action == "switch_scenario":
        if not req.scenario:
            raise HTTPException(status_code=400, detail="Scenario must be provided for switch_scenario.")
        global_simulator.set_scenario(req.scenario)
        if not global_simulator.is_running:
            global_simulator.start()
    elif action == "trigger_sos":
        global_simulator.trigger_sos()
    elif action == "trigger_fall":
        global_simulator.trigger_fall()
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: '{action}'. Valid: start, stop, switch_scenario, trigger_sos, trigger_fall")

    return get_simulator_status()
