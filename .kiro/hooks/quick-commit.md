# Quick Smart Commit Hook

## Description
Quickly analyze staged changes and generate a commit message, then execute the commit.

## Trigger
Manual execution

## Instructions
1. Run `git diff --cached --name-only` to see staged files
2. Run `git diff --cached` to see the actual changes
3. Analyze the changes and generate an appropriate commit message following Conventional Commits format
4. Ask the user to confirm the commit message
5. If confirmed, execute `git commit -m "<generated_message>"`

## Rules
- Only commit if there are staged changes
- Generate concise but descriptive messages
- Use appropriate commit type (feat, fix, refactor, etc.)
- Include scope when relevant
- Keep subject line under 50 characters