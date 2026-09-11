-- Enable pgvector extension for vector similarity search (RAG)
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Items Table
CREATE TABLE IF NOT EXISTS items (
    id VARCHAR(50) PRIMARY KEY,
    category VARCHAR(100) NOT NULL,
    brand VARCHAR(100),
    color VARCHAR(50),
    location VARCHAR(200) NOT NULL,
    found_time VARCHAR(50),
    description TEXT NOT NULL,
    verification_feature TEXT NOT NULL, -- Protected field, never returned to frontend
    embedding vector(768),              -- Vector embedding for RAG/pgvector similarity
    status VARCHAR(50) DEFAULT 'unclaimed', -- 'unclaimed', 'verified', 'claimed'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for vector similarity search using HNSW (Cosine Distance)
CREATE INDEX IF NOT EXISTS items_embedding_hnsw_idx 
ON items USING hnsw (embedding vector_cosine_ops);

-- Index for relational search fields
CREATE INDEX IF NOT EXISTS items_category_idx ON items(category);
CREATE INDEX IF NOT EXISTS items_brand_idx ON items(brand);
CREATE INDEX IF NOT EXISTS items_location_idx ON items(location);

-- Conversations Table (State Persistence)
CREATE TABLE IF NOT EXISTS conversations (
    id VARCHAR(100) PRIMARY KEY,
    intent VARCHAR(50),
    category VARCHAR(100),
    brand VARCHAR(100),
    color VARCHAR(50),
    location VARCHAR(200),
    time VARCHAR(50),
    selected_match_id VARCHAR(50) REFERENCES items(id) ON DELETE SET NULL,
    confidence_score FLOAT,
    confidence_level VARCHAR(20), -- 'HIGH', 'MEDIUM', 'LOW'
    verification_status VARCHAR(50), -- 'PENDING', 'VERIFIED', 'FAILED'
    stage VARCHAR(50) NOT NULL DEFAULT 'understanding',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Messages Table (Chat History)
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id VARCHAR(100) NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender VARCHAR(20) NOT NULL, -- 'user', 'ai'
    text TEXT NOT NULL,
    stage VARCHAR(50),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Pickups Table
CREATE TABLE IF NOT EXISTS pickups (
    id VARCHAR(50) PRIMARY KEY,
    conversation_id VARCHAR(100) NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    item_id VARCHAR(50) NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    location VARCHAR(200) NOT NULL,
    status VARCHAR(50) DEFAULT 'Ready for pickup',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
