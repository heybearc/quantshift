# ML Model Lifecycle Management

**Last Updated:** 2026-02-22  
**Status:** ✅ Production Ready

---

## Overview

QuantShift uses machine learning for market regime detection with automated lifecycle management to ensure models stay accurate and up-to-date.

**Current Model:**
- **Type:** Random Forest Classifier
- **Purpose:** Market regime detection (Bull/Bear/High Vol/Low Vol/Crisis)
- **Accuracy:** 91.7% (test), 93.3% (cross-validation)
- **Features:** ATR ratio, SMA slopes, MACD, RSI, volume
- **Training Data:** 2 years SPY historical data

---

## Automated Processes

### 1. Weekly Retraining (Sundays 2 AM UTC)

**Script:** `/opt/quantshift/scripts/retrain_ml_models.sh`

**What it does:**
1. Backs up current model (keeps last 3 versions)
2. Trains new model on rolling 2-year window
3. Validates accuracy (must be > 75%)
4. Deploys to primary and standby servers
5. Sends email report (if configured)
6. Cleans up old logs and backups

**Cron schedule:**
```bash
0 2 * * 0 /opt/quantshift/scripts/retrain_ml_models.sh
```

**Logs:**
- Training logs: `/opt/quantshift/logs/model-training-YYYYMMDD-HHMMSS.log`
- Keeps last 10 training logs

**Model backups:**
- Location: `/opt/quantshift/models/backups/`
- Format: `regime_classifier_YYYYMMDD-HHMMSS.pkl`
- Retention: Last 3 versions

### 2. Daily Monitoring (6 PM UTC)

**Script:** `/opt/quantshift/scripts/monitor_ml_models.sh`

**What it checks:**
- Model accuracy (warns if < 85%, critical if < 75%)
- Model age (warns if > 30 days old)
- Disk space for model storage
- Number of available backups

**Cron schedule:**
```bash
0 18 * * * /opt/quantshift/scripts/monitor_ml_models.sh
```

**Alert thresholds:**
- 🟢 **Healthy:** Accuracy ≥ 85%, Age ≤ 30 days
- 🟡 **Warning:** Accuracy 75-85%, Age 30-45 days
- 🔴 **Critical:** Accuracy < 75%, Age > 45 days

**Logs:**
- Monitoring logs: `/opt/quantshift/logs/model-monitoring-YYYYMMDD.log`
- Retention: 30 days

---

## Manual Operations

### Train Model Manually

```bash
# SSH to primary server
ssh quantshift-primary

# Run training script
/opt/quantshift/scripts/retrain_ml_models.sh

# Or run Python script directly
cd /opt/quantshift
source venv/bin/activate
python apps/bots/equity/train_ml_regime_classifier.py
```

### Check Model Status

```bash
# View current model
ls -lh /opt/quantshift/models/regime_classifier.pkl

# Check model age
stat /opt/quantshift/models/regime_classifier.pkl

# View available backups
ls -lh /opt/quantshift/models/backups/

# Check latest training log
tail -100 /opt/quantshift/logs/model-training-*.log | tail -1
```

### Rollback to Previous Model

```bash
# List available backups
ls -lt /opt/quantshift/models/backups/

# Copy backup to active model
cp /opt/quantshift/models/backups/regime_classifier_YYYYMMDD-HHMMSS.pkl \
   /opt/quantshift/models/regime_classifier.pkl

# Deploy to standby
scp /opt/quantshift/models/regime_classifier.pkl \
    quantshift-standby:/opt/quantshift/models/

# Restart bots to load new model
systemctl restart quantshift-equity
ssh quantshift-standby "systemctl restart quantshift-equity"
```

### Force Retraining

```bash
# Run retraining immediately (don't wait for Sunday)
/opt/quantshift/scripts/retrain_ml_models.sh

# Check if new model is better
tail -50 /opt/quantshift/logs/model-training-*.log | grep -E 'Accuracy|Features'
```

---

## Email Alerts Configuration

To enable email alerts for training failures and monitoring warnings:

```bash
# Set environment variables (add to /etc/environment or crontab)
export ADMIN_EMAIL="admin@example.com"
export SEND_EMAIL="true"

# Update crontab with environment variables
crontab -e

# Add these lines at the top:
ADMIN_EMAIL=admin@example.com
SEND_EMAIL=true
```

