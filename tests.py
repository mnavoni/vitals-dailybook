import io
import json

import pytest

import app
from domain import InvalidPatientReadingError


@pytest.fixture()
def base_data():
    data = [
        {"patient_id": "p1", "type": "bp_sys", "value": 182, "timestamp": "2025-10-19T01:02:03"},
        {"patient_id": "p1", "type": "pulse", "value": 77, "timestamp": "2025-10-19T20:11:20"},
        {"patient_id": "p2", "type": "spo2", "value": 88, "timestamp": "2025-10-19T18:19:20"},
        {"patient_id": "p2", "type": "pulse", "value": 130, "timestamp": "2025-10-19T13:14:15"},
    ]
    return data


def test_pass_original_assignment(capsys, base_data: list[dict]):
    # the expected output had to be modified because it didn't make real sense
    expected_output = {
"p1|2025-10-19": {"critical":1,"warning":0,"ok":0,"needs_attention":True},
"p2|2025-10-19": {"critical":1,"warning":1,"ok":0,"needs_attention":True}
}
    expected = json.loads(json.dumps(expected_output, sort_keys=True))
    app.main(base_data)
    result = json.loads(capsys.readouterr().out)

    assert str(result) == str(expected)


def test_no_rows(capsys, base_data: list[dict]):
    data = []

    with pytest.raises(ValueError):
        app.main(data)


def test_datetime_tz_mix(capsys):
    data = [
        {"patient_id": "p1", "type": "bp_sys", "value": 182, "timestamp": "2025-10-18T23:02:03-11:00"},
        {"patient_id": "p1", "type": "pulse", "value": 77, "timestamp": "2025-10-19T20:11:20"},
        {"patient_id": "p1", "type": "spo2", "value": 88, "timestamp": "2025-10-19T18:19:20Z"},
        {"patient_id": "p1", "type": "pulse", "value": 130, "timestamp": "2025-10-20T01:14:15+08:00"},
    ]

    app.main(data)
    result = json.loads(capsys.readouterr().out)
    assert len(result) == 1

def test_bad_value_type(capsys, base_data: list[dict]):
    app.main(base_data)

    base_data[2]["type"] = "badtype"

    with pytest.raises(InvalidPatientReadingError):
        app.main(base_data)


def test_bad_timestamp(capsys, base_data: list[dict]):
    app.main(base_data)

    base_data[3]["timestamp"] = "222"

    with pytest.raises(InvalidPatientReadingError):
        app.main(base_data)


def test_ok_patient(capsys):
    base_data = [
        {"patient_id": "p4", "type": "spo2", "value": 90, "timestamp": "2025-10-19T11:13:20Z"},
        {"patient_id": "p4", "type": "bp_sys", "value": 179.99, "timestamp": "2025-10-19T12:13:20Z"},
        {"patient_id": "p4", "type": "bp_dia", "value": 119.999, "timestamp": "2025-10-19T13:13:20Z"},
        {"patient_id": "p4", "type": "pulse", "value": 50, "timestamp": "2025-10-19T14:13:20Z"},
        {"patient_id": "p4", "type": "pulse", "value": 120, "timestamp": "2025-10-19T15:13:20Z"},
    ]

    app.main(base_data)
    result = json.loads(capsys.readouterr().out)
    assert result["p4|2025-10-19"]["ok"] == 1


def test_bad_health_patient(capsys):
    base_data = [
        {"patient_id": "p4", "type": "spo2", "value": 89.0000001, "timestamp": "2025-10-19T11:13:20Z"},
        {"patient_id": "p4", "type": "bp_sys", "value": 180.0001, "timestamp": "2025-10-19T12:13:20Z"},
        {"patient_id": "p4", "type": "bp_dia", "value": 120.0000123, "timestamp": "2025-10-19T13:13:20Z"},
        {"patient_id": "p4", "type": "pulse", "value": 49.991329, "timestamp": "2025-10-19T14:13:20Z"},
        {"patient_id": "p4", "type": "pulse", "value": 120.000000002, "timestamp": "2025-10-19T15:13:20Z"},
    ]

    app.main(base_data)
    result = json.loads(capsys.readouterr().out)
    record = result["p4|2025-10-19"]
    assert record["ok"] == 0
    assert record["critical"] == 3
    assert record["warning"] == 2


def test_needs_attention(capsys):
    base_data = [
        {"patient_id": "p4", "type": "spo2", "value": 52, "timestamp": "2025-10-01T12:13:20Z"},
        {"patient_id": "p4", "type": "bp_sys", "value": 12, "timestamp": "2025-10-02T12:13:20Z"},
        {"patient_id": "p4", "type": "pulse", "value": 49.991329, "timestamp": "2025-10-03T14:13:20Z"},
        {"patient_id": "p4", "type": "pulse", "value": 120.000000002, "timestamp": "2025-10-03T15:13:20Z"},
        {"patient_id": "p4", "type": "bp_dia", "value": 123, "timestamp": "2025-10-04T13:13:20Z"},
        {"patient_id": "p4", "type": "pulse", "value": 122, "timestamp": "2025-10-04T15:13:20Z"},
    ]

    app.main(base_data)
    result = json.loads(capsys.readouterr().out)
    assert result["p4|2025-10-01"]["needs_attention"] is True
    assert result["p4|2025-10-02"]["needs_attention"] is False
    assert result["p4|2025-10-03"]["needs_attention"] is True

    assert result["p4|2025-10-04"]["critical"] == 1
    assert result["p4|2025-10-04"]["warning"] == 1
    assert result["p4|2025-10-04"]["needs_attention"] is True


# todo: other tests:
#  many patient/day mixes
#  weird values, None, huge values
#  dates older than 1970, dates in the extreme future