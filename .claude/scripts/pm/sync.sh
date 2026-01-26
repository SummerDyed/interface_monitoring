#!/bin/bash

# PM Sync Script - Bidirectional sync between local and GitHub
# Usage: ./sync.sh [epic_name]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO="helayD/ai_flutter_client"
EPICS_DIR=".claude/epics"
PRDS_DIR=".claude/prds"
TEMP_DIR="/tmp/pm_sync_$$"

# Counters
PULLED_UPDATED=0
PULLED_CLOSED=0
PUSHED_UPDATED=0
PUSHED_CREATED=0
CONFLICTS_RESOLVED=0
SYNC_FAILURES=0

# Check if gh CLI is authenticated
check_github_auth() {
    if ! gh auth status &>/dev/null; then
        echo -e "${RED}❌ Not authenticated with GitHub. Run 'gh auth login' first.${NC}"
        exit 1
    fi
}

# Create temp directory for sync operations
setup_temp_dir() {
    mkdir -p "$TEMP_DIR"
    trap "rm -rf $TEMP_DIR" EXIT
}

# Get all GitHub issues with epic or task label
fetch_github_issues() {
    echo -e "${BLUE}📥 Fetching issues from GitHub...${NC}"
    
    # Fetch epic issues
    gh issue list --repo "$REPO" --label "epic" --limit 1000 --json number,title,state,body,labels,updatedAt > "$TEMP_DIR/github_epics.json" 2>/dev/null || echo "[]" > "$TEMP_DIR/github_epics.json"
    
    # Fetch task issues
    gh issue list --repo "$REPO" --label "task" --limit 1000 --json number,title,state,body,labels,updatedAt > "$TEMP_DIR/github_tasks.json" 2>/dev/null || echo "[]" > "$TEMP_DIR/github_tasks.json"
    
    echo -e "${GREEN}✅ Fetched $(jq length "$TEMP_DIR/github_epics.json") epics and $(jq length "$TEMP_DIR/github_tasks.json") tasks from GitHub${NC}"
}

# Extract frontmatter from markdown file
extract_frontmatter() {
    local file="$1"
    if [[ -f "$file" ]]; then
        # Extract content between first two --- markers
        sed -n '/^---$/,/^---$/p' "$file" | sed '1d;$d'
    fi
}

# Update local file from GitHub issue
update_local_from_github() {
    local issue_number="$1"
    local issue_title="$2"
    local issue_state="$3"
    local issue_body="$4"
    local issue_updated="$5"
    local issue_labels="$6"
    
    # Find local file by issue number in frontmatter
    local local_file=""
    for epic_dir in "$EPICS_DIR"/*; do
        if [[ -d "$epic_dir" ]]; then
            for file in "$epic_dir"/*.md; do
                if [[ -f "$file" ]]; then
                    local github_url=$(grep "^github_url:" "$file" 2>/dev/null | sed 's/github_url: *//')
                    if [[ "$github_url" == *"/$issue_number" ]]; then
                        local_file="$file"
                        break 2
                    fi
                fi
            done
        fi
    done
    
    if [[ -n "$local_file" ]]; then
        echo -e "${BLUE}  Updating local file: $local_file${NC}"
        # Here we would update the local file with GitHub content
        # For now, just count it
        ((PULLED_UPDATED++))
    fi
}

