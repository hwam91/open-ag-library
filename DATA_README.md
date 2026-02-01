# FAOSTAT Data Files

The FAOSTAT data files are not included in this repository due to their large size (several GB total).

## Getting the Data

The data files are stored locally in two directories:
- `FAOSTAT_A-S_E/` - Datasets A through S
- `FAOSTAT_T-Z_E/` - Datasets T through Z

Each file is a zip archive containing:
- Main data CSV (normalized format)
- Area codes CSV
- Item codes CSV (when applicable)
- Element codes CSV (when applicable)
- Flags CSV

## Data Source

All data comes from FAOSTAT: https://www.fao.org/faostat/

Download the bulk data files from:
https://www.fao.org/faostat/en/#data

Select "Bulk Downloads" and choose "Normalized" format for all datasets.

## Data Structure

See `SCHEMA_NOTES.md` for detailed analysis of the data structure and schema design decisions.
