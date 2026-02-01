# Open Ag Library - Quick Start Guide

This guide will get you up and running with Open Ag Library in minutes.

## Prerequisites

- PostgreSQL installed and running
- Python 3.8+
- FAOSTAT data files (see DATA_README.md)

## Setup Steps

### 1. Clone and Setup Environment

```bash
# If not already done
git clone https://github.com/hwam91/open-ag-library.git
cd open-ag-library

# Run setup script
./setup.sh
source venv/bin/activate
```

### 2. Configure Database

Create `.env` file:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=open_ag_library
DB_USER=postgres
DB_PASSWORD=your_password

# Choose one:
OPENAI_API_KEY=sk-...
# OR
ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Create Database

```bash
# Create the database
createdb open_ag_library

# Initialize schema
psql -d open_ag_library -f schema.sql
```

### 4. Import Data

```bash
# This will take several hours for all datasets
python import_faostat.py
```

**Tip**: To import just a few datasets for testing, move most zip files to a backup folder temporarily.

### 5. Setup Vanna (Optional but Recommended)

```bash
python vanna_setup.py
```

This will:
- Train Vanna on your database schema
- Provide example queries
- Launch an interactive query interface

## Usage Examples

### Option 1: Direct SQL Queries

```sql
-- Connect to database
psql -d open_ag_library

-- Example: Top wheat producers in 2020
SELECT
    area_name,
    SUM(value) as production,
    unit
FROM faostat_data_view
WHERE item_name LIKE '%Wheat%'
    AND year = 2020
    AND element_name LIKE '%Production%'
GROUP BY area_name, unit
ORDER BY production DESC
LIMIT 10;
```

### Option 2: Vanna Natural Language Queries

```python
from vanna_setup import setup_vanna

# Setup
vn = setup_vanna(use_anthropic=True)  # or False for OpenAI

# Ask questions
vn.ask("What is wheat production in India in 2020?")
vn.ask("Show me rice production trends from 2015 to 2020")
vn.ask("Compare corn yields between USA and China")
```

### Option 3: Interactive Vanna Mode

```bash
python vanna_setup.py
# Follow prompts to enter interactive query mode
```

## What's in the Database?

Check what datasets you have:

```sql
SELECT dataset_code, dataset_name, file_rows, date_update
FROM datasets
ORDER BY dataset_name;
```

See available countries:

```sql
SELECT DISTINCT area_name
FROM areas
ORDER BY area_name;
```

See available crops/items:

```sql
SELECT DISTINCT item_name
FROM items
WHERE item_name IS NOT NULL
ORDER BY item_name
LIMIT 20;
```

## Common Queries

### Production Trends

```sql
SELECT
    year,
    SUM(value) as total_production
FROM faostat_data_view
WHERE area_name = 'United States of America'
    AND item_name LIKE '%Wheat%'
    AND element_name LIKE '%Production%'
GROUP BY year
ORDER BY year;
```

### Country Comparisons

```sql
SELECT
    area_name,
    year,
    AVG(value) as avg_yield
FROM faostat_data_view
WHERE item_name LIKE '%Rice%'
    AND element_name LIKE '%Yield%'
    AND year BETWEEN 2015 AND 2020
    AND area_name IN ('China', 'India', 'Indonesia')
GROUP BY area_name, year
ORDER BY area_name, year;
```

### Environmental Data

```sql
SELECT
    year,
    element_name,
    SUM(value) as emissions,
    unit
FROM faostat_data_view
WHERE area_name = 'World'
    AND dataset_name LIKE '%Emission%'
GROUP BY year, element_name, unit
ORDER BY year DESC;
```

## Metabase Integration

1. Install Metabase
2. Add PostgreSQL database connection
3. Use credentials from `.env`
4. Connect to `open_ag_library` database
5. Start with the `faostat_data_view` for easy dashboard creation

## Troubleshooting

### Import is slow
- Normal! Processing millions of rows takes time
- Consider importing one dataset at a time for testing
- Import runs in chunks to handle large files

### Vanna not generating good SQL
- Train it on more examples: `vn.train(question="...", sql="...")`
- The more you use it, the better it gets
- Check the generated SQL before running

### Out of memory during import
- Reduce chunk size in `import_faostat.py` (default: 10000)
- Import datasets one at a time
- Ensure PostgreSQL has adequate memory configuration

## Next Steps

- Explore the data using Vanna
- Create Metabase dashboards
- Train Vanna on domain-specific queries
- Build custom applications using the database

## Need Help?

- Check `SCHEMA_NOTES.md` for schema details
- See `README.md` for full documentation
- Review example queries in `vanna_setup.py`
