"""
generate_songs.py
Scans the /audio folder and rebuilds songs.json automatically.

Naming convention for audio files:
  Song Title - Vocals.mp3          ← vocal guide stem
  Song Title - Instrumental.mp3   ← instrumental (backing track)

Rules:
  • Both stems present  → normal song (vocal slider + pitch active)
  • Instrumental only   → transition / scene-change music (vocal + pitch greyed out)
  • Vocal only          → skipped (needs at least an instrumental)

Supported extensions: mp3, wav, m4a, aiff, ogg, flac
The showTitle in songs.json is preserved if already set; change it there manually.
"""

import os, json, re

AUDIO_DIR   = 'audio'
SONGS_FILE  = 'songs.json'
EXTENSIONS  = r'mp3|wav|m4a|aiff|ogg|flac'

# Patterns — case-insensitive, singular or plural
VOCAL_PAT = re.compile(
    rf'^(.+?)\s*-\s*Vocals?\.({EXTENSIONS})$', re.IGNORECASE
)
INSTR_PAT = re.compile(
    rf'^(.+?)\s*-\s*Instrumentals?\.({EXTENSIONS})$', re.IGNORECASE
)

# ── Read existing songs.json to preserve showTitle ────────────────────────────
show_title = 'My Show'
if os.path.exists(SONGS_FILE):
    try:
        with open(SONGS_FILE) as f:
            existing = json.load(f)
        if isinstance(existing, dict) and existing.get('showTitle'):
            show_title = existing['showTitle']
    except Exception:
        pass

# ── Scan /audio folder ────────────────────────────────────────────────────────
stems = {}   # { 'Song Title': { 'vocal': 'audio/...', 'instr': 'audio/...' } }

if os.path.isdir(AUDIO_DIR):
    for filename in os.listdir(AUDIO_DIR):
        vm = VOCAL_PAT.match(filename)
        im = INSTR_PAT.match(filename)
        if vm:
            title = vm.group(1).strip()
            stems.setdefault(title, {})['vocal'] = f'{AUDIO_DIR}/{filename}'
        elif im:
            title = im.group(1).strip()
            stems.setdefault(title, {})['instr'] = f'{AUDIO_DIR}/{filename}'

# ── Build song list ───────────────────────────────────────────────────────────
# Sort alphanumerically (so "10. Finale" sorts after "9. Song")
def alphanum_key(s):
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', s)]

songs = []
for title in sorted(stems.keys(), key=alphanum_key):
    entry = stems[title]
    if 'instr' not in entry:
        print(f'  SKIP (no instrumental): {title}')
        continue
    record = {'title': title, 'instr': entry['instr']}
    if 'vocal' in entry:
        record['vocal'] = entry['vocal']
    songs.append(record)
    kind = 'vocal + instr' if 'vocal' in entry else 'instrumental only'
    print(f'  + {title}  [{kind}]')

# ── Write songs.json ──────────────────────────────────────────────────────────
output = {'showTitle': show_title, 'songs': songs}
with open(SONGS_FILE, 'w') as f:
    json.dump(output, f, indent=2)

print(f'\nWrote {SONGS_FILE}  ({len(songs)} songs, showTitle: "{show_title}")')
