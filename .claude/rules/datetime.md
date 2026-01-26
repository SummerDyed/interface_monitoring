# DateTime Rule

## Getting Current Date and Time

MUST obtain REAL current date/time from system when command requires date/time for frontmatter, timestamps, or logs. Never estimate or use placeholder values.

### How to Get Current DateTime

Use the `date` command to get ISO 8601 formatted datetime:

```bash
# Primary method (Linux/Mac)
date -u +"%Y-%m-%dT%H:%M:%SZ"

# Windows PowerShell
Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
```

### Required Format

All dates in frontmatter MUST use ISO 8601 format with UTC timezone:
- Format: `YYYY-MM-DDTHH:MM:SSZ`
- Example: `2024-01-15T14:30:45Z`

### Usage in Frontmatter

```yaml
---
name: feature-name
created: 2024-01-15T14:30:45Z  # Use actual output from date command
updated: 2024-01-15T14:30:45Z  # Use actual output from date command
---
```

### Implementation Instructions

1. Before writing any file with frontmatter:
   - Run: `date -u +"%Y-%m-%dT%H:%M:%SZ"`
   - Store the output
   - Use this exact value in the frontmatter

2. For commands that create files:
   - PRD creation: Use real date for `created` field
   - Epic creation: Use real date for `created` field
   - Task creation: Use real date for both `created` and `updated` fields
   - Progress tracking: Use real date for `started` and `last_sync` fields

3. For commands that update files:
   - Always update the `updated` field with current real datetime
   - Preserve the original `created` field
   - For sync operations, update `last_sync` with real datetime

### Examples

Creating a new PRD:
```bash
# Get current datetime
CURRENT_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Use in frontmatter
---
name: user-authentication
description: User authentication and authorization system
status: backlog
created: 2024-01-15T14:30:45Z
---
```

Updating an existing task:
```bash
# Get current datetime for update
UPDATE_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Update only the 'updated' field
---
name: implement-login-api
status: in-progress
created: 2024-01-10T09:15:30Z  # Keep original
updated: 2024-01-15T14:30:45Z  # Use new value
---
```

### Important Notes

- Never use placeholder dates like `[Current ISO date/time]` or `YYYY-MM-DD`
- Never estimate dates - always get actual system time
- Always use UTC (the `Z` suffix) for consistency across timezones
- Preserve timezone consistency - all dates in system use UTC

### Cross-Platform Compatibility

For compatibility across different systems:
```bash
date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || \
python3 -c "from datetime import datetime; print(datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'))"
```

## Rule Priority

HIGHEST PRIORITY. Must be followed by all commands that:
- Create new files with frontmatter
- Update existing files with frontmatter
- Track timestamps or progress
- Log any time-based information

Commands affected: prd-new, prd-parse, epic-decompose, epic-sync, issue-start, issue-sync, and any other command that writes timestamps.
