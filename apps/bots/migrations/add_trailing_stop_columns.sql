-- Migration: Add Trailing Stop-Loss Columns to positions table
-- Date: 2026-03-06
-- Description: Add columns to track high water mark, trailing stop state, and order IDs

-- Add high_water_mark column (highest price reached since entry)
ALTER TABLE positions 
ADD COLUMN IF NOT EXISTS high_water_mark DOUBLE PRECISION;

-- Add trailing_stop_active flag
ALTER TABLE positions 
ADD COLUMN IF NOT EXISTS trailing_stop_active BOOLEAN DEFAULT FALSE;

-- Add current_stop_loss (adjustable stop price)
ALTER TABLE positions 
ADD COLUMN IF NOT EXISTS current_stop_loss DOUBLE PRECISION;

-- Add stop_order_id (broker order ID for stop-loss)
ALTER TABLE positions 
ADD COLUMN IF NOT EXISTS stop_order_id TEXT;

-- Add take_profit_order_id (broker order ID for take-profit)
ALTER TABLE positions 
ADD COLUMN IF NOT EXISTS take_profit_order_id TEXT;

-- Add last_stop_update timestamp
ALTER TABLE positions 
ADD COLUMN IF NOT EXISTS last_stop_update TIMESTAMP;

-- Initialize high_water_mark for existing positions (set to current_price)
UPDATE positions 
SET high_water_mark = current_price 
WHERE high_water_mark IS NULL;

-- Initialize current_stop_loss for existing positions (use stop_loss if available)
UPDATE positions 
SET current_stop_loss = stop_loss 
WHERE current_stop_loss IS NULL AND stop_loss IS NOT NULL;

-- Create index on trailing_stop_active for faster queries
CREATE INDEX IF NOT EXISTS idx_positions_trailing_stop_active 
ON positions(trailing_stop_active);

-- Create index on stop_order_id for order lookup
CREATE INDEX IF NOT EXISTS idx_positions_stop_order_id 
ON positions(stop_order_id);

-- Verify migration
SELECT 
    column_name, 
    data_type, 
    is_nullable 
FROM information_schema.columns 
WHERE table_name = 'positions' 
    AND column_name IN (
        'high_water_mark', 
        'trailing_stop_active', 
        'current_stop_loss', 
        'stop_order_id',
        'take_profit_order_id',
        'last_stop_update'
    )
ORDER BY column_name;
