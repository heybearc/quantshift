import { prisma } from "@/lib/prisma";
import { catalogBroker, publicCatalog, type BrokerEnvironment } from "./broker-catalog";
import { BrokerError, keyHint, parseCredentials, parseOrder, readAccount, sendOrder, type AccountSnapshot, type BrokerCredentials } from "./broker-gateway";
import { openCredentials, redactSecrets, sealCredentials } from "./credential-vault";
import { cleanText, describeBot, venueSlug } from "./user-desk";

let tablesReady: Promise<void> | null = null;

export function ensureBrokerTables(): Promise<void> {
  if (!tablesReady) {
    tablesReady = createBrokerTables().catch((error) => {
      tablesReady = null;
      throw error;
    });
  }
  return tablesReady;
}

async function createBrokerTables() {
  await prisma.$executeRawUnsafe(`
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
    )
  `);
  await prisma.$executeRawUnsafe(`CREATE UNIQUE INDEX IF NOT EXISTS "broker_connections_user_id_venue_environment_key" ON "broker_connections"("user_id", "venue", "environment")`);
  await prisma.$executeRawUnsafe(`CREATE INDEX IF NOT EXISTS "broker_connections_user_id_idx" ON "broker_connections"("user_id")`);
  await prisma.$executeRawUnsafe(`
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
    )
  `);
  await prisma.$executeRawUnsafe(`CREATE INDEX IF NOT EXISTS "broker_orders_user_id_idx" ON "broker_orders"("user_id")`);
  await prisma.$executeRawUnsafe(`CREATE INDEX IF NOT EXISTS "broker_orders_connection_id_idx" ON "broker_orders"("connection_id")`);
  await prisma.$executeRawUnsafe(`
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
    )
  `);
  await prisma.$executeRawUnsafe(`CREATE INDEX IF NOT EXISTS "broker_requests_user_id_idx" ON "broker_requests"("user_id")`);
  await prisma.$executeRawUnsafe(`CREATE INDEX IF NOT EXISTS "broker_requests_status_idx" ON "broker_requests"("status")`);
}

export function publicConnection(row: {
  id: string;
  venue: string;
  environment: string;
  label: string;
  status: string;
  keyHint: string;
  lastCheckedAt: Date | null;
  lastError: string | null;
  lastSnapshot: unknown;
}) {
  return {
    id: row.id,
    venue: row.venue,
    environment: row.environment,
    label: row.label,
    status: row.status,
    keyHint: row.keyHint,
    lastCheckedAt: row.lastCheckedAt,
    lastError: row.lastError,
    snapshot: row.lastSnapshot,
  };
}

function optionalUrl(value: unknown): string {
  const text = cleanText(value, 300);
  if (!text) return "";
  let parsed: URL;
  try {
    parsed = new URL(text);
  } catch {
    throw new BrokerError("Enter a full http or https address.");
  }
  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    throw new BrokerError("Enter a full http or https address.");
  }
  return parsed.toString();
}

export async function connectBroker(userId: string, body: Record<string, unknown>) {
  await ensureBrokerTables();
  const venue = typeof body.venue === "string" ? body.venue : "";
  const broker = catalogBroker(venue);
  if (!broker || broker.adapter !== "ready") throw new BrokerError("Choose a broker that can accept a connection.");
  const environment = body.environment === "live" ? "live" : body.environment === "paper" ? "paper" : "";
  if (!environment || !broker.environments.includes(environment)) {
    throw new BrokerError("Choose paper or live for this broker.");
  }
  const credentials = parseCredentials(body.credentials);
  let snapshot: AccountSnapshot;
  try {
    snapshot = await readAccount(venue, environment, credentials);
  } catch (error) {
    const message = error instanceof BrokerError ? error.message : "The broker rejected the key.";
    throw new BrokerError(redactSecrets(message, [credentials.apiKey, credentials.apiSecret]), 400);
  }
  const saved = await prisma.brokerConnection.upsert({
    where: { userId_venue_environment: { userId, venue, environment } },
    create: {
      userId,
      venue,
      environment,
      label: broker.name,
      status: "connected",
      keyHint: keyHint(credentials.apiKey),
      ciphertext: sealCredentials(credentials),
      lastCheckedAt: new Date(),
      lastError: null,
      lastSnapshot: snapshot,
    },
    update: {
      status: "connected",
      keyHint: keyHint(credentials.apiKey),
      ciphertext: sealCredentials(credentials),
      lastCheckedAt: new Date(),
      lastError: null,
      lastSnapshot: snapshot,
    },
  });
  const bot = describeBot(venue);
  await prisma.userDesk.upsert({
    where: { userId },
    create: { userId, mode: "personal" },
    update: { mode: "personal" },
  });
  await prisma.personalBot.upsert({
    where: { userId_venue: { userId, venue } },
    create: { userId, ...bot, status: "connected", tradingMode: environment },
    update: { status: "connected", tradingMode: environment, adapter: bot.adapter, displayName: bot.displayName },
  });
  return publicConnection(saved);
}

