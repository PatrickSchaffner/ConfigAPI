#!/bin/bash
pip install .[tests]
pytest .
start firefox coverage/index.html
pip wheel --no-deps .
rm -rf build *.egg-info .coverage

