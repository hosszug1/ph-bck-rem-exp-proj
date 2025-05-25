#!/bin/bash
# Entrypoint script for the worker container
set -e

echo "Starting worker setup process..."

# Function to wait for the Prefect API to be available
wait_for_prefect_api() {
    local max_attempts=15
    local attempt=0
    local wait_time=5

    echo "Waiting for Prefect API to become available..."

    while [ $attempt -lt $max_attempts ]; do
        if prefect config view &>/dev/null; then
            echo "Prefect API is available!"
            return 0
        fi

        attempt=$((attempt + 1))
        echo "Attempt $attempt/$max_attempts: Prefect API not yet available. Waiting ${wait_time}s..."
        sleep $wait_time
    done

    echo "Failed to connect to Prefect API after $max_attempts attempts"
    return 1
}

# Wait for Prefect API to be available
wait_for_prefect_api || exit 1

# Create the worker pool using Prefect CLI if it doesn't exist
if ! prefect work-pool ls | grep -q "${POOL_NAME}"; then
    echo "Creating worker pool '${POOL_NAME}'..."
    prefect work-pool create --type docker "${POOL_NAME}"
else
    echo "Worker pool '${POOL_NAME}' already exists"
fi

# Start the worker and connect to the pool
echo "Starting worker and connecting to pool '${POOL_NAME}'..."
prefect worker start --pool "${POOL_NAME}"
