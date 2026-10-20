/** Display-only fill cost. These rates are not charged and do not change an order. */

export const PAPER_COST_FROM = new Date("2026-10-13T00:00:00.000Z");

export const FILL_COST_RATES: Record<string, number> = {
  "quantshift-equity": 0.0001,
  "quantshift-crypto": 0.006,
  "quantshift-kraken": 0.004,
};

export const FILL_COST_NOTE =
  "Estimated only. Not taken from the account. Equity is 1 bp of slippage. Coinbase is 60 bp. Kraken is 40 bp.";

export function estimateFillCost(botName: string, notional: number): number {
  const rate = FILL_COST_RATES[botName] ?? 0;
  return Math.round(Math.abs(notional) * rate * 100) / 100;
}
