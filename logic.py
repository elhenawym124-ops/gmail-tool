import os
import json
import subprocess
import shutil
import tempfile
import csv
import io
from typing import List, Dict, Tuple, Optional

class ChromeAccountManager:
    def __init__(self, tags_file: str = "gmail_tags.json", watchlist_file: str = "gmail_watchlist.json", credentials_file: str = "gmail_credentials.json"):
        import sys
        if getattr(sys, 'frozen', False):
            # Running as bundled exe - store data files next to the exe
            base_dir = os.path.dirname(sys.executable)
        else:
            # Running as script - store in the same directory as logic.py
            base_dir = os.path.dirname(__file__)
            
        self.tags_file = os.path.join(base_dir, tags_file)
        self.watchlist_file = os.path.join(base_dir, watchlist_file)
        self.credentials_file = os.path.join(base_dir, credentials_file)
        self.tags_data = self.load_tags()
        self.watchlist_data = self.load_watchlist()
        self.credentials_data = self.load_credentials()

    def load_credentials(self) -> Dict[str, Dict[str, str]]:
        if os.path.exists(self.credentials_file):
            try:
                with open(self.credentials_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_credentials(self):
        try:
            with open(self.credentials_file, 'w', encoding='utf-8') as f:
                json.dump(self.credentials_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error saving credentials: {e}")

    def update_credentials(self, email: str, password: str = "", recovery_email: str = ""):
        self.credentials_data[email] = {
            "password": password,
            "recovery_email": recovery_email
        }
        self.save_credentials()

    def bulk_update_credentials(self, creds_list: List[Dict[str, str]]):
        """Update multiple credentials and save once."""
        for entry in creds_list:
            email = entry.get('email', '').strip().lower()
            if email:
                self.credentials_data[email] = {
                    "password": entry.get('password', ''),
                    "recovery_email": entry.get('recovery_email', '')
                }
        self.save_credentials()

    def get_credentials(self, email: str) -> Dict[str, str]:
        return self.credentials_data.get(email, {"password": "", "recovery_email": ""})

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

    # --- Watchlist Management ---
    def load_watchlist(self) -> List[str]:
        if os.path.exists(self.watchlist_file):
            try:
                with open(self.watchlist_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def save_watchlist(self):
        try:
            with open(self.watchlist_file, 'w', encoding='utf-8') as f:
                json.dump(self.watchlist_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error saving watchlist: {e}")

    def add_to_watchlist(self, emails: List[str]):
        added = 0
        current_set = set(e.lower() for e in self.watchlist_data)
        for e in emails:
            e_low = e.lower()
            if e_low not in current_set:
                self.watchlist_data.append(e_low)
                current_set.add(e_low)
                added += 1
        if added > 0:
            self.save_watchlist()
        return added

    def remove_from_watchlist(self, email: str):
        email_low = email.lower()
        if email_low in self.watchlist_data:
            self.watchlist_data.remove(email_low)
            self.save_watchlist()
            return True
        return False

    def prune_watchlist(self, active_emails: List[str]) -> int:
        """Remove emails from watchlist that have been found in the system."""
        active_set = set(e.lower() for e in active_emails)
        before_count = len(self.watchlist_data)
        self.watchlist_data = [e for e in self.watchlist_data if e.lower() not in active_set]
        if len(self.watchlist_data) < before_count:
            self.save_watchlist()
            return before_count - len(self.watchlist_data)
        return 0

    def cleanup_tags(self, active_emails: List[str]):
        """Remove tags for emails that are no longer present on the system."""
        active_set = set(e.lower() for e in active_emails)
        before_count = len(self.tags_data)
        self.tags_data = {e: t for e, t in self.tags_data.items() if e.lower() in active_set}
        if len(self.tags_data) < before_count:
            self.save_tags()
            return before_count - len(self.tags_data)
        return 0

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

        # Temp directory for copying locked files
        with tempfile.TemporaryDirectory() as temp_dir:
            for p in sorted(profiles):
                # Avatar detection
                avatar_path = os.path.join(user_data_path, p, 'Google Profile Picture.png')
                if not os.path.exists(avatar_path):
                    avatar_path = None # Use default

                pref_path = os.path.join(user_data_path, p, 'Preferences')
                if not os.path.exists(pref_path):
                    continue

                try:
                    # Try to read directly, if fails, copy to temp
                    try:
                        with open(pref_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                    except (PermissionError, IOError):
                        temp_pref = os.path.join(temp_dir, f"{p}_pref")
                        shutil.copy2(pref_path, temp_pref)
                        with open(temp_pref, 'r', encoding='utf-8') as f:
                            data = json.load(f)

                    emails = set()
                    profile_name = "Unknown Profile"

                    if 'profile' in data and 'name' in data['profile']:
                        profile_name = data['profile']['name']

                    for acc in data.get('account_info', []):
                        email = acc.get('email', '')
                        if email:
                            emails.add(email.lower())

                    signin_email = data.get('google', {}).get('services', {}).get('signin', {}).get('email')
                    if signin_email:
                        emails.add(signin_email.lower())

                    for email in emails:
                        creds = self.get_credentials(email)
                        results.append({
                            "profile_dir": p,
                            "profile_name": profile_name,
                            "email": email,
                            "tags": self.tags_data.get(email, ""),
                            "password": creds["password"],
                            "recovery_email": creds["recovery_email"],
                            "avatar": avatar_path
                        })

                except Exception as e:
                    print(f"Error reading profile {p}: {e}")
                    continue

        return results

    def launch_chrome(self, profile_dir: str, email: Optional[str] = None, url: str = "https://mail.google.com/mail/u/"):
        try:
            target_url = url
            if email:
                # Use authuser parameter to switch to specific account within the profile
                target_url = f"{url}?authuser={email}"
            
            cmd = f'start chrome --profile-directory="{profile_dir}" "{target_url}"'
            subprocess.Popen(cmd, shell=True)
            return True
        except Exception as e:
            print(f"Error launching chrome: {e}")
            return False

    def export_to_csv(self, accounts: List[Dict]) -> str:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["profile_name", "email", "tags", "profile_dir"])
        writer.writeheader()
        for acc in accounts:
            # Filter keys to match fieldnames
            row = {k: acc[k] for k in ["profile_name", "email", "tags", "profile_dir"]}
            writer.writerow(row)
        return output.getvalue()
