CREATE TABLE IF NOT EXISTS "broker_connections" (
    "id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "venue" TEXT NOT NULL,
    "environment" TEXT NOT NULL,
    "label" TEXT NOT NULL DEFAULT '',
    "status" TEXT NOT NULL DEFAULT 'connected',
    "key_hint" TEXT NOT NULL DEFAULT '',
    "ciphertext" TEXT NOT NULL,
    "last_checked_at" TIMESTAMP(3),
    "last_error" TEXT,
    "last_snapshot" JSONB,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "broker_connections_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX IF NOT EXISTS "broker_connections_user_id_venue_environment_key"
    ON "broker_connections"("user_id", "venue", "environment");
CREATE INDEX IF NOT EXISTS "broker_connections_user_id_idx" ON "broker_connections"("user_id");

DO $$ BEGIN
    ALTER TABLE "broker_connections"
        ADD CONSTRAINT "broker_connections_user_id_fkey"
        FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS "broker_orders" (
    "id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "connection_id" TEXT NOT NULL,
    "venue" TEXT NOT NULL,
    "environment" TEXT NOT NULL,
    "symbol" TEXT NOT NULL,
    "side" TEXT NOT NULL,
    "quantity" TEXT NOT NULL,
    "status" TEXT NOT NULL,
    "broker_order_id" TEXT NOT NULL DEFAULT '',
    "message" TEXT NOT NULL DEFAULT '',
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "broker_orders_pkey" PRIMARY KEY ("id")
);

CREATE INDEX IF NOT EXISTS "broker_orders_user_id_idx" ON "broker_orders"("user_id");
CREATE INDEX IF NOT EXISTS "broker_orders_connection_id_idx" ON "broker_orders"("connection_id");

DO $$ BEGIN
    ALTER TABLE "broker_orders"
        ADD CONSTRAINT "broker_orders_user_id_fkey"
        FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE "broker_orders"
        ADD CONSTRAINT "broker_orders_connection_id_fkey"
        FOREIGN KEY ("connection_id") REFERENCES "broker_connections"("id") ON DELETE CASCADE ON UPDATE CASCADE;
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS "broker_requests" (
    "id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "website" TEXT NOT NULL DEFAULT '',
    "docs_url" TEXT NOT NULL DEFAULT '',
    "notes" TEXT NOT NULL DEFAULT '',
    "status" TEXT NOT NULL DEFAULT 'submitted',
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "broker_requests_pkey" PRIMARY KEY ("id")
);

CREATE INDEX IF NOT EXISTS "broker_requests_user_id_idx" ON "broker_requests"("user_id");
CREATE INDEX IF NOT EXISTS "broker_requests_status_idx" ON "broker_requests"("status");

DO $$ BEGIN
    ALTER TABLE "broker_requests"
        ADD CONSTRAINT "broker_requests_user_id_fkey"
        FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;
