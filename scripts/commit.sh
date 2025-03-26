#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get current branch name
BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Get staged files
STAGED_FILES=$(git diff --cached --name-only)

if [ -z "$STAGED_FILES" ]; then
    echo -e "${YELLOW}No files staged for commit. Staging all modified files...${NC}"
    git add .
    STAGED_FILES=$(git diff --cached --name-only)
fi

# Get commit type from branch name
if [[ $BRANCH == feature/* ]]; then
    TYPE="feat"
elif [[ $BRANCH == bugfix/* ]]; then
    TYPE="fix"
elif [[ $BRANCH == hotfix/* ]]; then
    TYPE="fix"
else
    TYPE="chore"
fi

# Get scope from first staged file
SCOPE=$(dirname "$STAGED_FILES" | head -n 1 | tr '/' ' ' | awk '{print $NF}')

# Prompt for commit message
echo -e "${GREEN}Staged files:${NC}"
echo "$STAGED_FILES" | while read -r file; do
    echo "  - $file"
done

echo -e "\n${GREEN}Commit type:${NC} $TYPE"
echo -e "${GREEN}Scope:${NC} $SCOPE"

read -p "Enter commit description: " DESCRIPTION

# Create commit message
COMMIT_MSG="$TYPE($SCOPE): $DESCRIPTION"

# Commit changes
git commit -m "$COMMIT_MSG"

# Push changes
echo -e "\n${GREEN}Pushing changes...${NC}"
git push origin "$BRANCH"

echo -e "\n${GREEN}Done!${NC}" 