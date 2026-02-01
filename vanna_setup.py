#!/usr/bin/env python3
"""
Vanna AI integration for Open Ag Library.
This script sets up Vanna 0.7.x to enable natural language querying of FAOSTAT data.
Uses self-hosted approach with OpenAI or Anthropic APIs (no Vanna API key needed).
"""

import os
from vanna.openai import OpenAI_Chat
from vanna.anthropic import Anthropic_Chat
from vanna.chromadb import ChromaDB_VectorStore
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'open_ag_library'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', '')
}

class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
    """Vanna instance using ChromaDB for vector storage and OpenAI for LLM."""
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)

class MyVannaAnthropic(ChromaDB_VectorStore, Anthropic_Chat):
    """Vanna instance using ChromaDB for vector storage and Anthropic for LLM."""
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        Anthropic_Chat.__init__(self, config=config)

def setup_vanna(use_anthropic=False):
    """
    Initialize and configure Vanna AI.

    Args:
        use_anthropic: If True, use Anthropic/Claude. Otherwise use OpenAI.

    Returns:
        Configured Vanna instance
    """
    if use_anthropic:
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            print("Error: ANTHROPIC_API_KEY not set in .env file")
            print("Please add: ANTHROPIC_API_KEY=your_key_here")
            return None

        vn = MyVannaAnthropic(config={
            'api_key': api_key,
            'model': 'claude-3-5-sonnet-20241022',
            'path': './vanna_chromadb'  # Local storage for training data
        })
    else:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("Error: OPENAI_API_KEY not set in .env file")
            print("Please add: OPENAI_API_KEY=your_key_here")
            return None

        vn = MyVanna(config={
            'api_key': api_key,
            'model': 'gpt-4o',  # or 'gpt-3.5-turbo' for faster/cheaper
            'path': './vanna_chromadb'  # Local storage for training data
        })

    # Connect to PostgreSQL
    vn.connect_to_postgres(
        host=DB_CONFIG['host'],
        dbname=DB_CONFIG['database'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        port=int(DB_CONFIG['port'])
    )

    print(f"✓ Connected to PostgreSQL database: {DB_CONFIG['database']}")
    return vn

def train_vanna_on_schema(vn):
    """Train Vanna on the database schema and common queries."""

    print("Training Vanna on database schema...")

    # Train on DDL - this helps Vanna understand the structure
    ddl_statements = [
        """
        -- Metadata about FAOSTAT datasets
        CREATE TABLE datasets (
            dataset_code VARCHAR(10) PRIMARY KEY,
            dataset_name TEXT NOT NULL,
            topic TEXT,
            description TEXT,
            contact TEXT,
            email VARCHAR(255),
            date_update TIMESTAMP
        );
        """,
        """
        -- Geographic areas/countries dimension table
        CREATE TABLE areas (
            area_code INTEGER PRIMARY KEY,
            m49_code VARCHAR(10),
            area_name TEXT NOT NULL
        );
        """,
        """
        -- Agricultural items/commodities dimension table
        CREATE TABLE items (
            item_code INTEGER PRIMARY KEY,
            cpc_code VARCHAR(20),
            item_name TEXT NOT NULL,
            dataset_code VARCHAR(10)
        );
        """,
        """
        -- Statistical elements dimension table (e.g., production, yield, area harvested)
        CREATE TABLE elements (
            element_code INTEGER PRIMARY KEY,
            element_name TEXT NOT NULL,
            dataset_code VARCHAR(10)
        );
        """,
        """
        -- Main fact table containing all FAOSTAT measurements
        CREATE TABLE faostat_data (
            id BIGSERIAL PRIMARY KEY,
            dataset_code VARCHAR(10),
            area_code INTEGER,
            item_code INTEGER,
            element_code INTEGER,
            year INTEGER NOT NULL,
            month_code INTEGER,
            month_name VARCHAR(20),
            value NUMERIC,
            unit VARCHAR(50),
            flag VARCHAR(10),
            note TEXT
        );
        """,
        """
        -- Denormalized view for easy querying
        CREATE VIEW faostat_data_view AS
        SELECT
            fd.id,
            fd.dataset_code,
            d.dataset_name,
            fd.area_code,
            a.area_name,
            a.m49_code,
            fd.item_code,
            i.item_name,
            fd.element_code,
            e.element_name,
            fd.year,
            fd.month_name,
            fd.value,
            fd.unit,
            fd.flag,
            fd.note
        FROM faostat_data fd
        LEFT JOIN datasets d ON fd.dataset_code = d.dataset_code
        LEFT JOIN areas a ON fd.area_code = a.area_code
        LEFT JOIN items i ON fd.item_code = i.item_code
        LEFT JOIN elements e ON fd.element_code = e.element_code;
        """
    ]

    for ddl in ddl_statements:
        vn.train(ddl=ddl)

    print(f"✓ Trained on {len(ddl_statements)} DDL statements")

    # Train on documentation to help with natural language understanding
    documentation = [
        "The faostat_data table contains agricultural statistics from FAO (Food and Agriculture Organization)",
        "The faostat_data_view is the preferred view for querying - it joins all dimension tables",
        "The areas table contains countries and regions with standard M49 codes",
        "The items table contains agricultural commodities like wheat, rice, corn, livestock, etc.",
        "The elements table contains measurement types: Production (tonnes), Yield (kg/ha), Area Harvested (ha), etc.",
        "Years range from approximately 1960s to 2020s depending on dataset and country",
        "Values are stored as numeric with units in a separate column",
        "Common units: tonnes, hectares (ha), kg/ha (yield), USD, percentage",
        "When asking about production, use element_name LIKE '%Production%'",
        "When asking about yields, use element_name LIKE '%Yield%'",
        "When asking about area, use element_name LIKE '%Area%'",
        "Country names in area_name may include full official names (e.g., 'United States of America')",
        "The flag column indicates data quality (A=official, E=estimate, F=FAO estimate, etc.)",
    ]

    for doc in documentation:
        vn.train(documentation=doc)

    print(f"✓ Trained on {len(documentation)} documentation items")

def train_common_queries(vn):
    """Train Vanna on common query patterns specific to agricultural data."""

    print("Training Vanna on common query patterns...")

    # Example questions and SQL pairs
    training_data = [
        {
            'question': 'What is the total wheat production in the United States in 2020?',
            'sql': """
                SELECT
                    area_name,
                    item_name,
                    element_name,
                    year,
                    SUM(value) as total_production,
                    unit
                FROM faostat_data_view
                WHERE area_name = 'United States of America'
                    AND item_name LIKE '%Wheat%'
                    AND year = 2020
                    AND element_name LIKE '%Production%'
                GROUP BY area_name, item_name, element_name, year, unit;
            """
        },
        {
            'question': 'Show me the top 10 countries by rice production in 2020',
            'sql': """
                SELECT
                    area_name,
                    SUM(value) as total_production,
                    unit
                FROM faostat_data_view
                WHERE item_name LIKE '%Rice%'
                    AND year = 2020
                    AND element_name LIKE '%Production%'
                GROUP BY area_name, unit
                ORDER BY total_production DESC
                LIMIT 10;
            """
        },
        {
            'question': 'What datasets are available?',
            'sql': """
                SELECT
                    dataset_code,
                    dataset_name,
                    description,
                    date_update
                FROM datasets
                ORDER BY dataset_name;
            """
        },
        {
            'question': 'Show crop production trends for India from 2010 to 2020',
            'sql': """
                SELECT
                    year,
                    item_name,
                    SUM(value) as production,
                    unit
                FROM faostat_data_view
                WHERE area_name = 'India'
                    AND year BETWEEN 2010 AND 2020
                    AND element_name LIKE '%Production%'
                GROUP BY year, item_name, unit
                ORDER BY year, production DESC;
            """
        },
        {
            'question': 'Compare corn yields between USA and China in 2019',
            'sql': """
                SELECT
                    area_name,
                    item_name,
                    element_name,
                    AVG(value) as avg_yield,
                    unit
                FROM faostat_data_view
                WHERE area_name IN ('United States of America', 'China')
                    AND item_name LIKE '%Maize%'
                    AND element_name LIKE '%Yield%'
                    AND year = 2019
                GROUP BY area_name, item_name, element_name, unit;
            """
        },
        {
            'question': 'What are the greenhouse gas emissions from agriculture in Brazil?',
            'sql': """
                SELECT
                    year,
                    element_name,
                    SUM(value) as emissions,
                    unit
                FROM faostat_data_view
                WHERE area_name = 'Brazil'
                    AND dataset_name LIKE '%Emission%'
                GROUP BY year, element_name, unit
                ORDER BY year DESC;
            """
        },
        {
            'question': 'List all items (crops/commodities) available',
            'sql': """
                SELECT DISTINCT
                    item_name,
                    COUNT(*) as record_count
                FROM faostat_data_view
                WHERE item_name IS NOT NULL
                GROUP BY item_name
                ORDER BY item_name;
            """
        },
        {
            'question': 'Show food price indices over time',
            'sql': """
                SELECT
                    year,
                    month_name,
                    item_name,
                    AVG(value) as avg_index,
                    unit
                FROM faostat_data_view
                WHERE dataset_name LIKE '%Price%'
                GROUP BY year, month_name, item_name, unit
                ORDER BY year, month_name;
            """
        }
    ]

    for item in training_data:
        vn.train(question=item['question'], sql=item['sql'])

    print(f"✓ Trained on {len(training_data)} example queries")

def main():
    """Main setup process."""
    print("="*60)
    print("Open Ag Library - Vanna AI Setup")
    print("="*60)
    print()

    # Ask user which LLM to use
    print("Which LLM would you like to use?")
    print("1. OpenAI (GPT-4)")
    print("2. Anthropic (Claude)")
    choice = input("Enter 1 or 2 (default: 1): ").strip() or "1"

    use_anthropic = (choice == "2")

    print()
    vn = setup_vanna(use_anthropic=use_anthropic)

    if vn is None:
        print("\n❌ Setup failed. Please configure API key in .env file")
        return

    print("\nTraining Vanna on database schema...")
    train_vanna_on_schema(vn)

    print("\nTraining Vanna on common queries...")
    train_common_queries(vn)

    print("\n" + "="*60)
    print("✓ Vanna setup completed!")
    print("="*60)
    print("\nYou can now use Vanna to query the database with natural language:")
    print("  >>> vn.ask('What is the total wheat production in China in 2020?')")
    print()

    # Interactive mode
    print("Entering interactive query mode (type 'exit' to quit):")
    print("-"*60)

    while True:
        print()
        question = input("Ask a question: ").strip()

        if question.lower() in ['exit', 'quit', 'q']:
            break

        if not question:
            continue

        try:
            # Generate SQL
            sql = vn.generate_sql(question)
            print(f"\n📝 Generated SQL:\n{sql}\n")

            # Ask if user wants to run it
            run = input("Run this query? (Y/n): ").strip().lower()
            if run in ['', 'y', 'yes']:
                df = vn.run_sql(sql)
                print("\n📊 Results:")
                print(df.to_string())

        except Exception as e:
            print(f"❌ Error: {e}")

    print("\nGoodbye!")

if __name__ == "__main__":
    main()
