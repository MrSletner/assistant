"""
Initialization script for Local AI Assistant
Sets up memory files and documents directory
"""
import os
from pathlib import Path

# Create directory structure
dirs = [
    'memory',
    'documents',
    'voice',
    'automation',
    'config'
]

for d in dirs:
    Path(d).mkdir(exist_ok=True)
    print(f"[OK] Created {d}/")

# Create template memory files
memory_files = {
    'profile.md': '# Profile\n\nAdd information about yourself here.\n',
    'goals.md': '# Goals\n\nList your goals and objectives.\n',
    'projects.md': '# Projects\n\nDocument your projects.\n',
    'journal.md': '# Journal\n\nWrite journal entries here.\n',
}

for filename, content in memory_files.items():
    path = Path('memory') / filename
    if not path.exists():
        path.write_text(content)
        print(f"[OK] Created memory/{filename}")

print("\n[OK] Setup complete! Ready to run: docker compose up --pull always")
