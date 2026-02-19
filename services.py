import pandas as pd

import domain
from domain import InvalidPatientReadingError, PatientReadingType

ALLOWED_TYPES = {prt.name.lower() for prt in list(PatientReadingType)}


def sanitize_df(patient_readings: pd.DataFrame) -> pd.DataFrame:
    # developer commentary: I won't be lenient on the input in this instance
    # because this software will be used for healthcare purposes

    expected_columns = {"patient_id", "type", "timestamp", "value"}
    unknown_columns = expected_columns - set(patient_readings.columns)
    if unknown_columns:
        raise InvalidPatientReadingError(f"Unexpected column(s) provided {unknown_columns}")
    _patient_readings = patient_readings.copy(deep=True)

    if _patient_readings["patient_id"].isna().any():
        raise InvalidPatientReadingError("Invalid patient_id found in data")

    reading_types = set(_patient_readings["type"].unique())

    unknown_types = reading_types - ALLOWED_TYPES
    if unknown_types:
        raise InvalidPatientReadingError(f"Invalid reading type(s) found: {unknown_types}")

    try:
        # accepting any kind of ISO8601 timestamp, probably should enforce UTC on input
        _patient_readings["timestamp"] = pd.to_datetime(_patient_readings["timestamp"],
                                                        format="ISO8601",
                                                        utc=True,
                                                        errors="raise"
                                                        )
    except Exception as e:
        raise InvalidPatientReadingError(f"Invalid timestamp found") from e

    try:
        _patient_readings["value"] = _patient_readings["value"].astype(float, errors="raise")
    except Exception as e:
        raise InvalidPatientReadingError(f"Invalid 'value' found in data") from e

    return _patient_readings


def get_daily_patient_summary(input_data: pd.DataFrame) -> pd.DataFrame:
    return domain.daily_patient_summary(input_data)
