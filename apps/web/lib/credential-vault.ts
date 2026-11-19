import { createCipheriv, createDecipheriv, randomBytes, scryptSync } from "crypto";

const SALT = "quantshift-broker-vault-v1";

type VaultEnv = { BROKER_VAULT_KEY?: string; JWT_SECRET?: string };

function vaultMaterial(env: VaultEnv = {
  BROKER_VAULT_KEY: process.env.BROKER_VAULT_KEY,
  JWT_SECRET: process.env.JWT_SECRET,
}): string {
  const dedicated = env.BROKER_VAULT_KEY?.trim() || "";
  const fallback = env.JWT_SECRET?.trim() || "";
  const material = dedicated || fallback;
  if (material.length < 16) {
    throw new Error("Set BROKER_VAULT_KEY before storing broker credentials.");
  }
  return material;
}

function keyBytes(env?: VaultEnv): Buffer {
  return scryptSync(vaultMaterial(env), SALT, 32);
}

export function sealCredentials(payload: Record<string, string>, env?: VaultEnv): string {
  const iv = randomBytes(12);
  const cipher = createCipheriv("aes-256-gcm", keyBytes(env), iv);
  const ciphertext = Buffer.concat([cipher.update(JSON.stringify(payload), "utf8"), cipher.final()]);
  const tag = cipher.getAuthTag();
  return Buffer.concat([iv, tag, ciphertext]).toString("base64");
}

export function openCredentials(sealed: string, env?: VaultEnv): Record<string, string> {
  const buf = Buffer.from(sealed, "base64");
  if (buf.length < 29) throw new Error("Stored broker credentials are unreadable.");
  const iv = buf.subarray(0, 12);
  const tag = buf.subarray(12, 28);
  const ciphertext = buf.subarray(28);
  const decipher = createDecipheriv("aes-256-gcm", keyBytes(env), iv);
  decipher.setAuthTag(tag);
  const plain = Buffer.concat([decipher.update(ciphertext), decipher.final()]).toString("utf8");
  const parsed = JSON.parse(plain) as Record<string, string>;
  if (!parsed || typeof parsed !== "object") throw new Error("Stored broker credentials are empty.");
  return parsed;
}

export function redactSecrets(message: string, secrets: string[]): string {
  let out = message || "The broker rejected the request.";
  for (const secret of secrets) {
    if (secret && secret.length > 4) out = out.split(secret).join("••••");
  }
  return out.replace(/\s+/g, " ").trim().slice(0, 300);
}
