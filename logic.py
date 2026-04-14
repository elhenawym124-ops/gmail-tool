import os
import json
import subprocess
from typing import List, Dict, Tuple, Optional

class ChromeAccountManager:
    def __init__(self, tags_file: str = "gmail_tags.json"):
        self.tags_file = os.path.join(os.path.dirname(__file__), tags_file)
        self.tags_data = self.load_tags()

    def load_tags(self) -> Dict[str, str]:
        if os.path.exists(self.tags_file):
            try:
                with open(self.tags_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_tags(self):
        try:
            with open(self.tags_file, 'w', encoding='utf-8') as f:
                json.dump(self.tags_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error saving tags: {e}")

    def update_tag(self, email: str, tag: str):
        self.tags_data[email] = tag
        self.save_tags()

    def get_chrome_user_data_path(self) -> str:
        local_app_data = os.environ.get('LOCALAPPDATA', '')
        if not local_app_data:
            return ""
        return os.path.join(local_app_data, 'Google', 'Chrome', 'User Data')

    def extract_accounts(self) -> List[Dict]:
        user_data_path = self.get_chrome_user_data_path()
        if not user_data_path or not os.path.exists(user_data_path):
            return []

        try:
            all_dirs = [d for d in os.listdir(user_data_path) if os.path.isdir(os.path.join(user_data_path, d))]
        except PermissionError:
            return []

        profiles = [d for d in all_dirs if d == 'Default' or d.startswith('Profile ')]
        results = []

        for p in sorted(profiles):
            pref_path = os.path.join(user_data_path, p, 'Preferences')
            if not os.path.exists(pref_path):
                continue

            try:
                with open(pref_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                emails = set()
                profile_name = "Unknown Profile"

                if 'profile' in data and 'name' in data['profile']:
                    profile_name = data['profile']['name']

                # Extract emails from account_info
                for acc in data.get('account_info', []):
                    email = acc.get('email', '')
                    if email:
                        emails.add(email.lower())

                # Extract signin email
                signin_email = data.get('google', {}).get('services', {}).get('signin', {}).get('email')
                if signin_email:
                    emails.add(signin_email.lower())

                for email in emails:
                    results.append({
                        "profile_dir": p,
                        "profile_name": profile_name,
                        "email": email,
                        "tags": self.tags_data.get(email, "")
                    })

            except Exception:
                continue

        return results

    def launch_chrome(self, profile_dir: str, url: str = "https://mail.google.com/mail/u/0/"):
        try:
            # Use 'start' on Windows to open in background
            cmd = f'start chrome --profile-directory="{profile_dir}" "{url}"'
            subprocess.Popen(cmd, shell=True)
            return True
        except Exception as e:
            print(f"Error launching chrome: {e}")
            return False
