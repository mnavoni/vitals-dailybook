# Vitals DailyBook

## Patient data aggregator

This software is a sample script about a service
that turns patient records into daily aggregations


## How to install

### clone repo
### (optional) create a virtual env and activate it
```
conda create --name vitals-dailybook python=3.12
conda activate vitals-dailybook
```

### install dependencies
```
pip install -r requirements.txt
```

### run
```
(vitals-dailybook) user@pc:~/vitals-dailybook$ python -m app -h
usage: vitals-dailybook [-h] filename

Classifies each reading and produces a per-patient, per-day summary

positional arguments:
  filename

options:
  -h, --help  show this help message and exit

Made with care, by mnavoni
```

## Contributing
### install dev requirements
```
pip install -r requirements-dev.txt
```

### install pre-commit
```
pre-commit install
```

### run tests
```
pytest
```
