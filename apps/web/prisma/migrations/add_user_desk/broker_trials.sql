ALTER TABLE "personal_bots" ADD COLUMN IF NOT EXISTS "display_name" TEXT NOT NULL DEFAULT '';
ALTER TABLE "personal_bots" ADD COLUMN IF NOT EXISTS "adapter" TEXT NOT NULL DEFAULT 'needed';
ALTER TABLE "personal_bots" ADD COLUMN IF NOT EXISTS "paper_available" BOOLEAN NOT NULL DEFAULT true;

UPDATE "personal_bots"
SET "adapter" = 'ready',
    "display_name" = CASE "venue"
      WHEN 'alpaca' THEN 'Alpaca'
      WHEN 'coinbase' THEN 'Coinbase'
      WHEN 'kraken' THEN 'Kraken'
      ELSE "display_name"
    END,
    "trading_mode" = 'paper',
    "paper_available" = true
WHERE "venue" IN ('alpaca', 'coinbase', 'kraken');

CREATE TABLE IF NOT EXISTS "strategy_trials" (
    "id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "idea_id" TEXT NOT NULL,
    "accepted_risk" BOOLEAN NOT NULL DEFAULT false,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "strategy_trials_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX IF NOT EXISTS "strategy_trials_user_id_idea_id_key" ON "strategy_trials"("user_id", "idea_id");
CREATE INDEX IF NOT EXISTS "strategy_trials_user_id_idx" ON "strategy_trials"("user_id");
