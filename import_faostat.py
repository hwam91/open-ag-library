#!/usr/bin/env python3
"""
Import FAOSTAT data into PostgreSQL database.
This script processes all zipped CSV files and loads them into the database.
"""

import os
import json
import zipfile
import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
from sqlalchemy import create_engine
from dotenv import load_dotenv
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Database connection parameters
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'open_ag_library'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', '')
}

def get_db_connection():
    """Create and return a database connection."""
    return psycopg2.connect(**DB_CONFIG)

def get_sqlalchemy_engine():
    """Create and return a SQLAlchemy engine."""
    conn_string = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    return create_engine(conn_string)

def load_datasets_metadata(json_path='datasets_E.json'):
    """Load dataset metadata from JSON file."""
    logger.info(f"Loading datasets metadata from {json_path}")
    with open(json_path, 'r') as f:
        data = json.load(f)

    datasets = data['Datasets']['Dataset']
    logger.info(f"Found {len(datasets)} datasets")
    return datasets

def insert_datasets_metadata(datasets):
    """Insert dataset metadata into the database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    insert_query = """
    INSERT INTO datasets (dataset_code, dataset_name, topic, description, contact, email, date_update, file_size, file_rows, file_location)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (dataset_code) DO UPDATE SET
        dataset_name = EXCLUDED.dataset_name,
        topic = EXCLUDED.topic,
        description = EXCLUDED.description,
        contact = EXCLUDED.contact,
        email = EXCLUDED.email,
        date_update = EXCLUDED.date_update,
        file_size = EXCLUDED.file_size,
        file_rows = EXCLUDED.file_rows,
        file_location = EXCLUDED.file_location;
    """

    for ds in datasets:
        try:
            cursor.execute(insert_query, (
                ds['DatasetCode'],
                ds['DatasetName'],
                ds.get('Topic'),
                ds.get('DatasetDescription'),
                ds.get('Contact'),
                ds.get('Email'),
                ds.get('DateUpdate'),
                ds.get('FileSize'),
                ds.get('FileRows'),
                ds.get('FileLocation')
            ))
        except Exception as e:
            logger.error(f"Error inserting dataset {ds['DatasetCode']}: {e}")

    conn.commit()
    cursor.close()
    conn.close()
    logger.info(f"Inserted {len(datasets)} dataset metadata records")

def process_zip_file(zip_path, dataset_code=None):
    """Process a single FAOSTAT zip file and load data into database."""
    logger.info(f"Processing {zip_path}")

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        file_list = zip_ref.namelist()

        # Find the main data file and metadata files
        main_csv = [f for f in file_list if 'All_Data_(Normalized).csv' in f][0]
        area_codes = [f for f in file_list if 'AreaCodes.csv' in f]
        item_codes = [f for f in file_list if 'ItemCodes.csv' in f]
        element_codes = [f for f in file_list if 'Elements.csv' in f]
        flags_file = [f for f in file_list if 'Flags.csv' in f]

        # dataset_code should be provided by caller
        if not dataset_code:
            logger.error("Dataset code not provided - this is a bug!")
            raise ValueError("Dataset code must be provided")

        conn = get_db_connection()
        cursor = conn.cursor()
        engine = get_sqlalchemy_engine()

        # Load dimension tables (with ON CONFLICT DO NOTHING for duplicates)
        if area_codes:
            logger.info("Loading area codes...")
            try:
                df_areas = pd.read_csv(zip_ref.open(area_codes[0]))
                df_areas.columns = ['area_code', 'm49_code', 'area_name']
                # Insert with ON CONFLICT handling
                for _, row in df_areas.iterrows():
                    cursor.execute("""
                        INSERT INTO areas (area_code, m49_code, area_name)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (area_code) DO NOTHING
                    """, (row['area_code'], row['m49_code'], row['area_name']))
                conn.commit()
                logger.info(f"Processed {len(df_areas)} area codes")
            except Exception as e:
                logger.warning(f"Error loading areas: {e}")
                conn.rollback()

        if item_codes:
            logger.info("Loading item codes...")
            try:
                df_items = pd.read_csv(zip_ref.open(item_codes[0]))
                df_items['dataset_code'] = dataset_code
                df_items.columns = ['item_code', 'cpc_code', 'item_name', 'dataset_code']
                # Insert with ON CONFLICT handling
                for _, row in df_items.iterrows():
                    cursor.execute("""
                        INSERT INTO items (item_code, cpc_code, item_name, dataset_code)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (item_code) DO NOTHING
                    """, (row['item_code'], row['cpc_code'], row['item_name'], row['dataset_code']))
                conn.commit()
                logger.info(f"Processed {len(df_items)} item codes")
            except Exception as e:
                logger.warning(f"Error loading items: {e}")
                conn.rollback()

        if element_codes:
            logger.info("Loading element codes...")
            try:
                df_elements = pd.read_csv(zip_ref.open(element_codes[0]))
                df_elements['dataset_code'] = dataset_code
                df_elements.columns = ['element_code', 'element_name', 'dataset_code']
                # Insert with ON CONFLICT handling
                for _, row in df_elements.iterrows():
                    cursor.execute("""
                        INSERT INTO elements (element_code, element_name, dataset_code)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (element_code) DO NOTHING
                    """, (row['element_code'], row['element_name'], row['dataset_code']))
                conn.commit()
                logger.info(f"Processed {len(df_elements)} element codes")
            except Exception as e:
                logger.warning(f"Error loading elements: {e}")
                conn.rollback()

        if flags_file:
            logger.info("Loading flags...")
            try:
                df_flags = pd.read_csv(zip_ref.open(flags_file[0]))
                df_flags.columns = ['flag_code', 'flag_description']
                # Insert with ON CONFLICT handling
                for _, row in df_flags.iterrows():
                    cursor.execute("""
                        INSERT INTO flags (flag_code, flag_description)
                        VALUES (%s, %s)
                        ON CONFLICT (flag_code) DO NOTHING
                    """, (row['flag_code'], row['flag_description']))
                conn.commit()
                logger.info(f"Processed {len(df_flags)} flags")
            except Exception as e:
                logger.warning(f"Error loading flags: {e}")
                conn.rollback()

        # Load main data in chunks to handle large files
        logger.info(f"Loading main data from {main_csv}...")
        chunk_size = 10000
        chunks_processed = 0

        for chunk in pd.read_csv(zip_ref.open(main_csv), chunksize=chunk_size):
            # Normalize column names and prepare data
            chunk['dataset_code'] = dataset_code

            # Map columns to database schema
            chunk_clean = pd.DataFrame()
            chunk_clean['dataset_code'] = chunk['dataset_code']
            chunk_clean['area_code'] = chunk['Area Code']
            chunk_clean['item_code'] = chunk['Item Code']
            chunk_clean['element_code'] = chunk['Element Code']
            chunk_clean['year'] = chunk['Year']
            chunk_clean['year_code'] = chunk.get('Year Code', chunk['Year'])
            chunk_clean['month_code'] = chunk.get('Months Code', None)
            chunk_clean['month_name'] = chunk.get('Months', None)
            chunk_clean['value'] = pd.to_numeric(chunk['Value'], errors='coerce')
            chunk_clean['unit'] = chunk.get('Unit', '')
            chunk_clean['flag'] = chunk.get('Flag', '')
            chunk_clean['note'] = chunk.get('Note', '')

            # Insert data
            chunk_clean.to_sql('faostat_data', engine, if_exists='append', index=False, method='multi')
            chunks_processed += 1

            if chunks_processed % 10 == 0:
                logger.info(f"Processed {chunks_processed * chunk_size} rows...")

        cursor.close()
        conn.close()
        logger.info(f"Completed processing {zip_path}")

def find_all_zip_files(base_dir='.'):
    """Find all FAOSTAT zip files in the directory structure."""
    zip_files = []
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('_(Normalized).zip'):
                zip_files.append(os.path.join(root, file))
    return zip_files

def get_dataset_code_from_filename(zip_filename, datasets_metadata):
    """Map a zip filename to its dataset code using metadata."""
    # Extract base filename without path
    base_name = os.path.basename(zip_filename)
    base_name = base_name.replace('_E_All_Data_(Normalized).zip', '')

    # Try to find matching dataset in metadata
    for ds in datasets_metadata:
        file_location = ds.get('FileLocation', '')
        if base_name in file_location or file_location.endswith(f'{base_name}.zip'):
            return ds['DatasetCode']

    # Fallback: use first part of filename (won't work well but better than nothing)
    logger.warning(f"Could not find dataset code for {zip_filename}, using filename prefix")
    return base_name[:10]

def main():
    """Main import process."""
    logger.info("Starting FAOSTAT data import process")

    # Load and insert dataset metadata
    try:
        datasets = load_datasets_metadata()
        insert_datasets_metadata(datasets)
    except Exception as e:
        logger.error(f"Error loading dataset metadata: {e}")
        return

    # Find all zip files
    zip_files = find_all_zip_files()
    logger.info(f"Found {len(zip_files)} zip files to process")

    # Process each zip file
    for i, zip_file in enumerate(zip_files, 1):
        logger.info(f"Processing file {i}/{len(zip_files)}: {zip_file}")
        try:
            # Get proper dataset code from metadata
            dataset_code = get_dataset_code_from_filename(zip_file, datasets)
            logger.info(f"Dataset code: {dataset_code}")
            process_zip_file(zip_file, dataset_code=dataset_code)
        except Exception as e:
            logger.error(f"Error processing {zip_file}: {e}")
            continue

    logger.info("FAOSTAT data import completed!")

if __name__ == "__main__":
    main()
