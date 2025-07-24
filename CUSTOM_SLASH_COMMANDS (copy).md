# Custom Slash Commands in Claude Code

Custom slash commands let you save frequently-used prompts as reusable commands. This guide covers everything you need to know about creating and using them.

## Overview

- Allow defining frequently-used prompts as Markdown files
- Organized by project-specific or personal scope
- Support namespacing through directory structures
- Automatically recognized - no installation required

## Command Types

### 1. Project Commands
- **Location**: `.claude/commands/`
- **Scope**: Shared with team via git
- **Identifier**: Shows "(project)" in help
- **Use case**: Team-wide workflows and standards

### 2. Personal Commands
- **Location**: `~/.claude/commands/`
- **Scope**: Available across all your projects
- **Identifier**: Shows "(user)" in help
- **Use case**: Personal productivity shortcuts

## Creating Commands

### Basic Setup

**For project commands:**
```bash
# Create the commands directory in your project
mkdir -p .claude/commands

# Create a command file
echo "Your command instructions here" > .claude/commands/your-command.md
```

**For personal commands:**
```bash
# Create personal commands directory
mkdir -p ~/.claude/commands

# Create a command file
echo "Your command instructions here" > ~/.claude/commands/your-command.md
```

### Command Structure

A typical command file looks like this:

```markdown
# Command Name
Brief description of what the command does.

## Instructions
1. First step
2. Second step
3. Third step

Additional details or context...
```

## Using Commands

### Basic Usage
- Type `/` to see all available commands
- Use: `/mycommand` or `/mycommand argument1 argument2`
- Commands appear with descriptions and scope indicators

### Syntax
```
/<command-name> [arguments]
```

## Key Features

### 1. Arguments
Use `$ARGUMENTS` placeholder for dynamic values:

```markdown
# Fix Issue Command
Fix the specified issue number.

Please fix issue #$ARGUMENTS following our coding standards.
```

Usage: `/fix-issue 123`

### 2. Namespacing
Organize commands in subdirectories:

```
.claude/commands/
├── dev/
│   └── code-review.md     # Accessed as /dev:code-review
├── test/
│   └── run-tests.md        # Accessed as /test:run-tests
└── deploy/
    └── staging.md          # Accessed as /deploy:staging
```

### 3. Execute Shell Commands
Use `!` prefix to run bash commands and include output:

```markdown
# Current Status
Check project status

## Current branch: !git branch --show-current
## Status: !git status
## Recent commits: !git log --oneline -5
```

### 4. Reference Files
Use `@` prefix to include file contents:

```markdown
# Review Code
Review the main application file

Please review this code for best practices:
@src/main.py
```

### 5. YAML Frontmatter (Optional)
Add metadata to commands:

```markdown
---
description: "Optimize code for performance"
argument-hint: "<file-path>"
allowed-tools: ["Read", "Edit", "Bash"]
---

# Optimize Performance
Analyze and optimize the specified file...
```

## Practical Examples

### 1. Git Commit Command
Save as `.claude/commands/commit.md`:

```markdown
# Commit Changes
Create a conventional commit with all current changes.

## Context
- Current status: !git status
- Changes: !git diff

## Steps
1. Analyze changes and determine commit type (feat/fix/docs/etc)
2. Stage all changes with `git add -A`
3. Create conventional commit with descriptive message
4. Push to current branch
```

Usage: `/commit`

### 2. Create Feature Command
Save as `.claude/commands/create-feature.md`:

```markdown
# Create Feature
Create a new feature: $ARGUMENTS

## Steps
1. Create feature branch from main
2. Implement the feature following our patterns
3. Add comprehensive tests
4. Update documentation
5. Create pull request
```

Usage: `/create-feature user-authentication`

### 3. Code Review Command
Save as `.claude/commands/dev/code-review.md`:

