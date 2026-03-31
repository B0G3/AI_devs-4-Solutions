import json
import os

from langchain_core.tools import tool

from utils.api import call, get_result_blocking
from logger import get_logger

log = get_logger("generate_signed_config")


def _compute_configs(
    forecast: list[dict],
    cutoff_wind_ms: float,
    min_operational_wind_ms: float,
) -> list[dict]:
    storm_configs: list[dict] = []
    production_candidates: list[dict] = []

    for point in forecast:
        wind = float(point["windMs"])
        date = point["timestamp"][:10]
        hour = f"{int(point['timestamp'][11:13]):02d}:00"

        if wind >= cutoff_wind_ms:
            storm_configs.append({
                "startDate": date,
                "startHour": hour,
                "windMs": wind,
                "pitchAngle": 90,
                "turbineMode": "idle",
            })
        elif wind >= min_operational_wind_ms:
            production_candidates.append({
                "startDate": date,
                "startHour": hour,
                "windMs": wind,
                "pitchAngle": 0,
                "turbineMode": "production",
            })

    configs = list(storm_configs)
    if production_candidates:
        best = max(production_candidates, key=lambda x: x["windMs"])
        configs.append(best)

    log.info(
        "computed %d configs: %d storm, %d production",
        len(configs),
        len(storm_configs),
        1 if production_candidates else 0,
    )
    return configs


@tool
def windpower_generate_signed_config(
    weather_file: str,
    cutoff_wind_ms: float,
    min_operational_wind_ms: float,
) -> str:
    """Compute turbine configs from a weather JSON file, sign them, submit, and call done.

    Args:
        weather_file: Absolute path to weather.json written by windpower_fetch_documentation.
                      Reads the forecast from the "forecast" key.
        cutoff_wind_ms: From documentation.json → safety.cutoffWindMs.
                        Wind at or above this speed requires shutdown (pitchAngle=90, idle).
        min_operational_wind_ms: From documentation.json → safety.minOperationalWindMs.
                                 Minimum wind speed for electricity generation.

    Rules applied deterministically:
    - wind >= cutoff_wind_ms                            → pitchAngle=90, turbineMode=idle  (all storm slots)
    - min_operational_wind_ms <= wind < cutoff_wind_ms  → pitchAngle=0,  turbineMode=production (single best slot)
    - wind < min_operational_wind_ms                    → omitted

    Returns:
        JSON string with the final API response from "done".
    """
    with open(weather_file) as f:
        weather_data = json.load(f)
    forecast: list[dict] = weather_data["forecast"]

    configs = _compute_configs(forecast, cutoff_wind_ms, min_operational_wind_ms)

    configs_with_codes: list[dict] = []
    for point in configs:
        call({
            "action": "unlockCodeGenerator",
            "startDate": point["startDate"],
            "startHour": point["startHour"],
            "windMs": point["windMs"],
            "pitchAngle": point["pitchAngle"],
        })
        unlock_result = get_result_blocking()
        configs_with_codes.append({**point, "unlockCode": unlock_result.get("unlockCode", "")})

    call({"action": "config", "configs": configs_with_codes})

    result = call({"action": "done"})
    return json.dumps(result, ensure_ascii=False)
