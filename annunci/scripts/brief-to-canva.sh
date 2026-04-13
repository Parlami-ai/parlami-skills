#!/bin/bash
# Take an Airtable brief and generate a Canva design via Musa
# Usage: ./brief-to-canva.sh '<brief_json>'
# Or pipe: echo '<brief_json>' | ./brief-to-canva.sh

CANVA_MCP="$HOME/clawd/agents/musa/skill/scripts/canva-mcp.js"

if [ -n "$1" ]; then
  BRIEF="$1"
else
  BRIEF=$(cat)
fi

# Parse brief and build Canva prompt
python3 -c "
import json, subprocess, sys

brief = json.loads('''$BRIEF''')

headline = brief.get('headline', '')
description = brief.get('description', '')
caption = brief.get('caption', '')
cta = brief.get('cta', 'Schedule a Tour')
age_group = brief.get('age_group', '')
targeting = brief.get('targeting', '')

prompt = f'''Create a professional advertisement for Amici Trilingual Montessori.
Headline: \"{headline}\"
Subtext: \"{description[:120]}\"
Caption: \"{caption}\"
Call to action: \"{cta}\"
Age group: {age_group}
Target audience: {targeting}
Location: Ahwatukee, Phoenix AZ
Key differentiator: Phoenix's Only Trilingual Montessori - Mandarin, Spanish & English
Style: Warm, professional, trustworthy, educational. Earth tones and clean layout.
Include the Amici Trilingual Montessori brand name.'''

# Build Canva generate args
args = {
    'query': prompt,
    'design_type': 'facebook_post',
    'user_intent': f'Ad creative for Amici {age_group}'
}

# Add photo asset IDs if we uploaded any
print(json.dumps(args))
"
