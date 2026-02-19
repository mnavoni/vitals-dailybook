import argparse
import json
import sys

import pandas as pd

import services
from domain import InvalidPatientReadingError

parser = argparse.ArgumentParser(
                    prog='vitals-dailybook',
                    description='Classifies each reading and produces a per-patient, per-day summary',
                    epilog='Made with care, by mnavoni')
parser.add_argument("filename")


def _load_file(filename: str) -> pd.DataFrame:
    if filename.endswith(".csv"):
        input_data = pd.read_csv(filename)
    elif filename.endswith(".json"):
        try:
            input_data = pd.DataFrame.from_records(json.load(open(filename)))
        except json.decoder.JSONDecodeError:
            raise InvalidPatientReadingError("Error parsing .json file")
    else:
        raise InvalidPatientReadingError("Input data must be .json or .csv")

    return input_data


def main(input_data: str | list[dict] | pd.DataFrame) -> None:
    if isinstance(input_data, str):
        _data = _load_file(input_data)

    elif isinstance(input_data, list):
        _data = pd.DataFrame.from_records(data=input_data)

    elif isinstance(input_data, pd.DataFrame):
        _data = input_data

    else:
        raise ValueError(f"Invalid input data: {input_data}")

    if _data.empty:
        raise InvalidPatientReadingError("Input data must not be empty")

    readings = services.sanitize_df(_data)

    res = services.get_daily_patient_summary(readings)

    res.index = res["patient_id"] + "|" + res["day_utc"].astype(str)
    res = res.drop(columns=["patient_id", "day_utc"])
    res = res.rename(columns={"critical_count": "critical",
                              "warning_count": "warning",
                              "is_ok": "ok",
                              })
    res["ok"] = res["ok"].astype(int)

    print(json.dumps(res.to_dict(orient="index"), indent=4, default=str, sort_keys=True))


if __name__ == "__main__":
    args = parser.parse_args()
    try:
        main(args.filename)
        # todo: differentiate exceptions raised from service, presentation and domain layer
    except InvalidPatientReadingError as e:
        print(f"Invalid input file: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"File not found: {args.filename}")
