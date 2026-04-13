#!/bin/bash
# Update Airtable record status and add Canva design URL
# Usage: ./airtable-update.sh <record_id> <status> [canva_url]
# Example: ./airtable-update.sh recABC123 "Approved" "https://www.canva.com/design/..."

AIRTABLE_TOKEN="${AIRTABLE_API_TOKEN}"
BASE_ID="appTWNa6EqDTVgM8f"
TABLE_ID="tblA5Kqy9Oh64SaXM"

RECORD_ID="$1"
STATUS="$2"
CANVA_URL="$3"

if [ -z "$RECORD_ID" ] || [ -z "$STATUS" ]; then
  echo "Usage: $0 <record_id> <status> [canva_url]"
  exit 1
fi

# Build fields JSON
if [ -n "$CANVA_URL" ]; then
  FIELDS="{\"Status\": \"$STATUS\", \"Canva URL\": \"$CANVA_URL\"}"
else
  FIELDS="{\"Status\": \"$STATUS\"}"
fi

curl -s -X PATCH "https://api.airtable.com/v0/$BASE_ID/$TABLE_ID/$RECORD_ID" \
  -H "Authorization: Bearer $AIRTABLE_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"fields\": $FIELDS}"
