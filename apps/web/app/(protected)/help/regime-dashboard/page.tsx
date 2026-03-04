'use client';

import { ProtectedRoute } from '@/components/protected-route';
import { LayoutWrapper } from '@/components/layout-wrapper';

export default function RegimeDashboardHelpPage() {
  return (
    <ProtectedRoute>
      <LayoutWrapper>
        <div className="container mx-auto px-4 py-8 max-w-4xl">
          <h1 className="text-3xl font-bold text-white mb-6">📊 Market Regime Dashboard</h1>
          
          <div className="space-y-8 text-slate-300">
            {/* Overview */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">What is the Regime Dashboard?</h2>
              <p className="mb-4">
                The Market Regime Dashboard shows you what type of market conditions the trading bot is currently detecting. 
                The bot uses machine learning to classify the market into different "regimes" and automatically adjusts 
                its trading strategies based on current conditions.
              </p>
              <p>
                Think of it like a weather forecast for the stock market - it helps the bot know whether to be aggressive, 
                conservative, or somewhere in between.
              </p>
            </section>

            {/* How to Access */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">🔍 How to Access</h2>
              <ol className="list-decimal list-inside space-y-2 ml-4">
                <li>Click <strong>Regime</strong> in the main navigation menu</li>
                <li>The dashboard will load showing current market conditions</li>
                <li>Data refreshes automatically every 30 seconds</li>
              </ol>
            </section>

            {/* Understanding Regimes */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">🎯 Understanding Market Regimes</h2>
              
              <div className="space-y-4">
                <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
                  <h3 className="text-lg font-semibold text-green-400 mb-2">🟢 Bull Trending</h3>
                  <p>Market is moving up with low volatility. Bot focuses on breakout strategies.</p>
                </div>

                <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
                  <h3 className="text-lg font-semibold text-red-400 mb-2">🔴 Bear Trending</h3>
                  <p>Market is moving down with low volatility. Bot reduces exposure and focuses on defensive strategies.</p>
                </div>

                <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
                  <h3 className="text-lg font-semibold text-blue-400 mb-2">🔵 Low Vol Range</h3>
                  <p>Market is moving sideways with low volatility. Bot uses mean reversion strategies (buy low, sell high).</p>
                </div>

                <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
                  <h3 className="text-lg font-semibold text-orange-400 mb-2">🟠 High Vol Choppy</h3>
                  <p>Market is volatile with no clear direction. Bot reduces position sizes and trades more cautiously.</p>
                </div>

                <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
                  <h3 className="text-lg font-semibold text-purple-400 mb-2">🟣 Crisis</h3>
                  <p>Extreme volatility detected. Bot may pause trading or use very conservative strategies.</p>
                </div>
              </div>
            </section>

            {/* What You'll See */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">👀 What You'll See on the Dashboard</h2>
              
              <div className="space-y-4">
                <div>
                  <h3 className="text-lg font-semibold text-cyan-400 mb-2">Current Regime Card</h3>
                  <p>Shows the current market regime with a color-coded indicator and ML confidence level (how sure the bot is).</p>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-cyan-400 mb-2">ML Model Accuracy</h3>
                  <p>Displays how accurate the machine learning model is (typically 90%+). Higher is better.</p>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-cyan-400 mb-2">Risk Multiplier</h3>
                  <p>Shows how the bot is adjusting position sizes. 1.0x is normal, lower means more conservative, higher means more aggressive.</p>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-cyan-400 mb-2">Strategy Allocation</h3>
                  <p>Bar charts showing what percentage of capital is allocated to each trading strategy based on current regime.</p>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-cyan-400 mb-2">ML Feature Importance</h3>
                  <p>Technical indicators the ML model uses to detect regimes (ATR ratio, moving averages, etc.).</p>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-cyan-400 mb-2">Regime Distribution</h3>
                  <p>Shows what percentage of time the market spent in each regime over the last 7 days.</p>
                </div>
              </div>
            </section>

            {/* How the Bot Uses This */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">🤖 How the Bot Uses Regime Detection</h2>
              <ul className="list-disc list-inside space-y-2 ml-4">
                <li><strong>Strategy Selection:</strong> Different strategies work better in different market conditions</li>
                <li><strong>Position Sizing:</strong> Adjusts how much to invest based on market volatility</li>
                <li><strong>Risk Management:</strong> Reduces exposure during uncertain or volatile periods</li>
                <li><strong>Automatic Adaptation:</strong> No manual intervention needed - bot adjusts automatically</li>
              </ul>
            </section>

            {/* Common Questions */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">❓ Common Questions</h2>
              
              <div className="space-y-4">
                <div>
                  <h3 className="text-lg font-semibold text-white mb-2">How often does the regime change?</h3>
                  <p>Regime changes are relatively infrequent - typically a few times per week. The bot requires confirmation before switching regimes to avoid false signals.</p>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-white mb-2">What does "confidence" mean?</h3>
                  <p>Confidence shows how certain the ML model is about the current regime. 50% means uncertain, 90%+ means very confident. The bot is more cautious when confidence is low.</p>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-white mb-2">Can I override the regime detection?</h3>
                  <p>No - the regime detection is fully automated. However, you can monitor it to understand why the bot is making certain trading decisions.</p>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-white mb-2">Why is the ML model so accurate?</h3>
                  <p>The model was trained on 2 years of historical market data and uses multiple technical indicators. It's been validated with 5-fold cross-validation to ensure reliability.</p>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-white mb-2">What should I do if I see a regime change?</h3>
                  <p>Nothing! The bot automatically adjusts its strategies. You can use the dashboard to understand why performance might change when market conditions shift.</p>
                </div>
              </div>
            </section>

            {/* Tips */}
            <section className="bg-slate-800 p-6 rounded-lg border border-slate-700">
              <h2 className="text-2xl font-semibold text-white mb-4">💡 Pro Tips</h2>
              <ul className="list-disc list-inside space-y-2 ml-4">
                <li>Check the regime dashboard weekly to understand current market conditions</li>
                <li>Compare regime changes with performance metrics to see how the bot adapts</li>
                <li>Low confidence regimes (below 60%) mean the market is uncertain - expect more conservative trading</li>
                <li>The dashboard updates every 30 seconds, but regime changes are infrequent</li>
                <li>Use regime history to understand long-term market patterns</li>
              </ul>
            </section>

            {/* Need More Help */}
            <section className="border-t border-slate-700 pt-6">
              <h2 className="text-2xl font-semibold text-white mb-4">📞 Need More Help?</h2>
              <p className="mb-4">
                If you have questions about the regime dashboard or how the bot uses market regime detection:
              </p>
              <ul className="list-disc list-inside space-y-2 ml-4">
                <li>Check the <a href="/help" className="text-cyan-400 hover:underline">Help Center</a> for more guides</li>
                <li>Contact your system administrator</li>
                <li>Use the <strong>Send Feedback</strong> button in the app</li>
              </ul>
            </section>
          </div>
        </div>
      </LayoutWrapper>
    </ProtectedRoute>
  );
}
