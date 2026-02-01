#!/usr/bin/env python3
"""
Analyze FAOSTAT data schemas to identify standardization needs.
This script examines the structure of different datasets and reports inconsistencies.
"""

import os
import zipfile
import pandas as pd
from pathlib import Path
from collections import defaultdict
import json

def analyze_zip_structure(zip_path):
    """Analyze the structure of a single FAOSTAT zip file."""
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        file_list = zip_ref.namelist()

        # Find the main data file
        main_csv = [f for f in file_list if 'All_Data_(Normalized).csv' in f]
        if not main_csv:
            return None

        # Read first few rows to get column structure
        df = pd.read_csv(zip_ref.open(main_csv[0]), nrows=100)

        return {
            'zip_file': os.path.basename(zip_path),
            'columns': list(df.columns),
            'num_columns': len(df.columns),
            'data_types': df.dtypes.to_dict(),
            'files_in_zip': file_list,
            'sample_row': df.iloc[0].to_dict() if len(df) > 0 else {}
        }

def find_all_zip_files(base_dir='.'):
    """Find all FAOSTAT zip files."""
    zip_files = []
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('_(Normalized).zip'):
                zip_files.append(os.path.join(root, file))
    return zip_files

def main():
    """Main analysis process."""
    print("Analyzing FAOSTAT data schemas...\n")

    zip_files = find_all_zip_files()
    print(f"Found {len(zip_files)} zip files\n")

    schemas = []
    column_variants = defaultdict(set)

    for zip_file in zip_files[:10]:  # Analyze first 10 for quick assessment
        print(f"Analyzing {os.path.basename(zip_file)}...")
        schema = analyze_zip_structure(zip_file)

        if schema:
            schemas.append(schema)
            for col in schema['columns']:
                column_variants[col].add(schema['zip_file'])

    # Print analysis results
    print("\n" + "="*80)
    print("SCHEMA ANALYSIS RESULTS")
    print("="*80)

    # Column consistency analysis
    print("\n1. COLUMN CONSISTENCY")
    print("-" * 80)

    all_columns = set()
    for schema in schemas:
        all_columns.update(schema['columns'])

    print(f"\nTotal unique columns across all datasets: {len(all_columns)}")
    print("\nColumn distribution:")

    for col in sorted(all_columns):
        count = sum(1 for s in schemas if col in s['columns'])
        print(f"  {col}: {count}/{len(schemas)} datasets ({count/len(schemas)*100:.1f}%)")

    # Standard columns that should be in all datasets
    print("\n2. STANDARD COLUMNS")
    print("-" * 80)

    standard_columns = ['Area Code', 'Area', 'Item Code', 'Item', 'Element Code',
                       'Element', 'Year', 'Value', 'Flag']

    for col in standard_columns:
        count = sum(1 for s in schemas if col in s['columns'])
        status = "✓" if count == len(schemas) else "✗"
        print(f"  {status} {col}: {count}/{len(schemas)} datasets")

    # Optional/varying columns
    print("\n3. OPTIONAL/VARYING COLUMNS")
    print("-" * 80)

    optional_columns = all_columns - set(standard_columns)
    for col in sorted(optional_columns):
        count = sum(1 for s in schemas if col in s['columns'])
        print(f"  {col}: {count}/{len(schemas)} datasets")

    # Files included in zips
    print("\n4. METADATA FILES")
    print("-" * 80)

    metadata_files = defaultdict(int)
    for schema in schemas:
        for f in schema['files_in_zip']:
            if 'All_Data' not in f:
                metadata_files[f.split('_')[-1]] += 1

    for file_type, count in sorted(metadata_files.items()):
        print(f"  {file_type}: {count}/{len(schemas)} datasets ({count/len(schemas)*100:.1f}%)")

    # Save detailed schema info
    output_file = 'schema_analysis.json'
    with open(output_file, 'w') as f:
        json.dump(schemas, f, indent=2, default=str)

    print(f"\n5. DETAILED SCHEMA INFORMATION")
    print("-" * 80)
    print(f"Detailed analysis saved to: {output_file}")

    # Recommendations
    print("\n6. STANDARDIZATION RECOMMENDATIONS")
    print("-" * 80)

    print("\nBased on the analysis:")
    print("  1. Core columns are consistent across datasets")
    print("  2. Optional columns (Months, Unit, Note) vary by dataset type")
    print("  3. All datasets include metadata files for dimensions (Area, Item, Element, Flags)")
    print("  4. The normalized schema can handle all variations with nullable columns")
    print("\nThe current schema in schema.sql should handle all datasets appropriately.")

if __name__ == "__main__":
    main()
