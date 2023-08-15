#!/bin/bash

set -eux

isort impall.py
black impall.py
ruff check --fix impall.py
mypy impall.py
pytest
