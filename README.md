# Gmail Extractor Pro 📧

A premium, modern tool to manage and automate Gmail accounts found within local Google Chrome profiles.

![Status Icons](https://img.shields.io/badge/UI-NiceGUI-blue)
![Status Icons](https://img.shields.io/badge/Platform-Windows-lightgrey)

## ✨ Features
- **Modern Dashboard**: Real-time stats on your local Chrome ecosystem.
- **Auto-Extraction**: Automatically finds all signed-in Gmail accounts across all Chrome profiles.
- **Platform Tagging**: Assign accounts to specific platforms (e.g., ChatGPT, Meta, Gemini) with local persistence.
- **One-Click Launch**: Launch Chrome directly into the specific Gmail account using the correct profile.
- **Bulk Verification**: Tool to compare an external list of emails against your local profiles.

## 🚀 Getting Started

### Prerequisites
- Windows OS
- Python 3.10+
- Google Chrome installed

### Installation
1. Clone the repository:
   ```bash
   git clone <your-repo-url>
   cd gmail_tools
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python main_app.py
   ```

### 🏷️ Using the App
- **Search**: Use the search bar to filter by email or platform.
- **Edit**: Click the edit icon to add/modify platform tags for an account.
- **Launch**: Click the "Open" icon to launch Chrome with that specific profile.

## 🛠️ Tech Stack
- **UI**: NiceGUI (Python + Quasar + Tailwind)
- **Logic**: Python Core
- **Database**: Local JSON Persistence

## 📄 Documentation
- [Structure](backend/Structure.md)
- [Bugs & Notes](backend/Bugs.md)
- [Team Sync](backend/TEAM_SYNC.md)
