import json
import os
import subprocess
from datetime import datetime

# Auto push content.json to GitHub
def save_to_json(data: dict):
    with open("content.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Save timestamped backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"backups/content_{timestamp}.json"
    os.makedirs("backups", exist_ok=True)
    with open(backup_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    push_to_git()

def push_to_git():
    try:
        subprocess.run(["git", "config", "--global", "user.name", os.getenv("GIT_USERNAME")], check=True)
        subprocess.run(["git", "config", "--global", "user.email", os.getenv("GIT_EMAIL")], check=True)

        subprocess.run(["git", "add", "content.json"], check=True)
        subprocess.run(["git", "add", "backups"], check=True)
        subprocess.run(["git", "commit", "-m", "🔄 Auto-update content.json"], check=True)
        subprocess.run(["git", "push", f"https://{os.getenv('GIT_TOKEN')}@github.com/{os.getenv('GIT_USERNAME')}/neostudybot.git"], check=True)
        print("✅ Pushed content.json to GitHub.")
    except subprocess.CalledProcessError as e:
        print("❌ Git push failed:", e)
