#!/bin/bash
# Write the Google credentials JSON to a file
if [ -n "$GOOGLE_CREDENTIALS_JSON" ]; then
  echo "$GOOGLE_CREDENTIALS_JSON" > /tmp/google-credentials.json
  export GOOGLE_APPLICATION_CREDENTIALS=/tmp/google-credentials.json
  # Log the first few characters of the credentials (masked) and the file contents
  echo "GOOGLE_CREDENTIALS_JSON starts with: ${GOOGLE_CREDENTIALS_JSON:0:10}..."
  echo "Contents of /tmp/google-credentials.json:"
  cat /tmp/google-credentials.json
else
  echo "GOOGLE_CREDENTIALS_JSON is not set."
fi

# Start the app (run the CMD from the Dockerfile)
exec "$@" 