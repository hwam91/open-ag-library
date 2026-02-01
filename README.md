# Open Ag Library

A PostgreSQL-based system for querying FAOSTAT agricultural data using natural language via Vanna AI.

## Overview

Open Ag Library makes FAOSTAT data more accessible by:
- Storing all FAOSTAT datasets in a normalized PostgreSQL database
- Enabling natural language queries through Vanna AI
- Providing a foundation for integration with visualization tools like Metabase

## Project Structure

```
.
├── FAOSTAT_A-S_E/          # FAOSTAT data files (A-S datasets)
├── FAOSTAT_T-Z_E/          # FAOSTAT data files (T-Z datasets)
├── datasets_E.json         # Dataset metadata
├── schema.sql              # PostgreSQL database schema
├── import_faostat.py       # Data import script
├── analyze_schema.py       # Schema analysis tool
├── vanna_setup.py          # Vanna AI configuration
├── requirements.txt        # Python dependencies
├── .env.example           # Environment configuration template
└── README.md              # This file
```

## Quick Start

### 1. Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Git

### 2. Database Setup

Create a PostgreSQL database:

```bash
createdb open_ag_library
```

Initialize the schema:

```bash
psql -d open_ag_library -f schema.sql
```

### 3. Python Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Configuration

Copy the example environment file and configure:

```bash
cp .env.example .env
# Edit .env with your database credentials
```

### 5. Data Import

Analyze the schema structure:

```bash
python analyze_schema.py
```

Import FAOSTAT data into PostgreSQL:

```bash
python import_faostat.py
```

Note: Full import may take several hours depending on data volume.

### 6. Vanna AI Setup (Optional)

Configure Vanna for natural language queries. Vanna 0.7 is self-hosted and only requires an OpenAI or Anthropic API key (no Vanna API key needed):

```bash
# Add OPENAI_API_KEY or ANTHROPIC_API_KEY to .env first
python vanna_setup.py
```

The setup script will:
- Train Vanna on the database schema
- Provide example queries for agricultural data
- Store training data locally in ChromaDB
- Launch an interactive query interface

## Database Schema

### Core Tables

- **datasets** - Metadata about FAOSTAT datasets
- **areas** - Geographic areas/countries (dimension table)
- **items** - Agricultural items/commodities (dimension table)
- **elements** - Statistical elements like production, yield (dimension table)
- **flags** - Data quality flags
- **faostat_data** - Main fact table with all measurements

### Views

- **faostat_data_view** - Denormalized view joining all dimensions for easy querying

## Usage Examples

### Direct SQL Queries

```sql
-- Top 10 wheat producing countries in 2020
SELECT area_name, SUM(value) as production, unit
FROM faostat_data_view
WHERE item_name LIKE '%Wheat%'
  AND year = 2020
  AND element_name LIKE '%Production%'
GROUP BY area_name, unit
ORDER BY production DESC
LIMIT 10;
```

### Vanna AI Natural Language Queries

```python
from vanna_setup import setup_vanna

vn = setup_vanna()

# Ask questions in natural language
vn.ask("What is the total rice production in India in 2020?")
vn.ask("Show me crop production trends for China from 2010 to 2020")
```

## Data Sources

All data comes from FAOSTAT (Food and Agriculture Organization of the United Nations):
- Website: https://www.fao.org/faostat/
- Data downloaded in normalized CSV format
- Coverage: Multiple agricultural domains including production, trade, emissions, prices, etc.

## Schema Analysis

The FAOSTAT data follows a consistent structure:
- All datasets use normalized format with dimension tables
- Core columns: Area, Item, Element, Year, Value, Flag
- Optional columns: Months, Unit, Note (vary by dataset)
- Each dataset includes metadata files for lookups

Run `python analyze_schema.py` for detailed schema analysis.

## Integration with Metabase

To connect Metabase:

1. Install and run Metabase
2. Add PostgreSQL database connection using credentials from `.env`
3. Point to the `open_ag_library` database
4. Use the `faostat_data_view` for easier dashboard creation

## Development

### Adding New Datasets

1. Place new zip files in `FAOSTAT_A-S_E/` or `FAOSTAT_T-Z_E/`
2. Update `datasets_E.json` if needed
3. Run `python import_faostat.py`

### Training Vanna on New Queries

```python
vn.train(
    question="Your question here",
    sql="SELECT ... corresponding SQL"
)
```

## License

[To be determined]

## Contact

[Your contact information]

## Acknowledgments

- Food and Agriculture Organization (FAO) for providing FAOSTAT data
- Vanna AI for natural language SQL generation