async function ownedConnection(userId: string, id: string) {
  await ensureBrokerTables();
  const row = await prisma.brokerConnection.findFirst({ where: { id, userId } });
  if (!row) throw new BrokerError("That connection is not on your desk.", 404);
  return row;
}

function storedCredentials(ciphertext: string): BrokerCredentials {
  const opened = openCredentials(ciphertext);
  return parseCredentials(opened);
}

export async function refreshConnection(userId: string, id: string) {
  const row = await ownedConnection(userId, id);
  const credentials = storedCredentials(row.ciphertext);
  try {
    const snapshot = await readAccount(row.venue, row.environment as BrokerEnvironment, credentials);
    const saved = await prisma.brokerConnection.update({
      where: { id: row.id },
      data: { status: "connected", lastCheckedAt: new Date(), lastError: null, lastSnapshot: snapshot },
    });
    return publicConnection(saved);
  } catch (error) {
    const message = redactSecrets(error instanceof Error ? error.message : "The broker rejected the key.", [credentials.apiKey, credentials.apiSecret]);
    await prisma.brokerConnection.update({
      where: { id: row.id },
      data: { status: "error", lastCheckedAt: new Date(), lastError: message },
    });
    throw new BrokerError(message, error instanceof BrokerError ? error.status : 502);
  }
}

export async function removeConnection(userId: string, id: string) {
  const row = await ownedConnection(userId, id);
  await prisma.brokerConnection.delete({ where: { id: row.id } });
  const remaining = await prisma.brokerConnection.count({ where: { userId, venue: row.venue } });
  if (remaining === 0) {
    const bot = describeBot(row.venue);
    await prisma.personalBot.updateMany({
      where: { userId, venue: row.venue },
      data: { status: bot.status, tradingMode: "paper" },
    });
  }
}

export async function placeConnectionOrder(userId: string, id: string, body: unknown) {
  const row = await ownedConnection(userId, id);
  const environment = row.environment as BrokerEnvironment;
  const order = parseOrder(body, environment);
  const credentials = storedCredentials(row.ciphertext);
  try {
    const placed = await sendOrder(row.venue, environment, credentials, order);
    const saved = await prisma.brokerOrder.create({
      data: {
        userId,
        connectionId: row.id,
        venue: row.venue,
        environment,
        symbol: order.symbol,
        side: order.side,
        quantity: order.quantity,
        status: placed.status,
        brokerOrderId: placed.brokerOrderId,
        message: placed.message,
      },
    });
    return {
      id: saved.id,
      brokerOrderId: saved.brokerOrderId,
      status: saved.status,
      symbol: saved.symbol,
      side: saved.side,
      quantity: saved.quantity,
      environment: saved.environment,
      message: saved.message,
    };
  } catch (error) {
    const message = redactSecrets(error instanceof Error ? error.message : "The broker rejected the order.", [credentials.apiKey, credentials.apiSecret]);
    await prisma.brokerOrder.create({
      data: {
        userId,
        connectionId: row.id,
        venue: row.venue,
        environment,
        symbol: order.symbol,
        side: order.side,
        quantity: order.quantity,
        status: "rejected",
        message,
      },
    });
    throw new BrokerError(message, error instanceof BrokerError ? error.status : 502);
  }
}

export async function listConnections(userId: string) {
  await ensureBrokerTables();
  const rows = await prisma.brokerConnection.findMany({
    where: { userId },
    orderBy: [{ venue: "asc" }, { environment: "asc" }],
  });
  return { catalog: publicCatalog(), connections: rows.map(publicConnection) };
}

export function requestDraft(body: Record<string, unknown>) {
  const name = cleanText(body.name, 80);
  if (name.length < 2) throw new BrokerError("Name the broker.");
  const slug = venueSlug(name);
  if (slug && catalogBroker(slug)?.adapter === "ready") {
    throw new BrokerError("That broker is already connected from the catalog. Store the key there.");
  }
  return {
    name,
    website: optionalUrl(body.website),
    docsUrl: optionalUrl(body.docsUrl),
    notes: cleanText(body.notes, 1000),
  };
}

export async function submitBrokerRequest(userId: string, body: Record<string, unknown>) {
  await ensureBrokerTables();
  const draft = requestDraft(body);
  return prisma.brokerRequest.create({ data: { userId, ...draft, status: "submitted" } });
}
