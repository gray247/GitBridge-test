#!/bin/bash
API_URL="https://ac8a1417-23c9-4dc3-8ee1-5baf8d86d9af-00-2ucu3csiocbx6.spock.replit.dev"
TEST_PATH="test/test_upload.txt"
TEST_CONTENT="This is a GitBridge test file created at $(date)"

echo "Uploading test file to $TEST_PATH ..."
curl -X POST "$API_URL/upload" \
  -H "Content-Type: application/json" \
  -d "{\"path\": \"$TEST_PATH\", \"content\": \"$TEST_CONTENT\"}"
