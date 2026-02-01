-- Open Ag Library PostgreSQL Schema
-- FAOSTAT Data Import Schema

-- Create database (run separately if needed)
-- CREATE DATABASE open_ag_library;

-- Datasets metadata table
CREATE TABLE IF NOT EXISTS datasets (
    dataset_code VARCHAR(10) PRIMARY KEY,
    dataset_name TEXT NOT NULL,
    topic TEXT,
    description TEXT,
    contact TEXT,
    email VARCHAR(255),
    date_update TIMESTAMP,
    file_size VARCHAR(20),
    file_rows INTEGER,
    file_location TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Generic dimension tables (shared across datasets)
CREATE TABLE IF NOT EXISTS areas (
    area_code INTEGER PRIMARY KEY,
    m49_code VARCHAR(10),
    area_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS items (
    item_code INTEGER PRIMARY KEY,
    cpc_code VARCHAR(20),
    item_name TEXT NOT NULL,
    dataset_code VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS elements (
    element_code INTEGER PRIMARY KEY,
    element_name TEXT NOT NULL,
    dataset_code VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS flags (
    flag_code VARCHAR(10) PRIMARY KEY,
    flag_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Main fact table for all FAOSTAT data
-- This will store data from all datasets in a normalized format
CREATE TABLE IF NOT EXISTS faostat_data (
    id BIGSERIAL PRIMARY KEY,
    dataset_code VARCHAR(10) NOT NULL,
    area_code INTEGER,
    item_code INTEGER,
    element_code INTEGER,
    year INTEGER NOT NULL,
    year_code INTEGER,
    month_code INTEGER,
    month_name VARCHAR(20),
    value NUMERIC,
    unit VARCHAR(50),
    flag VARCHAR(10),
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dataset_code) REFERENCES datasets(dataset_code),
    FOREIGN KEY (area_code) REFERENCES areas(area_code),
    FOREIGN KEY (item_code) REFERENCES items(item_code),
    FOREIGN KEY (element_code) REFERENCES elements(element_code)
);

-- Create indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_faostat_data_dataset ON faostat_data(dataset_code);
CREATE INDEX IF NOT EXISTS idx_faostat_data_area ON faostat_data(area_code);
CREATE INDEX IF NOT EXISTS idx_faostat_data_item ON faostat_data(item_code);
CREATE INDEX IF NOT EXISTS idx_faostat_data_year ON faostat_data(year);
CREATE INDEX IF NOT EXISTS idx_faostat_data_composite ON faostat_data(dataset_code, area_code, item_code, year);

-- Create a view for easy querying with dimension names
CREATE OR REPLACE VIEW faostat_data_view AS
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
    f.flag_description,
    fd.note
FROM faostat_data fd
LEFT JOIN datasets d ON fd.dataset_code = d.dataset_code
LEFT JOIN areas a ON fd.area_code = a.area_code
LEFT JOIN items i ON fd.item_code = i.item_code
LEFT JOIN elements e ON fd.element_code = e.element_code
LEFT JOIN flags f ON fd.flag = f.flag_code;

-- Add comments for documentation
COMMENT ON TABLE datasets IS 'Metadata about FAOSTAT datasets';
COMMENT ON TABLE areas IS 'Geographic areas/countries dimension table';
COMMENT ON TABLE items IS 'Agricultural items/commodities dimension table';
COMMENT ON TABLE elements IS 'Statistical elements (e.g., production, yield) dimension table';
COMMENT ON TABLE faostat_data IS 'Main fact table containing all FAOSTAT measurements';
COMMENT ON VIEW faostat_data_view IS 'Denormalized view joining all dimension tables for easy querying';
