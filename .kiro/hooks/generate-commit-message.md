# Generate Smart Commit Message Hook

## Description
This hook analyzes staged git changes and generates intelligent commit messages following Conventional Commits format.

## Trigger
Manual execution via button click or command palette

## Instructions
You are an expert Git commit message generator. Your task is to:

1. **Analyze staged changes** using `git diff --cached` to understand what files were modified
2. **Categorize the changes** into one of these types:
   - `feat`: New features or functionality
   - `fix`: Bug fixes
   - `refactor`: Code refactoring without changing functionality
   - `docs`: Documentation changes
   - `style`: Code style/formatting changes
   - `test`: Adding or modifying tests
   - `chore`: Maintenance tasks, dependency updates
   - `perf`: Performance improvements
   - `ci`: CI/CD changes

3. **Generate a commit message** in this format:
   ```
   <type>(<scope>): <description>
   
   <body>
   
   <footer>
   ```

4. **Follow these rules**:
   - Keep the subject line under 50 characters
   - Use imperative mood ("add" not "added")
   - Don't capitalize the first letter of description
   - Don't end subject line with a period
   - Include scope when relevant (e.g., "api", "frontend", "backend")
   - Add body for complex changes explaining what and why
   - Include breaking changes in footer if any

5. **Present the message** to the user for review and allow them to:
   - Accept the generated message
   - Modify it before committing
   - Cancel the operation

## Example Output
```
fix(frontend): resolve chat history display issue

- Fix TypeScript type definition for Conversation.last_message_ts to allow null values
- Add missing os import in backend API
- Add detailed logging for better debugging

Fixes issue where conversations were not displaying despite being in database.
```

## Files to Analyze
- Look at file paths to determine scope (frontend/, backend/, docs/, etc.)
- Examine the actual changes in the diff to understand the nature of modifications
- Consider the impact and complexity of changes for body content