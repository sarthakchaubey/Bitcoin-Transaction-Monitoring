#!/usr/bin/env bash
set -e

python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "Setup complete."
echo "Reminder: manually download GeoLite2-City.mmdb from MaxMind (free account required)"
echo "and place it in the geoip/ directory."
