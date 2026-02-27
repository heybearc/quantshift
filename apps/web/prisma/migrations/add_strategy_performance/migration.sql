-- CreateTable
CREATE TABLE IF NOT EXISTS "strategy_performance" (
    "id" TEXT NOT NULL,
    "bot_name" TEXT NOT NULL,
    "strategy_name" TEXT NOT NULL,
    "total_trades" INTEGER NOT NULL DEFAULT 0,
    "winning_trades" INTEGER NOT NULL DEFAULT 0,
    "losing_trades" INTEGER NOT NULL DEFAULT 0,
    "win_rate" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "total_pnl" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "total_pnl_pct" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "avg_win" DOUBLE PRECISION,
    "avg_loss" DOUBLE PRECISION,
    "largest_win" DOUBLE PRECISION,
    "largest_loss" DOUBLE PRECISION,
    "sharpe_ratio" DOUBLE PRECISION,
    "profit_factor" DOUBLE PRECISION,
    "max_drawdown" DOUBLE PRECISION,
    "current_drawdown" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "peak_equity" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "last_trade_at" TIMESTAMP(3),
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "strategy_performance_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "strategy_performance_bot_name_strategy_name_key" ON "strategy_performance"("bot_name", "strategy_name");

-- CreateIndex
CREATE INDEX "strategy_performance_bot_name_idx" ON "strategy_performance"("bot_name");

-- CreateIndex
CREATE INDEX "strategy_performance_strategy_name_idx" ON "strategy_performance"("strategy_name");
