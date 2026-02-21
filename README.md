# Claude Code Skills

A collection of skills for [Claude Code](https://github.com/anthropics/claude-code) that extend Claude with domain-specific knowledge and workflows.

## Repository Structure

Each skill lives in its own directory:

```
skills/
├── django-crud-views/
│   ├── SKILL.md              # Main skill file (required)
│   └── references/           # Optional supporting files
│       └── api-reference.md
└── your-skill/
    └── SKILL.md
```

### `SKILL.md` format

Every skill requires a `SKILL.md` with a YAML frontmatter header:

```markdown
---
name: your-skill-name
description: "When to use this skill. Claude reads this to decide whether to invoke it automatically."
---

# Your Skill

Skill content here — instructions, patterns, code examples, etc.
```

The `description` field is important: Claude uses it to decide when to load and apply the skill automatically during a conversation.

## Installing a Skill Locally

### Copy (one-time install)

```bash
cp -r django-crud-views ~/.claude/skills/
```

### Symlink (live development — changes in the repo are reflected immediately)

```bash
ln -s "$(pwd)/django-crud-views" ~/.claude/skills/django-crud-views
```

After installing, restart Claude Code or start a new session. Claude will automatically pick up installed skills from `~/.claude/skills/`.

### Verify installation

```bash
ls ~/.claude/skills/
```

You should see your skill directory listed.

## Developing a Skill

1. Create a directory named after your skill.
2. Add a `SKILL.md` with the YAML frontmatter and your skill content.
3. Add any supporting reference files under a `references/` subdirectory and link to them from `SKILL.md`.
4. Symlink to `~/.claude/skills/` as shown above, then test in a new Claude Code session.

Use the `skill-creator` skill inside Claude Code for guided help writing effective skill content:

```
/skill-creator
```
