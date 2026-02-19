from enum import Enum, auto

import pandas as pd


class InvalidPatientReadingError(ValueError):
    pass


class PatientReadingType(Enum):
    BP_SYS = auto()
    BP_DIA = auto()
    PULSE = auto()
    SPO2 = auto()


def _analyze_patient_readings(readings: pd.DataFrame) -> None:
    # developer commentary: this function has side effects (modifying the source dataframe), so it must return None
    _spo_readings = readings["type"] == PatientReadingType.SPO2.name.lower()

    readings["spo_low"] = _spo_readings & (readings["value"] < 90)

    _bp_sys_readings = readings["type"] == PatientReadingType.BP_SYS.name.lower()
    readings["bp_sys_high"] = _bp_sys_readings & (readings["value"] >= 180)

    _bp_dia_readings = readings["type"] == PatientReadingType.BP_DIA.name.lower()
    readings["bp_dia_high"] = _bp_dia_readings & (readings["value"] >= 120)

    _pulse_readings = readings["type"] == PatientReadingType.PULSE.name.lower()
    readings["pulse_low"] = _pulse_readings & (readings["value"] < 50)
    readings["pulse_high"] = _pulse_readings & (readings["value"] > 120)

    readings["warning"] = readings[["pulse_low", "pulse_high"]].any(axis="columns")

    readings["critical"] = readings[["spo_low", "bp_sys_high", "bp_dia_high"]].any(
        axis="columns"
    )

    readings["is_ok"] = ~readings[["critical", "warning"]].any(axis="columns")


def _daily_aggregation(patient_readings: pd.DataFrame) -> pd.DataFrame:
    # developer commentary: this is where the magic happens. I expect the pandas library to use a properly
    # optimized algorithm for grouping
    patient_days = patient_readings.groupby(
        [pd.Grouper(key="timestamp", freq="D", origin="start_day"), "patient_id"]
    )

    result = patient_days.aggregate(
        {"warning": "sum", "critical": "sum", "is_ok": "sum"}
    )[["warning", "critical", "is_ok"]].reset_index()

    result["timestamp"] = result["timestamp"].dt.date

    result = result.rename(
        columns={
            "timestamp": "day_utc",
            "warning": "warning_count",
            "critical": "critical_count",
            "is_ok": "is_ok_count",
        }
    )

    result["needs_attention"] = (result["warning_count"] >= 2) | (
        result["critical_count"]
    )
    return result


def daily_patient_summary(patient_readings: pd.DataFrame) -> pd.DataFrame:
    """
    Produces a per-patient, per-day summary based on patient_readings DataFrame.
    :param patient_readings: Dataframe which has the following columns:
    patient_id, type, value, timestamp
    :return: Dataframe with columns: day, patient_id, warning_count, critical_count, is_ok, needs_attention
    """
    # developer commentary: I use pandas because I expect this service to process a big amount of records.
    _analyze_patient_readings(patient_readings)

    result = _daily_aggregation(patient_readings)

    return result
