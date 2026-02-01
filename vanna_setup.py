#!/usr/bin/env python3
"""
Vanna AI integration for Open Ag Library.
This script sets up Vanna to enable natural language querying of FAOSTAT data.
"""

import os
from vanna.remote import VannaDefault
from dotenv import load_dotenv
import psycopg2

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

def setup_vanna():
    """Initialize and configure Vanna AI."""
    api_key = os.getenv('VANNA_API_KEY')
    model_name = os.getenv('VANNA_MODEL', 'open_ag_library')

    if not api_key:
        print("Warning: VANNA_API_KEY not set in .env file")
        print("You can still train the model locally or set up the API key later")
        return None

    vn = VannaDefault(model=model_name, api_key=api_key)

    # Connect to PostgreSQL
    conn_string = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    vn.connect_to_postgres(
        host=DB_CONFIG['host'],
        dbname=DB_CONFIG['database'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        port=DB_CONFIG['port']
    )

    return vn

def train_vanna_on_schema(vn):
    """Train Vanna on the database schema and common queries."""

    # Train on DDL
    ddl_statements = [
        # Provide information about tables
        """
        CREATE TABLE datasets (
            dataset_code VARCHAR(10) PRIMARY KEY,
            dataset_name TEXT NOT NULL,
            topic TEXT,
            description TEXT
        );
        """,
        """
        CREATE TABLE areas (
            area_code INTEGER PRIMARY KEY,
            m49_code VARCHAR(10),
            area_name TEXT NOT NULL
        );
        """,
        """
        CREATE TABLE items (
            item_code INTEGER PRIMARY KEY,
            item_name TEXT NOT NULL,
            dataset_code VARCHAR(10)
        );
        """,
        """
        CREATE TABLE faostat_data (
            id BIGSERIAL PRIMARY KEY,
            dataset_code VARCHAR(10),
            area_code INTEGER,
            item_code INTEGER,
            element_code INTEGER,
            year INTEGER,
            value NUMERIC,
            unit VARCHAR(50)
        );
        """
    ]

    for ddl in ddl_statements:
        vn.train(ddl=ddl)

    # Train on documentation
    documentation = [
        "The faostat_data table contains agricultural statistics from FAO",
        "The areas table contains country and region information with M49 codes",
        "The items table contains agricultural commodities and products",
        "The elements table contains the type of measurement (production, yield, area harvested, etc.)",
        "Use the faostat_data_view for easier querying with dimension names already joined",
        "Years are stored as integers in the 'year' column",
        "Values are numeric and stored in the 'value' column with units in the 'unit' column"
    ]

    for doc in documentation:
        vn.train(documentation=doc)

def train_common_queries(vn):
    """Train Vanna on common query patterns."""

    # Example questions and SQL pairs
    training_data = [
        {
            'question': 'What is the total wheat production in the United States in 2020?',
            'sql': """
                SELECT SUM(value) as total_production, unit
                FROM faostat_data_view
                WHERE area_name = 'United States of America'
                AND item_name LIKE '%Wheat%'
                AND year = 2020
                AND element_name LIKE '%Production%'
                GROUP BY unit;
            """
        },
        {
            'question': 'Show me the top 10 countries by rice production in 2020',
            'sql': """
                SELECT area_name, SUM(value) as total_production, unit
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
                SELECT dataset_code, dataset_name, description
                FROM datasets
                ORDER BY dataset_name;
            """
        },
        {
            'question': 'Show crop production trends for India from 2010 to 2020',
            'sql': """
                SELECT year, item_name, SUM(value) as production
                FROM faostat_data_view
                WHERE area_name = 'India'
                AND year BETWEEN 2010 AND 2020
                AND element_name LIKE '%Production%'
                GROUP BY year, item_name
                ORDER BY year, production DESC;
            """
        }
    ]

    for item in training_data:
        vn.train(question=item['question'], sql=item['sql'])

    print(f"Trained on {len(training_data)} example queries")

def main():
    """Main setup process."""
    print("Setting up Vanna AI for Open Ag Library...\n")

    vn = setup_vanna()

    if vn is None:
        print("\nSkipping Vanna training (no API key configured)")
        print("To use Vanna, add VANNA_API_KEY to your .env file")
        return

    print("Training Vanna on database schema...")
    train_vanna_on_schema(vn)

    print("Training Vanna on common queries...")
    train_common_queries(vn)

    print("\nVanna setup completed!")
    print("\nYou can now use Vanna to query the database with natural language:")
    print("  vn.ask('What is the total wheat production in China in 2020?')")

    # Interactive mode
    print("\nEntering interactive query mode (type 'exit' to quit):")
    while True:
        question = input("\nAsk a question: ").strip()
        if question.lower() in ['exit', 'quit', 'q']:
            break

        if not question:
            continue

        try:
            sql = vn.generate_sql(question)
            print(f"\nGenerated SQL:\n{sql}\n")

            df = vn.run_sql(sql)
            print("Results:")
            print(df)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
