# Database initialization script
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(100),
    github_username VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create repositories table
CREATE TABLE IF NOT EXISTS repositories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) UNIQUE NOT NULL,
    github_id INTEGER UNIQUE NOT NULL,
    clone_url VARCHAR(500) NOT NULL,
    webhook_secret VARCHAR(255),
    default_branch VARCHAR(100) DEFAULT 'main',
    language VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    auto_review_enabled BOOLEAN DEFAULT TRUE,
    review_on_pr BOOLEAN DEFAULT TRUE,
    review_on_push BOOLEAN DEFAULT FALSE,
    owner_id UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create code_reviews table
CREATE TABLE IF NOT EXISTS code_reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    repository_id UUID NOT NULL REFERENCES repositories(id),
    commit_hash VARCHAR(40) NOT NULL,
    pr_number INTEGER,
    branch VARCHAR(255),
    status VARCHAR(20) DEFAULT 'pending',
    trigger_event VARCHAR(50),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds INTEGER,
    total_files INTEGER DEFAULT 0,
    analyzed_files INTEGER DEFAULT 0,
    total_findings INTEGER DEFAULT 0,
    critical_findings INTEGER DEFAULT 0,
    high_findings INTEGER DEFAULT 0,
    medium_findings INTEGER DEFAULT 0,
    low_findings INTEGER DEFAULT 0,
    overall_score FLOAT,
    recommendation TEXT,
    created_by_id UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_code_reviews_repository_id ON code_reviews(repository_id);
CREATE INDEX IF NOT EXISTS idx_code_reviews_status ON code_reviews(status);
CREATE INDEX IF NOT EXISTS idx_code_reviews_created_at ON code_reviews(created_at);
CREATE INDEX IF NOT EXISTS idx_code_reviews_commit_hash ON code_reviews(commit_hash);

-- Insert default admin user
INSERT INTO users (username, email, full_name, is_admin) 
VALUES ('admin', 'admin@aicodereview.com', 'Administrator', TRUE)
ON CONFLICT (username) DO NOTHING;
