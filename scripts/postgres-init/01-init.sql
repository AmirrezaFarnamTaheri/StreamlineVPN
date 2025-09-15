-- PostgreSQL Initialization Script for StreamlineVPN
-- ===================================================

-- Create database if it doesn't exist
-- (This is handled by POSTGRES_DB environment variable)

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS streamline;

-- Set default schema
SET search_path TO streamline, public;

-- Create tables
CREATE TABLE IF NOT EXISTS configurations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    protocol VARCHAR(20) NOT NULL,
    server VARCHAR(255) NOT NULL,
    port INTEGER NOT NULL,
    uuid VARCHAR(36),
    password TEXT,
    alter_id INTEGER,
    security VARCHAR(20),
    network VARCHAR(20),
    path VARCHAR(255),
    host VARCHAR(255),
    sni VARCHAR(255),
    service_name VARCHAR(255),
    method VARCHAR(50),
    plugin VARCHAR(50),
    plugin_opts TEXT,
    alpn TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source_url TEXT,
    source_tier VARCHAR(20),
    is_active BOOLEAN DEFAULT true,
    quality_score DECIMAL(3,2) DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url TEXT UNIQUE NOT NULL,
    name VARCHAR(255),
    tier VARCHAR(20) NOT NULL,
    weight DECIMAL(3,2) DEFAULT 1.0,
    protocols TEXT[],
    update_frequency VARCHAR(20),
    reliability DECIMAL(3,2) DEFAULT 0.0,
    last_checked TIMESTAMP WITH TIME ZONE,
    last_success TIMESTAMP WITH TIME ZONE,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    total_items INTEGER DEFAULT 0,
    processed_items INTEGER DEFAULT 0,
    error_message TEXT,
    result_data JSONB,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS cache_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    cache_value TEXT NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS statistics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,4) NOT NULL,
    metric_unit VARCHAR(20),
    tags JSONB,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_configurations_protocol ON configurations(protocol);
CREATE INDEX IF NOT EXISTS idx_configurations_server ON configurations(server);
CREATE INDEX IF NOT EXISTS idx_configurations_port ON configurations(port);
CREATE INDEX IF NOT EXISTS idx_configurations_active ON configurations(is_active);
CREATE INDEX IF NOT EXISTS idx_configurations_quality ON configurations(quality_score DESC);
CREATE INDEX IF NOT EXISTS idx_configurations_created ON configurations(created_at);

CREATE INDEX IF NOT EXISTS idx_sources_url ON sources(url);
CREATE INDEX IF NOT EXISTS idx_sources_tier ON sources(tier);
CREATE INDEX IF NOT EXISTS idx_sources_active ON sources(is_active);
CREATE INDEX IF NOT EXISTS idx_sources_reliability ON sources(reliability DESC);

CREATE INDEX IF NOT EXISTS idx_jobs_type ON jobs(job_type);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_created ON jobs(created_at);

CREATE INDEX IF NOT EXISTS idx_cache_key ON cache_entries(cache_key);
CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache_entries(expires_at);

CREATE INDEX IF NOT EXISTS idx_statistics_name ON statistics(metric_name);
CREATE INDEX IF NOT EXISTS idx_statistics_recorded ON statistics(recorded_at);

-- Create functions
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_configurations_updated_at 
    BEFORE UPDATE ON configurations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sources_updated_at 
    BEFORE UPDATE ON sources 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_jobs_updated_at 
    BEFORE UPDATE ON jobs 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cache_entries_updated_at 
    BEFORE UPDATE ON cache_entries 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create views for common queries
CREATE OR REPLACE VIEW active_configurations AS
SELECT 
    c.*,
    s.name as source_name,
    s.tier as source_tier,
    s.reliability as source_reliability
FROM configurations c
LEFT JOIN sources s ON c.source_url = s.url
WHERE c.is_active = true
ORDER BY s.reliability DESC, c.quality_score DESC;

CREATE OR REPLACE VIEW source_statistics AS
SELECT 
    s.id,
    s.name,
    s.url,
    s.tier,
    s.reliability,
    s.success_count,
    s.failure_count,
    CASE 
        WHEN s.success_count + s.failure_count = 0 THEN 0
        ELSE ROUND(s.success_count::DECIMAL / (s.success_count + s.failure_count) * 100, 2)
    END as success_rate,
    s.last_checked,
    s.last_success,
    s.is_active
FROM sources s
ORDER BY s.reliability DESC;

-- Insert default data
INSERT INTO sources (url, name, tier, weight, protocols, update_frequency, reliability, is_active) VALUES
('https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt', 'V2RayAggregator Main', 'premium', 1.0, ARRAY['vmess', 'vless', 'trojan', 'shadowsocks'], 'hourly', 0.95, true),
('https://raw.githubusercontent.com/AzadNetCH/Clash/main/AzadNet.yml', 'AzadNet Clash', 'premium', 1.0, ARRAY['vmess', 'vless', 'trojan'], 'daily', 0.92, true),
('https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/vmess', 'Telegram Configs VMess', 'premium', 1.0, ARRAY['vmess'], '6-hourly', 0.90, true)
ON CONFLICT (url) DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA streamline TO streamline;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA streamline TO streamline;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA streamline TO streamline;
GRANT USAGE ON SCHEMA streamline TO streamline;
