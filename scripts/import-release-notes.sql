-- Import release notes for versions 1.3.0 through 1.5.0

-- Version 1.3.0
INSERT INTO release_notes (id, version, title, description, changes, release_date, is_published, type, created_at, updated_at)
VALUES (
  'rn-1.3.0',
  '1.3.0',
  'Environment Indicator & Infrastructure Improvements',
  'New environment indicator showing LIVE/STANDBY status, enhanced deployment system, and improved testing coverage.',
  '{"features": ["Environment indicator with colored dot (Green=LIVE, Blue=STANDBY)", "Hover tooltip showing server details (name, status, container, IP)", "Enhanced deployment system for zero-downtime updates"], "improvements": ["Page title consistency across application", "Enhanced test coverage for reliability", "Better deployment infrastructure"], "bugFixes": ["Fixed page titles for better clarity", "Improved navigation consistency"]}',
  '2026-01-29 00:00:00',
  true,
  'minor',
  NOW(),
  NOW()
)
ON CONFLICT (version) DO UPDATE SET
  title = EXCLUDED.title,
  description = EXCLUDED.description,
  changes = EXCLUDED.changes,
  release_date = EXCLUDED.release_date,
  is_published = EXCLUDED.is_published,
  updated_at = NOW();

-- Version 1.3.1
INSERT INTO release_notes (id, version, title, description, changes, release_date, is_published, type, created_at, updated_at)
VALUES (
  'rn-1.3.1',
  '1.3.1',
  'Bug Fixes & Performance Improvements',
  'Minor bug fixes and performance enhancements for improved stability.',
  '{"bugFixes": ["Fixed environment indicator display issues", "Improved session handling"], "improvements": ["Performance optimizations", "Enhanced error handling"]}',
  '2026-01-28 00:00:00',
  true,
  'patch',
  NOW(),
  NOW()
)
ON CONFLICT (version) DO UPDATE SET
  title = EXCLUDED.title,
  description = EXCLUDED.description,
  changes = EXCLUDED.changes,
  release_date = EXCLUDED.release_date,
  is_published = EXCLUDED.is_published,
  updated_at = NOW();

-- Version 1.3.2
INSERT INTO release_notes (id, version, title, description, changes, release_date, is_published, type, created_at, updated_at)
VALUES (
  'rn-1.3.2',
  '1.3.2',
  'Dashboard Enhancements',
  'Improved dashboard layout and user experience enhancements.',
  '{"improvements": ["Enhanced dashboard layout", "Improved data visualization", "Better responsive design"], "bugFixes": ["Fixed dashboard loading issues", "Improved chart rendering"]}',
  '2026-02-01 00:00:00',
  true,
  'patch',
  NOW(),
  NOW()
)
ON CONFLICT (version) DO UPDATE SET
  title = EXCLUDED.title,
  description = EXCLUDED.description,
  changes = EXCLUDED.changes,
  release_date = EXCLUDED.release_date,
  is_published = EXCLUDED.is_published,
  updated_at = NOW();

-- Version 1.4.0
INSERT INTO release_notes (id, version, title, description, changes, release_date, is_published, type, created_at, updated_at)
VALUES (
  'rn-1.4.0',
  '1.4.0',
  'Enhanced Dashboard Analytics',
  'Major dashboard improvements with advanced analytics, real-time updates, and enhanced bot monitoring.',
  '{"features": ["Advanced analytics dashboard with real-time metrics", "Enhanced bot status monitoring", "Improved performance charts", "Real-time position tracking", "Advanced trade history filtering"], "improvements": ["Faster dashboard loading", "Better data refresh rates", "Enhanced mobile responsiveness", "Improved chart interactions"], "bugFixes": ["Fixed data synchronization issues", "Improved error handling", "Better session management"]}',
  '2026-02-18 00:00:00',
  true,
  'minor',
  NOW(),
  NOW()
)
ON CONFLICT (version) DO UPDATE SET
  title = EXCLUDED.title,
  description = EXCLUDED.description,
  changes = EXCLUDED.changes,
  release_date = EXCLUDED.release_date,
  is_published = EXCLUDED.is_published,
  updated_at = NOW();

-- Version 1.5.0
INSERT INTO release_notes (id, version, title, description, changes, release_date, is_published, type, created_at, updated_at)
VALUES (
  'rn-1.5.0',
  '1.5.0',
  'AI/ML Trading Platform',
  'Revolutionary AI-powered trading with ML market regime analysis, sentiment analysis, and deep reinforcement learning for position sizing.',
  '{"features": ["ML-powered market regime analysis (91.7% accuracy)", "Real-time regime detection (Bull, Bear, Choppy, Range, Crisis)", "FinBERT sentiment analysis for trade filtering", "Deep RL agent for intelligent position sizing", "ML Regime Analysis dashboard with dark theme", "Automated weekly model retraining", "Daily online learning for RL agent"], "improvements": ["Strategy allocation based on market regime", "Sentiment-aware trade filtering", "AI-optimized position sizing", "Enhanced risk management through ML insights"], "technical": ["RandomForest classifier integration", "PPO reinforcement learning implementation", "Custom trading environment for AI training", "Automated ML pipeline"]}',
  '2026-02-21 00:00:00',
  true,
  'minor',
  NOW(),
  NOW()
)
ON CONFLICT (version) DO UPDATE SET
  title = EXCLUDED.title,
  description = EXCLUDED.description,
  changes = EXCLUDED.changes,
  release_date = EXCLUDED.release_date,
  is_published = EXCLUDED.is_published,
  updated_at = NOW();
