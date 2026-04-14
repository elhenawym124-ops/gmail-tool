# Known Bugs & Implementation Notes

## NiceGUI / Chrome Interaction
- **Browser State**: If Chrome is already open with a specific profile, launching it again via CLI might focus the existing window instead of opening a new tab in some configurations.
- **Permission Errors**: Reading `Preferences` files requires Chrome to be closed or the files to be not exclusively locked by the browser. Added try-except to handle lock cases gracefully.

## Persistence
- **JSON Concurrency**: Tags are saved to `gmail_tags.json`. In a multi-user environment, this would need a database, but for local use, JSON is sufficient.
