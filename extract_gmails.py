import os
import json

def get_chrome_profiles_emails():
    # Path to Chrome User Data on Windows
    local_app_data = os.environ.get('LOCALAPPDATA', '')
    if not local_app_data:
        print("LOCALAPPDATA environment variable not found. Please ensure you are on Windows.")
        return

    user_data_path = os.path.join(local_app_data, 'Google', 'Chrome', 'User Data')
    
    if not os.path.exists(user_data_path):
        print(f"Chrome User Data not found at: {user_data_path}")
        return

    print(f"Searching Chrome Profiles in: {user_data_path}\n")
    
    # Get all directories that might be profiles
    all_dirs = []
    try:
        all_dirs = [d for d in os.listdir(user_data_path) if os.path.isdir(os.path.join(user_data_path, d))]
    except PermissionError:
        print("Permission denied to read Chrome User Data directory. Ensure Chrome is closed or run as admin.")
        return

    # Filter for 'Default' or 'Profile *'
    profiles = [d for d in all_dirs if d == 'Default' or d.startswith('Profile ')]
    
    results = {}
    
    for p in sorted(profiles):
        pref_path = os.path.join(user_data_path, p, 'Preferences')
        if not os.path.exists(pref_path):
            continue
            
        try:
            with open(pref_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            emails = set()
            name = "Unknown Profile Name"
            
            # Extract Profile Name
            profile_info = data.get('profile', {})
            if 'name' in profile_info:
                name = profile_info['name']
                
            # Method 1: account_info list
            acc_info = data.get('account_info', [])
            for acc in acc_info:
                email = acc.get('email', '')
                if email:
                    emails.add(email)
            
            # Method 2: google.services.signin
            signin_email = data.get('google', {}).get('services', {}).get('signin', {}).get('email')
            if signin_email:
                emails.add(signin_email)
                
            results[p] = {
                'name': name,
                'emails': list(emails)
            }
                
        except Exception as e:
            results[p] = {'error': str(e)}

    # Display Results
    total_emails = 0
    print("=" * 60)
    print(f"{'PROFILE DIRECTORY':<15} | {'PROFILE NAME':<20} | GMAIL ACCOUNTS")
    print("=" * 60)
    for p, info in results.items():
        if 'error' in info:
            print(f"[{p}] Error reading profile: {info['error']}")
            continue
            
        emails_list = info['emails']
        if not emails_list:
            print(f"{p:<15} | {info['name']:<20} | No accounts found")
        else:
            # Print the first email with profile info
            print(f"{p:<15} | {info['name']:<20} | {emails_list[0]}")
            total_emails += 1
            # Print remaining emails aligned properly under the first one
            for em in emails_list[1:]:
                print(f"{'':<15} | {'':<20} | {em}")
                total_emails += 1
        print("-" * 60)
        
    print(f"\nTotal Profiles Checked: {len(results)}")
    print(f"Total Gmail Accounts Found: {total_emails}")

if __name__ == '__main__':
    get_chrome_profiles_emails()
    input("\nPress Enter to exit...")
