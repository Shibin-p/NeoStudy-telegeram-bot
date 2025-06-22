import json
import os
from datetime import datetime

DATA_FILE = "content.json"

def load_from_json(collection_name):
    try:
        if not os.path.exists(DATA_FILE):
            return {}

        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get(collection_name, {})
    except Exception as e:
        print(f"❌ Error loading {collection_name} from JSON: {e}")
        return {}

def save_to_json(collection_name, new_data):
    try:
        data = {}

        # Load existing data
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

        # Update collection
        data[collection_name] = new_data

        # Write back to file
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"✅ Saved to content.json: {collection_name}")
        
        # Auto push changes to GitHub (optional backup)
        auto_commit_to_github()

    except Exception as e:
        print(f"❌ Error saving {collection_name} to JSON: {e}")

def auto_commit_to_github():
    try:
        os.system("git add content.json")
        os.system(f'git commit -m "📝 Auto-backup on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"')
        os.system("git push origin main")
        print("📤 Auto backup pushed to GitHub.")
    except Exception as e:
        print(f"❌ GitHub backup failed: {e}")
