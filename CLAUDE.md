# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running

```bash
# Convert .sub to .f32 (RF audio)
python3 convert.py data/subfiles/<file>.sub

# Classify a single capture
python3 analyze.py data/subfiles/<file>.sub

# Batch summary
python3 analyze.py data/subfiles/ --summary-only

# JSON output
python3 analyze.py data/subfiles/ --json

# Save GeoJSON (only captures with real GPS coords)
python3 analyze.py data/subfiles/ --geojson wardrive.geojson

# Log to SQLite database
python3 analyze.py data/subfiles/ --db session.db

# View database summary
python3 analyze.py --db-summary session.db
```

**Dependency:** `numpy`, `pytest` (no requirements.txt; install manually if needed)

## Architecture

Two files:
- `analyze.py` — all signal analysis (parse, features, decode, classify, output, CLI)
- `wardrive_db.py` — SQLite session database (`WardriveDB` class)

`convert.py` converts Flipper Zero SubGhz BinRAW captures (`.sub`) to float32 audio sample files (`.f32`) for RF signal analysis.

**Data flow:** `.sub` → `parse_sub_file()` → `SubFile` → `extract_features()` → `FeatureVector` → `classify()` → `ClassificationResult` → `format_report()` / `format_json()` / `format_geojson()`

**Classifier pipeline order (first match wins):**
NOISE → AMR_METER → TPMS → ALARM_SENSOR → SHUTTER_BLIND → DOORBELL → OUTLET_SWITCH → GARAGE_REMOTE → KEYFOB_REMOTE → WEATHER_STATION → UNKNOWN_STRUCTURED

**Decode helpers:** `detect_pwm_params` + `decode_pwm_bits` (OOK PWM), `decode_manchester` (Manchester dual-convention), `detect_rolling_code` (compare payloads across segments)

**Supported frequencies:** 315MHz, 433.42MHz, 433.92MHz, 868.35MHz, 915MHz

**`.sub` file format** (Flipper SubGhz Key File v1):
- `Frequency:` — Hz (integer)
- `TE:` — timing element in microseconds; each bit maps to this duration
- `Lat:` / `Lon:` — optional GPS coordinates
- `Preset:` — modulation preset string
- `Bit_RAW:` / `Data_RAW:` — hex-encoded bytes; bits extracted MSB-first; each `Data_RAW` line is kept as a separate segment

**Sample data** is in `data/subfiles/`.
**Tests** are in `tests/` — run with `python3 -m pytest tests/ -v`.
