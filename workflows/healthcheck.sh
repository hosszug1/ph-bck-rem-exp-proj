#!/bin/bash
# healthcheck.sh - Script to check if Prefect server is running

set -e

MAX_ATTEMPTS=30
SLEEP_TIME=2
ATTEMPT=1

echo "Checking Prefect server health..."

while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    echo "Attempt $ATTEMPT/$MAX_ATTEMPTS: Checking connection to Prefect API..."

    # Try to get health info from Prefect API
    if curl -s -f "$PREFECT_API_URL/health" >/dev/null; then
        echo "Prefect server is healthy and ready!"
        exit 0
    fi

    ATTEMPT=$((ATTEMPT + 1))
    echo "Prefect server not ready yet. Waiting ${SLEEP_TIME}s..."
    sleep $SLEEP_TIME
done

echo "Failed to connect to Prefect server after $MAX_ATTEMPTS attempts."
exit 1