```markdown
# Code Review
Perform comprehensive code review

## Review the following files:
@$ARGUMENTS

## Check for:
1. Code style and conventions
2. Potential bugs or issues
3. Performance concerns
4. Security vulnerabilities
5. Test coverage
6. Documentation completeness
```

Usage: `/dev:code-review src/api/handlers.py`

### 4. Security Audit Command
Save as `.claude/commands/security-audit.md`:

```markdown
---
description: "Perform security audit on codebase"
allowed-tools: ["Grep", "Read", "Task"]
---

# Security Audit
Comprehensive security review of the codebase

## Audit Steps:
1. Search for hardcoded credentials
2. Check for SQL injection vulnerabilities
3. Review authentication mechanisms
4. Analyze input validation
5. Check for exposed sensitive data
6. Review dependency vulnerabilities
```

Usage: `/security-audit`

## Best Practices

### 1. Keep Commands Focused
- One command = one specific task
- Avoid overly complex commands
- Break large workflows into multiple commands

### 2. Use Descriptive Names
- Choose clear, action-oriented names
- Use namespaces for organization
- Avoid abbreviations that aren't obvious

### 3. Document Well
- Always include a description
- Provide usage examples in the command
- Specify expected arguments clearly

### 4. Version Control
- Commit project commands to git
- Share standardized workflows with team
- Review and update commands regularly

### 5. Token Optimization
- Convert repetitive instructions to commands
- Use commands instead of copying long prompts
- Reported 20% reduction in token usage

### 6. Team Collaboration
- Establish naming conventions
- Document team commands in README
- Review commands in code reviews

## Integration with CLAUDE.md

You can reference slash commands in your CLAUDE.md file:

```markdown
### Work Keywords
- **"commit my changes"**: Execute `/commit` command
- **"review this PR"**: Execute `/dev:code-review` command
- **"run security check"**: Execute `/security-audit` command
```

This allows natural language triggers for your commands.

## Common Use Cases

1. **Development Workflows**
   - Code review processes
   - Feature implementation
   - Bug fixing procedures
   - Refactoring tasks

2. **Git Operations**
   - Conventional commits
   - Branch management
   - PR creation
   - Merge procedures

3. **Testing**
   - Run specific test suites
   - Generate test cases
   - Coverage analysis
   - Performance testing

4. **Documentation**
   - Generate API docs
   - Update README
   - Create user guides
   - Document changes

5. **DevOps**
   - Deployment procedures
   - Environment setup
   - Configuration management
   - Monitoring checks

## Troubleshooting

### Command Not Found
- Check file location (`.claude/commands/` or `~/.claude/commands/`)
- Ensure `.md` extension
- Verify no syntax errors in path

### Arguments Not Working
- Use `$ARGUMENTS` exactly (case-sensitive)
- Place arguments after command: `/command arg1 arg2`
- Quote multi-word arguments if needed

### Namespace Issues
- Use colon syntax: `/namespace:command`
- Check directory structure
- Avoid special characters in names

## Advanced Techniques

### Chaining Commands
Reference other commands within commands:

```markdown
# Full Deploy
Complete deployment process

1. First run tests: Execute /test:all
2. Then create commit: Execute /commit
3. Finally deploy: Execute /deploy:production
```

### Conditional Logic
Use bash commands for conditions:

```markdown
# Smart Commit
Intelligent commit based on changes

Branch: !git branch --show-current
Has tests: !find . -name "*test*" -type f | head -1

Create appropriate commit based on branch and test presence.
```

### Multi-file Operations
Process multiple files:

```markdown
# Refactor Module
Refactor all files in module: $ARGUMENTS

Files to process: !find $ARGUMENTS -name "*.py"

Apply consistent refactoring across all files.
```

## Conclusion

Custom slash commands are a powerful way to:
- Standardize workflows
- Save time on repetitive tasks
- Share best practices with your team
- Reduce token usage
- Ensure consistency

Start with simple commands and gradually build your library as you identify repetitive patterns in your workflow.