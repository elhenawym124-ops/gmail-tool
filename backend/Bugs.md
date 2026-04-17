# Known Bugs & Implementation Notes

## NiceGUI / Chrome Interaction
- **Browser State**: If Chrome is already open with a specific profile, launching it again via CLI might focus the existing window instead of opening a new tab in some configurations.
- **Permission Errors**: Reading `Preferences` files requires Chrome to be closed or the files to be not exclusively locked by the browser. Added try-except to handle lock cases gracefully.

## Persistence
- **JSON Concurrency**: Tags are saved to `gmail_tags.json`. In a multi-user environment, this would need a database, but for local use, JSON is sufficient.

## Fixed Bugs
- **Table Selection Crash (2026-04-16)**: Fixed `AttributeError: 'Table' object has no attribute 'bind_selected'` by switching to the `on_select` event handler for tracking row selection in NiceGUI's `ui.table`.
- **UI Navigation Bug (2026-04-16)**: Fixed `AttributeError: module 'nicegui.ui' has no attribute 'open'` by replacing it with `ui.navigate.to(url, new_tab=True)`.
- **Wrong Account Session Bug (2026-04-16)**: Fixed an issue where the wrong Gmail account would open if multiple accounts were in one profile. Added `authuser` targeting to the launch URL.
- **Login Automation Blocking (2026-04-16)**: To avoid Google's "secure browser" blocking, implemented a "Guided Assistant" that fills credentials and provides copy-paste helpers instead of full robotic automation.
