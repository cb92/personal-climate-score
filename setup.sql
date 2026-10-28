-- ============================================================================
-- Personal Climate Score - Database Schema
-- Replaces file-based CSV/JSON cache mechanism in helper.py
-- Compatible with MySQL 8.0+ / MariaDB 10.5+ / Railway MySQL
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. CITIES TABLE
-- Stores normalized city metadata and API geocoding lookups
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cities (
    city_id INT AUTO_INCREMENT PRIMARY KEY,
    city_name VARCHAR(100) NOT NULL,
    state_name VARCHAR(100) NOT NULL,
    latitude DECIMAL(9, 6) NOT NULL,
    longitude DECIMAL(9, 6) NOT NULL,
    timezone VARCHAR(100) NOT NULL DEFAULT 'UTC',
    population INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uq_city_state UNIQUE (city_name, state_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------------------
-- 2. HISTORICAL DAILY WEATHER TABLE
-- Replaces cache_filename: {city}_{state}_historical_daily.csv
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS historical_daily_weather (
    historical_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    city_id INT NOT NULL,
    date DATE NOT NULL,
    temperature_2m_max__celsius FLOAT NULL,
    dew_point_2m_min__celsius FLOAT NULL,
    rain_sum__millimetre FLOAT NULL,
    snowfall_sum__centimetre FLOAT NULL,
    cloud_cover_mean__percentage FLOAT NULL,
    wind_speed_10m_mean__kilometres_per_hour FLOAT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_hist_city FOREIGN KEY (city_id) REFERENCES cities (city_id) ON DELETE CASCADE,
    CONSTRAINT uq_hist_city_date UNIQUE (city_id, date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------------------
-- 3. HISTORICAL HOURLY AQI (PM2.5) TABLE
-- Replaces cache_filename: {city}_{state}_historical_pm25.csv
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS historical_hourly_aqi (
    aqi_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    city_id INT NOT NULL,
    datetime DATETIME NOT NULL,
    date DATE NOT NULL,
    pm2_5__micrograms_per_cubic_metre FLOAT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_aqi_city FOREIGN KEY (city_id) REFERENCES cities (city_id) ON DELETE CASCADE,
    CONSTRAINT uq_aqi_city_datetime UNIQUE (city_id, datetime)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------------------
-- 4. CLIMATE FORECAST DAILY TABLE
-- Replaces cache_filename: {city}_{state}_{models}_combined_forecasted_data.csv
-- Supports multi-model forecasted data (EC_Earth3P_HR, MRI_AGCM3_2_S, NICAM16_8S)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS forecasted_daily_weather (
    forecast_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    city_id INT NOT NULL,
    model_name VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    year INT NOT NULL,
    temperature_2m_max__celsius FLOAT NULL,
    dew_point_2m_min__celsius FLOAT NULL,
    rain_sum__millimetre FLOAT NULL,
    snowfall_sum__centimetre FLOAT NULL,
    cloud_cover_mean__percentage FLOAT NULL,
    wind_speed_10m_mean__kilometres_per_hour FLOAT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_fore_city FOREIGN KEY (city_id) REFERENCES cities (city_id) ON DELETE CASCADE,
    CONSTRAINT uq_fore_city_model_date UNIQUE (city_id, model_name, date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------------------
-- 5. SCORE PARAMETER CONFIGURATIONS TABLE
-- Tracks unique Score() configurations keyed by MD5 hash of parameter dict
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS score_configurations (
    config_hash CHAR(32) PRIMARY KEY,
    parameters_json JSON NOT NULL,
    min_time TIME NOT NULL,
    max_time TIME NOT NULL,
    scaling_factor FLOAT NOT NULL,
    ideal_temp_min FLOAT NOT NULL,
    ideal_temp_max FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------------------
-- 6. COMPUTED HISTORICAL SCORES TABLE
-- Replaces cache_filename: {city}_{state}_historical_score_{hash}.csv
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS computed_historical_scores (
    score_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    city_id INT NOT NULL,
    config_hash CHAR(32) NOT NULL,
    date DATE NOT NULL,
    year INT NOT NULL,
    score FLOAT NOT NULL,
    reason VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_hscore_city FOREIGN KEY (city_id) REFERENCES cities (city_id) ON DELETE CASCADE,
    CONSTRAINT fk_hscore_config FOREIGN KEY (config_hash) REFERENCES score_configurations (config_hash) ON DELETE CASCADE,
    CONSTRAINT uq_hscore_city_hash_date UNIQUE (city_id, config_hash, date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------------------
-- 7. COMPUTED FORECASTED SCORES TABLE
-- Replaces cache_filename: {city}_{state}_{models}_combined_forecasted_score_{hash}.csv
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS computed_forecasted_scores (
    score_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    city_id INT NOT NULL,
    config_hash CHAR(32) NOT NULL,
    model_name VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    year INT NOT NULL,
    score FLOAT NOT NULL,
    reason VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_fscore_city FOREIGN KEY (city_id) REFERENCES cities (city_id) ON DELETE CASCADE,
    CONSTRAINT fk_fscore_config FOREIGN KEY (config_hash) REFERENCES score_configurations (config_hash) ON DELETE CASCADE,
    CONSTRAINT uq_fscore_city_hash_model_date UNIQUE (city_id, config_hash, model_name, date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------------------
-- INDEXES FOR PERFORMANCE OPTIMIZATION
-- ----------------------------------------------------------------------------
CREATE INDEX idx_hist_city_date ON historical_daily_weather (city_id, date);
CREATE INDEX idx_aqi_city_date ON historical_hourly_aqi (city_id, date);
CREATE INDEX idx_fore_city_model ON forecasted_daily_weather (city_id, model_name, date);
CREATE INDEX idx_hscore_lookup ON computed_historical_scores (city_id, config_hash);
CREATE INDEX idx_fscore_lookup ON computed_forecasted_scores (city_id, config_hash, model_name);