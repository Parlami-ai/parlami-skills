#!/bin/bash
# Pull creative briefs from Airtable AMICI PMAX Creatives table
# Outputs JSON briefs ready for Musa/Canva

AIRTABLE_TOKEN="${AIRTABLE_API_TOKEN}"
BASE_ID="appTWNa6EqDTVgM8f"
TABLE_ID="tblA5Kqy9Oh64SaXM"

# Optional: filter by status (Draft, Approved, Live)
STATUS_FILTER="${1:-Draft}"

curl -s "https://api.airtable.com/v0/$BASE_ID/$TABLE_ID?filterByFormula=%7BStatus%7D%3D%22$STATUS_FILTER%22" \
  -H "Authorization: Bearer $AIRTABLE_TOKEN" | python3 -c "
import json, sys

data = json.load(sys.stdin)
briefs = []

for r in data.get('records', []):
    f = r.get('fields', {})
    
    # Extract photo URLs from Airtable attachments
    photos = []
    for img in f.get('Image', []):
        photos.append({
            'url': img.get('url', ''),
            'filename': img.get('filename', ''),
            'width': img.get('width', 0),
            'height': img.get('height', 0)
        })
    
    brief = {
        'record_id': r['id'],
        'campaign': f.get('Campaign Name', ''),
        'asset_group': f.get('Ad Groups / Segment', ''),
        'age_group': f.get('Age Group', ''),
        'headline': f.get('Headline 1', ''),
        'description': f.get('Description 1', ''),
        'caption': f.get('Image/Video Caption', ''),
        'cta': f.get('Call To Action', ''),
        'final_url': f.get('Final URL', ''),
        'targeting': f.get('Targeting', ''),
        'ad_sizes': f.get('Ad Size / Format', ''),
        'status': f.get('Status', ''),
        'photos': photos,
        'photo_count': len(photos)
    }
    briefs.append(brief)

print(json.dumps(briefs, indent=2))
"
