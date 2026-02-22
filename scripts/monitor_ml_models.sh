#!/bin/bash
#
# ML Model Monitoring Script
# Checks model performance and alerts if accuracy degrades
# Schedule: Daily at 6 PM UTC (after market close)
#
# Usage: /opt/quantshift/scripts/monitor_ml_models.sh
#

set -e

# Configuration
QUANTSHIFT_HOME="/opt/quantshift"
MODELS_DIR="${QUANTSHIFT_HOME}/models"
LOGS_DIR="${QUANTSHIFT_HOME}/logs"
MONITOR_LOG="${LOGS_DIR}/model-monitoring-$(date +%Y%m%d).log"

# Thresholds
ACCURACY_WARNING_THRESHOLD=0.85
ACCURACY_CRITICAL_THRESHOLD=0.75
MODEL_AGE_WARNING_DAYS=30

# Email configuration
ADMIN_EMAIL="${ADMIN_EMAIL:-}"
SEND_EMAIL="${SEND_EMAIL:-false}"

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "${MONITOR_LOG}"
}

log "=========================================="
log "ML Model Monitoring Check"
log "=========================================="

# Check if model exists
if [ ! -f "${MODELS_DIR}/regime_classifier.pkl" ]; then
    log "ERROR: Model file not found at ${MODELS_DIR}/regime_classifier.pkl"
    exit 1
fi

# Check model age
MODEL_AGE_DAYS=$(( ($(date +%s) - $(stat -f %m "${MODELS_DIR}/regime_classifier.pkl" 2>/dev/null || stat -c %Y "${MODELS_DIR}/regime_classifier.pkl")) / 86400 ))
log "Model age: ${MODEL_AGE_DAYS} days"

ALERTS=""

# Alert if model is old
if [ ${MODEL_AGE_DAYS} -gt ${MODEL_AGE_WARNING_DAYS} ]; then
    ALERT="⚠️  Model is ${MODEL_AGE_DAYS} days old (threshold: ${MODEL_AGE_WARNING_DAYS} days)"
    log "${ALERT}"
    ALERTS="${ALERTS}\n${ALERT}"
fi

# Check recent training logs for accuracy
LATEST_TRAINING_LOG=$(ls -t "${LOGS_DIR}"/model-training-*.log 2>/dev/null | head -1)
if [ -n "${LATEST_TRAINING_LOG}" ]; then
    ACCURACY=$(grep -oP 'Test Accuracy: \K[0-9.]+' "${LATEST_TRAINING_LOG}" | tail -1)
    
    if [ -n "${ACCURACY}" ]; then
        log "Latest model accuracy: ${ACCURACY}"
        
        # Check if accuracy is below critical threshold
        if (( $(echo "${ACCURACY} < ${ACCURACY_CRITICAL_THRESHOLD}" | bc -l) )); then
            ALERT="🔴 CRITICAL: Model accuracy ${ACCURACY} below threshold ${ACCURACY_CRITICAL_THRESHOLD}"
            log "${ALERT}"
            ALERTS="${ALERTS}\n${ALERT}"
        # Check if accuracy is below warning threshold
        elif (( $(echo "${ACCURACY} < ${ACCURACY_WARNING_THRESHOLD}" | bc -l) )); then
            ALERT="🟡 WARNING: Model accuracy ${ACCURACY} below threshold ${ACCURACY_WARNING_THRESHOLD}"
            log "${ALERT}"
            ALERTS="${ALERTS}\n${ALERT}"
        else
            log "✅ Model accuracy is healthy: ${ACCURACY}"
        fi
    fi
fi

# Check disk space for model storage
DISK_USAGE=$(df -h "${MODELS_DIR}" | awk 'NR==2 {print $5}' | sed 's/%//')
if [ ${DISK_USAGE} -gt 90 ]; then
    ALERT="⚠️  Disk usage high: ${DISK_USAGE}%"
    log "${ALERT}"
    ALERTS="${ALERTS}\n${ALERT}"
fi

# Count model backups
BACKUP_COUNT=$(ls -1 "${MODELS_DIR}/backups"/regime_classifier_*.pkl 2>/dev/null | wc -l)
log "Model backups available: ${BACKUP_COUNT}"

log "=========================================="
log "Monitoring check complete"
log "=========================================="

# Send alert email if there are any alerts
if [ -n "${ALERTS}" ] && [ "${SEND_EMAIL}" = "true" ] && [ -n "${ADMIN_EMAIL}" ]; then
    {
        echo "ML Model Monitoring Alerts"
        echo ""
        echo "Date: $(date)"
        echo ""
        echo "Alerts:"
        echo -e "${ALERTS}"
        echo ""
        echo "Model Details:"
        echo "  Age: ${MODEL_AGE_DAYS} days"
        echo "  Accuracy: ${ACCURACY:-N/A}"
        echo "  Backups: ${BACKUP_COUNT}"
        echo "  Disk Usage: ${DISK_USAGE}%"
        echo ""
        echo "Full monitoring log:"
        echo "----------------------------------------"
        cat "${MONITOR_LOG}"
    } | mail -s "ML Model Monitoring Alerts - $(date)" "${ADMIN_EMAIL}"
fi

# Cleanup old monitoring logs (keep last 30 days)
find "${LOGS_DIR}" -name "model-monitoring-*.log" -mtime +30 -delete 2>/dev/null || true

exit 0
