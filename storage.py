import os, json, subprocess

GIT_TOKEN = os.getenv("GITHUB_TOKEN")  # needs Write permission to repo
GIT_REPO = os.getenv("GITHUB_REPO", "")  # e.g. "YourUsername/NeoStudy-telegram-bot"
BRANCH = os.getenv("GITHUB_BRANCH", "main")

def _load_json_file(fname):
    if not os.path.exists(fname):
        return {}
    with open(fname, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def _save_json_file(fname, data):
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def save_to_json(name, data):
    """
    Call this to save 'data' dict into <name>.json locally, then commit & push to GitHub.
    name: "data" or "logs" or "suggestions"
    """
    fname = f"{name}.json"
    _save_json_file(fname, data)

    if not GIT_TOKEN or not GIT_REPO:
        return  # skip Git push if env var missing

    # Git commit & push
    subprocess.run(["git", "config", "user.name", "BotUser"], check=False)
    subprocess.run(["git", "config", "user.email", "bot@example.com"], check=False)
    subprocess.run(["git", "add", fname], check=False)
    msg = f"Auto-save '{name}' at " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    subprocess.run(["git", "commit", "-m", msg], check=False)
    remote = f"https://x-access-token:{GIT_TOKEN}@github.com/{GIT_REPO}.git"
    subprocess.run(["git", "push", remote, BRANCH], check=False)
