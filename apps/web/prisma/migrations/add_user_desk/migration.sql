CREATE TABLE IF NOT EXISTS "user_desks" (
    "user_id" TEXT NOT NULL,
    "mode" TEXT NOT NULL DEFAULT 'house',
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "user_desks_pkey" PRIMARY KEY ("user_id")
);

CREATE TABLE IF NOT EXISTS "personal_bots" (
    "id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "venue" TEXT NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'stopped',
    "trading_mode" TEXT NOT NULL DEFAULT 'paper',
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "personal_bots_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX IF NOT EXISTS "personal_bots_user_id_venue_key" ON "personal_bots"("user_id", "venue");
CREATE INDEX IF NOT EXISTS "personal_bots_user_id_idx" ON "personal_bots"("user_id");

CREATE TABLE IF NOT EXISTS "symbol_preferences" (
    "id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "symbol" TEXT NOT NULL,
    "intent" TEXT NOT NULL DEFAULT 'research',
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "symbol_preferences_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX IF NOT EXISTS "symbol_preferences_user_id_symbol_key" ON "symbol_preferences"("user_id", "symbol");
CREATE INDEX IF NOT EXISTS "symbol_preferences_user_id_idx" ON "symbol_preferences"("user_id");

CREATE TABLE IF NOT EXISTS "strategy_ideas" (
    "id" TEXT NOT NULL,
    "author_id" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "body" TEXT NOT NULL,
    "source" TEXT NOT NULL DEFAULT 'human',
    "status" TEXT NOT NULL DEFAULT 'suggestion',
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "strategy_ideas_pkey" PRIMARY KEY ("id")
);

CREATE INDEX IF NOT EXISTS "strategy_ideas_created_at_idx" ON "strategy_ideas"("created_at");

CREATE TABLE IF NOT EXISTS "strategy_comments" (
    "id" TEXT NOT NULL,
    "idea_id" TEXT NOT NULL,
    "author_id" TEXT NOT NULL,
    "body" TEXT NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "strategy_comments_pkey" PRIMARY KEY ("id")
);

CREATE INDEX IF NOT EXISTS "strategy_comments_idea_id_idx" ON "strategy_comments"("idea_id");