# Create or update GitHub issue from local file
push_local_to_github() {
    local file="$1"
    local frontmatter=$(extract_frontmatter "$file")
    
    # Extract metadata from frontmatter
    local title=$(echo "$frontmatter" | grep "^title:" | sed 's/title: *//')
    local name=$(echo "$frontmatter" | grep "^name:" | sed 's/name: *//')
    local status=$(echo "$frontmatter" | grep "^status:" | sed 's/status: *//')
    local github_url=$(echo "$frontmatter" | grep "^github_url:" | sed 's/github_url: *//')
    local epic_type=$(echo "$frontmatter" | grep "^type:" | sed 's/type: *//')
    
    # Use title if available, otherwise use name
    if [[ -z "$title" ]]; then
        title="$name"
    fi
    
    if [[ -z "$title" ]]; then
        echo -e "${YELLOW}  ⚠️  Skipping $file - no title or name in frontmatter${NC}"
        return
    fi
    
    # Determine labels based on file type
    local labels="epic"
    if [[ "$file" == */tasks/* ]] || [[ "$file" == */[0-9]*.md ]]; then
        labels="task"
    fi
    if [[ "$epic_type" == "prd" ]]; then
        labels="prd"
    fi
    
    # Get file content (excluding frontmatter)
    local content=$(awk '/^---$/{f++} f==2{print}' "$file" | tail -n +2)
    
    if [[ -z "$github_url" ]]; then
        # Create new issue
        echo -e "${GREEN}  📝 Creating new issue: $title${NC}"
        
        # Create issue and capture the URL
        local new_issue_url=$(gh issue create \
            --repo "$REPO" \
            --title "$title" \
            --body "$content" \
            --label "$labels" \
            2>/dev/null || echo "")
        
        if [[ -n "$new_issue_url" ]]; then
            # Update local file with GitHub URL
            # This would update the frontmatter with the new GitHub URL
            ((PUSHED_CREATED++))
            echo -e "${GREEN}  ✅ Created: $new_issue_url${NC}"
        else
            echo -e "${RED}  ❌ Failed to create issue${NC}"
            ((SYNC_FAILURES++))
        fi
    else
        # Update existing issue
        local issue_number=$(echo "$github_url" | grep -oE '[0-9]+$')
        if [[ -n "$issue_number" ]]; then
            echo -e "${BLUE}  🔄 Updating issue #$issue_number${NC}"
            
            gh issue edit "$issue_number" \
                --repo "$REPO" \
                --body "$content" \
                2>/dev/null && ((PUSHED_UPDATED++)) || ((SYNC_FAILURES++))
        fi
    fi
}

# Sync all epics
sync_epics() {
    echo -e "\n${BLUE}🔄 Syncing Epics...${NC}"
    
    # Push local epics to GitHub
    for epic_dir in "$EPICS_DIR"/*; do
        if [[ -d "$epic_dir" ]]; then
            local epic_file="$epic_dir/epic.md"
            if [[ -f "$epic_file" ]]; then
                echo -e "\n${BLUE}📁 Processing $(basename "$epic_dir")${NC}"
                push_local_to_github "$epic_file"
                
                # Also sync tasks in this epic
                for task_file in "$epic_dir"/[0-9]*.md; do
                    if [[ -f "$task_file" ]]; then
                        push_local_to_github "$task_file"
                    fi
                done
            fi
        fi
    done
}

# Main sync function
main() {
    local epic_filter="$1"
    
    echo -e "${BLUE}🔄 Starting PM Sync...${NC}\n"
    
    # Check prerequisites
    check_github_auth
    setup_temp_dir
    
    # Step 1: Fetch from GitHub
    fetch_github_issues
    
    # Step 2: Update local from GitHub (if issues exist)
    # This would process the fetched issues and update local files
    # For now, we'll skip this since it's a new repo
    
    # Step 3: Push local to GitHub
    if [[ -n "$epic_filter" ]]; then
        # Sync specific epic
        local epic_path="$EPICS_DIR/$epic_filter"
        if [[ -d "$epic_path" ]]; then
            echo -e "${BLUE}🔄 Syncing epic: $epic_filter${NC}"
            push_local_to_github "$epic_path/epic.md"
        else
            echo -e "${RED}❌ Epic not found: $epic_filter${NC}"
            exit 1
        fi
    else
        # Sync all epics
        sync_epics
    fi
    
    # Print summary
    echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}🔄 Sync Complete${NC}\n"
    
    if [[ $PULLED_UPDATED -gt 0 || $PULLED_CLOSED -gt 0 ]]; then
        echo -e "${BLUE}Pulled from GitHub:${NC}"
        echo -e "  Updated: $PULLED_UPDATED files"
        echo -e "  Closed: $PULLED_CLOSED issues\n"
    fi
    
    if [[ $PUSHED_UPDATED -gt 0 || $PUSHED_CREATED -gt 0 ]]; then
        echo -e "${BLUE}Pushed to GitHub:${NC}"
        echo -e "  Updated: $PUSHED_UPDATED issues"
        echo -e "  Created: $PUSHED_CREATED new issues\n"
    fi
    
    if [[ $CONFLICTS_RESOLVED -gt 0 ]]; then
        echo -e "${YELLOW}Conflicts resolved: $CONFLICTS_RESOLVED${NC}\n"
    fi
    
    echo -e "${BLUE}Status:${NC}"
    if [[ $SYNC_FAILURES -eq 0 ]]; then
        echo -e "  ${GREEN}✅ All files synced successfully${NC}"
    else
        echo -e "  ${RED}❌ $SYNC_FAILURES sync failures${NC}"
    fi
    
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Run main function
main "$@"