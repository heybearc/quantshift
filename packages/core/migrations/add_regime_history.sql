-- Add regime_history table for tracking market regime changes
CREATE TABLE IF NOT EXISTS regime_history (
    id SERIAL PRIMARY KEY,
    bot_name VARCHAR(100) NOT NULL,
    regime VARCHAR(50) NOT NULL,
    method VARCHAR(20) NOT NULL,
    confidence FLOAT NOT NULL,
    risk_multiplier FLOAT NOT NULL,
    allocation JSONB NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Indexes for efficient queries
    INDEX idx_regime_history_bot_timestamp (bot_name, timestamp DESC),
    INDEX idx_regime_history_regime (regime),
    INDEX idx_regime_history_timestamp (timestamp DESC)
);

-- Add comment
COMMENT ON TABLE regime_history IS 'Historical record of market regime changes detected by ML classifier';
