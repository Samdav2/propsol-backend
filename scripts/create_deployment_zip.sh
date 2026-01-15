#!/bin/bash

# Define the output zip file name
OUTPUT_FILE="backend_deployment.zip"

# Remove existing zip file if it exists
if [ -f "$OUTPUT_FILE" ]; then
    rm "$OUTPUT_FILE"
fi

# Create the zip file
# Exclude: .git, .idea, .venv, __pycache__, *.pyc, *.log, *.db (optional, maybe we want the db schema but not data, usually db is separate)
# Including: app, requirements.txt, alembic.ini, scripts (maybe useful for admin), .env.example (if exists)

zip -r "$OUTPUT_FILE" . -x "*.git*" -x "*.idea*" -x "*.venv*" -x "*__pycache__*" -x "*.pyc" -x "*.log" -x "*.db" -x "*.DS_Store"

echo "Deployment zip created: $OUTPUT_FILE"
