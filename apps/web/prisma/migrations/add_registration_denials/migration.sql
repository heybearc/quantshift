CREATE TABLE IF NOT EXISTS "registration_denials" (
    "id" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "username" TEXT,
    "full_name" TEXT,
    "rejected_by_email" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "registration_denials_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX IF NOT EXISTS "registration_denials_email_key" ON "registration_denials"("email");
CREATE INDEX IF NOT EXISTS "registration_denials_username_idx" ON "registration_denials"("username");
