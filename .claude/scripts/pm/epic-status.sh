#!/bin/bash

echo "Getting status..."
echo ""
echo ""

epic_name="$1"

if [ -z "$epic_name" ]; then
  echo "❌ Please specify an epic name"
  echo "Usage: /pm:epic-status <epic-name>"
  echo ""
  echo "Available epics:"
  for dir in .claude/epics/*/; do
    [ -d "$dir" ] && echo "  • $(basename "$dir")"
  done
  exit 1
else
  # Show status for specific epic
  epic_dir=".claude/epics/$epic_name"
  epic_file="$epic_dir/epic.md"

  if [ ! -f "$epic_file" ]; then
    echo "❌ Epic not found: $epic_name"
    echo ""
    echo "Available epics:"
    for dir in .claude/epics/*/; do
      [ -d "$dir" ] && echo "  • $(basename "$dir")"
    done
    exit 1
  fi

  echo "📚 Epic Status: $epic_name"
  echo "================================"
  echo ""

  # Extract metadata
  status=$(grep "^status:" "$epic_file" | head -1 | sed 's/^status: *//')
  progress=$(grep "^progress:" "$epic_file" | head -1 | sed 's/^progress: *//')
  github=$(grep "^github:" "$epic_file" | head -1 | sed 's/^github: *//')

  # Count tasks
  total=0
  open=0
  closed=0
  blocked=0
  deprecated=0

  # Use find to safely iterate over task files
  for task_file in "$epic_dir"/[0-9]*.md; do
    [ -f "$task_file" ] || continue
    ((total++))

    task_status=$(grep "^status:" "$task_file" | head -1 | sed 's/^status: *//')
    task_deprecated=$(grep "^deprecated:" "$task_file" | head -1 | sed 's/^deprecated: *//')
    deps=$(grep "^depends_on:" "$task_file" | head -1 | sed 's/^depends_on: *\[//' | sed 's/\]//')

    # Check if deprecated first
    if [ "$task_deprecated" = "true" ]; then
      ((deprecated++))
    elif [ "$task_status" = "closed" ] || [ "$task_status" = "completed" ]; then
      ((closed++))
    elif [ -n "$deps" ] && [ "$deps" != "depends_on:" ]; then
      ((blocked++))
    else
      ((open++))
    fi
  done

  # Display progress bar
  if [ $total -gt 0 ]; then
    percent=$((closed * 100 / total))
    filled=$((percent * 20 / 100))
    empty=$((20 - filled))

    echo -n "Progress: ["
    [ $filled -gt 0 ] && printf '%0.s█' $(seq 1 $filled)
    [ $empty -gt 0 ] && printf '%0.s░' $(seq 1 $empty)
    echo "] $percent%"
  else
    echo "Progress: No tasks created"
  fi

  echo ""
  echo "📊 Breakdown:"
  echo "  Total tasks: $total"
  echo "  ✅ Completed: $closed"
  echo "  🔄 Available: $open"
  echo "  ⏸️ Blocked: $blocked"
  [ $deprecated -gt 0 ] && echo "  🗄️  Deprecated: $deprecated"

  [ -n "$github" ] && echo ""
  [ -n "$github" ] && echo "🔗 GitHub: $github"
  
  # Show deprecated tasks if --show-deprecated flag
  if [[ "$*" == *"--show-deprecated"* ]] && [ $deprecated -gt 0 ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🗄️  Deprecated Tasks:"
    
    for task_file in "$epic_dir"/[0-9]*.md; do
      [ -f "$task_file" ] || continue
      
      task_deprecated=$(grep "^deprecated:" "$task_file" | head -1 | sed 's/^deprecated: *//')
      [ "$task_deprecated" != "true" ] && continue
      
      task_num=$(basename "$task_file" .md | grep -o '^[0-9]*')
      task_name=$(grep "^name:" "$task_file" | head -1 | sed 's/^name: *//')
      replaced_by=$(grep "^replaced_by:" "$task_file" | head -1 | sed 's/^replaced_by: *//' | tr -d '"')
      
      echo "  #$task_num - $task_name"
      [ -n "$replaced_by" ] && [ "$replaced_by" != "" ] && echo "    → Replaced by #$replaced_by"
    done
  fi
fi

exit 0
