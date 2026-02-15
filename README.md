# Skills

A collection of custom agent skills for AI coding assistants (Claude Code, Cursor, etc.). Licensed under [Apache License 2.0](LICENSE). Each skill adds specialized capabilities—design systems, diagram generation, publishing workflows—that can be invoked when relevant.

## What are Skills?

Skills are modular capabilities that extend an AI assistant with focused knowledge, workflows, or tool integrations. Each skill is self-contained (a folder with a `SKILL.md` file) and is activated when the task matches the skill’s description or triggers.

## Structure

```
skills/
├── skills/
│   ├── beautiful-ui/        # Glassmorphism UI with Next.js + Tailwind v4
│   ├── beautiful-diagrams/  # Article diagrams via HTML + Playwright
│   └── substack-publisher/  # Publish markdown to Substack
└── README.md
```

## Available Skills

| Skill | Description |
|-------|-------------|
| **beautiful-ui** | Build glassmorphism dark-mode interfaces with Next.js and Tailwind CSS v4: translucent surfaces, luminous palettes, Framer Motion, and production-ready code. |
| **beautiful-diagrams** | Generate article-ready diagrams (pipelines, sequences, grids) using HTML + Playwright screenshots—canvas background, gradient cards, clean typography. |
| **substack-publisher** | Publish markdown posts to Substack as drafts or articles; converts markdown to Substack’s ProseMirror JSON and supports dry-run. |

## Using Skills

Depending on your environment:

- **Claude Code** — Use `/skill-name`, reference the skill in conversation, or let Claude suggest it from context.
- **Cursor** — Skills under `.cursor/skills/` or linked from agent skills are suggested automatically when the conversation matches their description.

## Skill Format

Each skill lives in its own folder with a `SKILL.md` file. Frontmatter defines name and when to use it; the body holds instructions the model follows when the skill is active.

```yaml
---
name: skill-name
description: When to use this skill and what it does
---

# Skill Name

[Instructions, examples, and guidelines]
```

## Adding New Skills

1. Create a folder in `skills/` (e.g. `skills/my-skill/`).
2. Add `SKILL.md` with the YAML frontmatter and instructions.
3. Add the skill to the **Available Skills** table in this README.

## Resources

- [What are skills?](https://docs.anthropic.com/en/docs/build-with-claude/skills)
- [Creating custom skills](https://docs.anthropic.com/en/docs/build-with-claude/skills#creating-custom-skills)
