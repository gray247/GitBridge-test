#!/bin/bash

API_URL="https://ac8a1417-23c9-4dc3-8ee1-5baf8d86d9af-00-2ucu3csiocbx6.spock.replit.dev"
TEST_FILE="test/verify_test.txt"
TEST_CONTENT="This is a GitBridge test file created at $(date)"

echo "[1] Checking /health..."
curl -s "$API_URL/health" || echo "Failed to connect"

echo -e "\n[2] Uploading test file..."
curl -s -X POST "$API_URL/upload" \
  -H "Content-Type: application/json" \
  -d "{\"path\": \"$TEST_FILE\", \"content\": \"$TEST_CONTENT\"}" || echo "Upload failed"

echo -e "\n[3] Verifying file was uploaded..."
curl -s -X POST "$API_URL/verify_upload" \
  -H "Content-Type: application/json" \
  -d "{\"path\": \"$TEST_FILE\"}" || echo "Verification failed"

echo -e "\n[4] Fetching tree to confirm file list..."
curl -s "$API_URL/tree" || echo "Tree fetch failed"