**Alert types:**
- ✅ **Training success:** Weekly summary with accuracy metrics
- ❌ **Training failure:** Immediate alert with error details
- ⚠️ **Monitoring warnings:** Daily if thresholds exceeded

---

## Model Performance Tracking

### Key Metrics

**Training Metrics:**
- Test accuracy (target: > 90%)
- Cross-validation accuracy (target: > 90%)
- Feature importance (top 5 features)

**Production Metrics:**
- Prediction accuracy vs actual outcomes
- Regime detection latency
- Model age (days since last training)

### Viewing Metrics

```bash
# Latest training results
grep -E 'Accuracy|Features' /opt/quantshift/logs/model-training-*.log | tail -20

# Model performance over time
for log in /opt/quantshift/logs/model-training-*.log; do
    echo "$(basename $log):"
    grep 'Test Accuracy' "$log"
done
```

---

## Troubleshooting

### Training Fails

**Check logs:**
```bash
tail -100 /opt/quantshift/logs/model-training-*.log
```

**Common issues:**
- Insufficient training data (need 2 years)
- Yahoo Finance API rate limit
- Disk space full
- Python dependencies missing

**Solutions:**
```bash
# Check disk space
df -h /opt/quantshift

# Verify dependencies
source /opt/quantshift/venv/bin/activate
pip list | grep -E 'scikit-learn|pandas|yfinance'

# Test data fetch manually
python -c "import yfinance as yf; df = yf.download('SPY', period='2y'); print(len(df))"
```

### Model Not Deploying to Standby

**Check SSH connectivity:**
```bash
ssh quantshift-standby "echo 'Connection OK'"
```

**Manual deployment:**
```bash
scp /opt/quantshift/models/regime_classifier.pkl \
    quantshift-standby:/opt/quantshift/models/
```

### Accuracy Degrading

**Possible causes:**
- Market regime shift (2020 COVID, 2022 rate hikes)
- Insufficient recent data
- Feature drift

**Actions:**
1. Review recent market conditions
2. Check if training data is current
3. Consider adding new features
4. Retrain with longer historical window
5. Compare ML vs rule-based performance

---

## Best Practices

### DO ✅

- **Monitor weekly:** Review training logs every Monday
- **Keep backups:** Always maintain last 3 model versions
- **Test before deploy:** Validate accuracy before production
- **Document changes:** Note any manual interventions
- **Track metrics:** Monitor accuracy trends over time

### DON'T ❌

- **Don't auto-deploy** if accuracy drops significantly
- **Don't delete backups** manually (automated cleanup)
- **Don't skip validation** when rolling back
- **Don't train during market hours** (use Sunday 2 AM)
- **Don't ignore warnings** from monitoring script

---

## Future Enhancements

**Planned (Phase 0.5 completion):**
- [ ] Admin UI dashboard for model management
- [ ] "Train Now" button in web interface
- [ ] Model performance comparison charts
- [ ] A/B testing framework (50% ML, 50% rule-based)
- [ ] Automatic rollback if accuracy < 75%
- [ ] Slack/Discord alerts (in addition to email)

**Under consideration:**
- [ ] Multi-model ensemble (combine multiple classifiers)
- [ ] Real-time accuracy tracking (vs actual outcomes)
- [ ] Hyperparameter auto-tuning
- [ ] Feature importance drift detection
- [ ] Model explainability dashboard (SHAP values)

---

## References

- **Training script:** `apps/bots/equity/train_ml_regime_classifier.py`
- **Model class:** `packages/core/src/quantshift_core/ml_regime_classifier.py`
- **Retraining script:** `scripts/retrain_ml_models.sh`
- **Monitoring script:** `scripts/monitor_ml_models.sh`
- **Implementation plan:** `IMPLEMENTATION-PLAN.md` (Phase 0.4, 0.5)

---

## Support

**Questions or issues?**
1. Check logs: `/opt/quantshift/logs/`
2. Review this documentation
3. Test scripts manually before troubleshooting cron
4. Contact system administrator

**Emergency rollback:**
```bash
# Use most recent backup
LATEST_BACKUP=$(ls -t /opt/quantshift/models/backups/*.pkl | head -1)
cp "$LATEST_BACKUP" /opt/quantshift/models/regime_classifier.pkl
systemctl restart quantshift-equity
```
