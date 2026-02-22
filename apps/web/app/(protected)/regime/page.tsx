import { RegimeDashboard } from '@/components/regime-dashboard-simple';

export default function RegimePage() {
  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Market Regime Analysis</h2>
          <p className="text-muted-foreground">
            ML-powered regime detection with 91.7% accuracy
          </p>
        </div>
      </div>
      <RegimeDashboard />
    </div>
  );
}
