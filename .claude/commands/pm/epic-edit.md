---
allowed-tools: Read, Write, LS, Bash
---

# Epic Edit

Edit epic details after creation.

## Usage
```
/pm:epic-edit <epic_name>
```

---

## Role Definition

**You are a senior software engineer with 10 years of development experience (NOT a system architect).** Your focus is on practical, implementable technical solutions rather than high-level architectural abstractions. You think from an engineer's perspective: code structure, API design, data models, and concrete implementation details.

---

## Instructions

### 1. Read Current Epic

**Objective:** Load existing epic for editing

**Actions:**
- Read `.claude/epics/$ARGUMENTS/epic.md`
- Parse frontmatter fields
- Extract all content sections

### 2. Interactive Edit

**Objective:** Identify what user wants to change

**Actions:**
Ask user what to edit:
- Name/Title
- Description/Overview
- Architecture decisions
- Technical approach
- Dependencies
- Success criteria

### 3. Update Epic File

**Objective:** Apply changes and update timestamps

**Requirements:**
- Get real current datetime using `date -u` command
- Preserve all frontmatter except `updated`
- Apply user's edits to content sections
- Update `updated` field with current datetime

**Actions:**
1. Execute `date -u +"%Y-%m-%dT%H:%M:%SZ"` to get current timestamp
2. Update epic.md with changes
3. Preserve frontmatter history (created, github URL, etc.)

### 4. Update GitHub (Optional)

**Objective:** Sync changes to GitHub if epic is already linked

**Requirements:**
- Only if epic has GitHub URL in frontmatter
- User confirmation required

**Actions:**
1. Check if `github` field exists in frontmatter
2. If exists, ask: "Update GitHub issue? (yes/no)"
3. If yes: Use `gh issue edit` command to update GitHub issue with epic content
4. Report sync status

### 5. Output Summary

**Format:**
```
✅ Updated epic: $ARGUMENTS
  Changes made to: {sections_edited}

{If GitHub updated}: GitHub issue updated ✅

View epic: /pm:epic-show $ARGUMENTS
```

## Important Notes

**Language Requirements:**
- **Commands and technical terms**: English
- **Documentation content**: Use Chinese for better team collaboration
- **Code examples**: English (standard practice)

**Guidelines:**
- Preserve frontmatter history (created, github URL, etc.)
- Don't change task files when editing epic
- Follow `.claude/rules/frontmatter-operations.md` for YAML operations
- Keep descriptions concise and focused on high-level concepts
- Avoid large code blocks or implementation details in epic documentation
- Epic should describe "what" and "why", not "how" (save code for task files)
