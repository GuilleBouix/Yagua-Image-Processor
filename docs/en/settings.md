# Settings

## Overview
Configure language, theme, visible modules, and check for updates.

## Supported inputs
- User configuration saved in `user_settings.json`.

## Outputs
- Persisted settings for next launches.

## Workflow
### General
- Change language/theme and visible modules.

### Updates
- “Check for updates” verifies if there is a newer stable version.
- If available, it shows a button/link to open the GitHub Release for manual download/install.

## Common errors
- No internet: update check can fail (error state is shown).

## Troubleshooting
- Logs:
  - Windows: `%APPDATA%\\Yagua\\yagua.log`
  - Linux: `~/.config/Yagua/yagua.log`
  - macOS: `~/Library/Application Support/Yagua/yagua.log`

## Examples
- Switch language to English and hide unused modules.

## Technical notes
- The update check uses the `latest.json` asset from the repo’s “latest” release.

## Limitations
- No automatic installation (download and install are manual).

## Performance tips
- If Settings feels slow: check disk performance and log size.

