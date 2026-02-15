# Skills

A collection of custom skills for Claude Code.

## What are Skills?

Skills are modular capabilities that extend Claude's functionality with specialized knowledge, workflows, or tool integrations. Each skill is self-contained and can be invoked when needed.

## Structure

This repository is organized as follows:

```
skills/
├── skills/           # Individual skill directories
│   ├── skill-1/      # First skill
│   └── skill-2/      # Second skill
└── README.md         # This file
```

## Using Skills

Skills can be invoked in Claude Code by:
- Using the `/skill-name` command
- Referencing them in conversation when relevant
- Claude will automatically suggest applicable skills based on context

## Skill Format

Each skill is contained in its own folder with a `SKILL.md` file that includes:

```yaml
---
name: skill-name
description: A clear description of what this skill does and when to use it
---

# Skill Name

[Instructions that Claude will follow when this skill is active]

## Examples
- Example usage 1
- Example usage 2

## Guidelines
- Guideline 1
- Guideline 2
```

## Available Skills

Skills in this repository:
- Add your skills here after creating them

## Creating New Skills

To create a new skill:

1. Create a new folder in `skills/` with your skill name (use kebab-case)
2. Add a `SKILL.md` file with the required frontmatter and instructions
3. Update this README to list the new skill

## Contributing

Add your custom skills by creating new folders in the `skills/` directory following the standard skill format.

## Resources

- [What are skills?](https://docs.anthropic.com/en/docs/build-with-claude/skills)
- [Creating custom skills](https://docs.anthropic.com/en/docs/build-with-claude/skills#creating-custom-skills)
