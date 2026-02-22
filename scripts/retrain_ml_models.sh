#!/bin/bash
#
# ML Model Retraining Script
# Runs weekly to retrain ML regime classifier with latest market data
# Schedule: Sunday 2 AM UTC (when markets closed)
#
# Usage: /opt/quantshift/scripts/retrain_ml_models.sh
#

set -e

# Configuration
QUANTSHIFT_HOME="/opt/quantshift"
VENV_PATH="${QUANTSHIFT_HOME}/venv"
MODELS_DIR="${QUANTSHIFT_HOME}/models"
LOGS_DIR="${QUANTSHIFT_HOME}/logs"
BACKUP_DIR="${QUANTSHIFT_HOME}/models/backups"
TRAINING_LOG="${LOGS_DIR}/model-training-$(date +%Y%m%d-%H%M%S).log"

# Email configuration (optional)
ADMIN_EMAIL="${ADMIN_EMAIL:-}"
SEND_EMAIL="${SEND_EMAIL:-false}"

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "${TRAINING_LOG}"
}

# Error handler
error_exit() {
    log "ERROR: $1"
    if [ "${SEND_EMAIL}" = "true" ] && [ -n "${ADMIN_EMAIL}" ]; then
        mail -s "ML Model Training Failed - $(date)" "${ADMIN_EMAIL}" < "${TRAINING_LOG}"
    fi
    exit 1
}

log "=========================================="
log "ML Model Retraining Started"
log "=========================================="

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

# Backup existing models
log "Backing up existing models..."
if [ -f "${MODELS_DIR}/regime_classifier.pkl" ]; then
    BACKUP_FILE="${BACKUP_DIR}/regime_classifier_$(date +%Y%m%d-%H%M%S).pkl"
    cp "${MODELS_DIR}/regime_classifier.pkl" "${BACKUP_FILE}"
    log "Backed up to: ${BACKUP_FILE}"
    
    # Keep only last 3 backups
    ls -t "${BACKUP_DIR}"/regime_classifier_*.pkl | tail -n +4 | xargs -r rm
    log "Cleaned up old backups (keeping last 3)"
fi

# Activate virtual environment
log "Activating virtual environment..."
source "${VENV_PATH}/bin/activate" || error_exit "Failed to activate venv"

# Train ML regime classifier
log "Training ML regime classifier..."
cd "${QUANTSHIFT_HOME}"
python apps/bots/equity/train_ml_regime_classifier.py >> "${TRAINING_LOG}" 2>&1 || error_exit "ML training failed"

# Verify model was created
if [ ! -f "${MODELS_DIR}/regime_classifier.pkl" ]; then
    error_exit "Model file not created after training"
fi

# Copy model to standby server
log "Deploying model to standby server..."
if scp "${MODELS_DIR}/regime_classifier.pkl" quantshift-standby:"${MODELS_DIR}/" >> "${TRAINING_LOG}" 2>&1; then
    log "Model deployed to standby successfully"
else
    log "WARNING: Failed to deploy to standby (continuing anyway)"
fi

# Extract accuracy from training log
ACCURACY=$(grep -oP 'Test Accuracy: \K[0-9.]+' "${TRAINING_LOG}" | tail -1)
CV_ACCURACY=$(grep -oP 'CV Mean Accuracy: \K[0-9.]+' "${TRAINING_LOG}" | tail -1)

log "=========================================="
log "ML Model Retraining Complete"
log "Test Accuracy: ${ACCURACY:-N/A}"
log "CV Accuracy: ${CV_ACCURACY:-N/A}"
log "Model saved to: ${MODELS_DIR}/regime_classifier.pkl"
log "Training log: ${TRAINING_LOG}"
log "=========================================="

# Send success email
if [ "${SEND_EMAIL}" = "true" ] && [ -n "${ADMIN_EMAIL}" ]; then
    {
        echo "ML Model Retraining Completed Successfully"
        echo ""
        echo "Date: $(date)"
        echo "Test Accuracy: ${ACCURACY:-N/A}"
        echo "CV Accuracy: ${CV_ACCURACY:-N/A}"
        echo ""
        echo "Full training log attached below:"
        echo "----------------------------------------"
        cat "${TRAINING_LOG}"
    } | mail -s "ML Model Retrained Successfully - $(date)" "${ADMIN_EMAIL}"
fi

# Cleanup old training logs (keep last 10)
log "Cleaning up old training logs..."
ls -t "${LOGS_DIR}"/model-training-*.log | tail -n +11 | xargs -r rm

log "Script completed successfully"
exit 0
