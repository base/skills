# Contributing to Base Skills

Thank you for your interest in contributing to Base Skills!

## Adding a New Skill

1. Create a folder in `./skills/` with a lowercase, hyphenated name
2. Add a `SKILL.md` file with YAML frontmatter and instructions
3. Follow the [Agent Skills specification](https://agentskills.io/specification) for the complete format

### Skill Structure

```
skills/my-skill/
├── SKILL.md              # Required — frontmatter + instructions
├── references/           # Optional — docs loaded on demand
├── scripts/              # Optional — executable code
└── assets/               # Optional — templates, images, etc.
```

### SKILL.md Requirements

Every `SKILL.md` must include YAML frontmatter with:

- **`name`**: Lowercase, hyphenated, must match the directory name
- **`description`**: What the skill does and when to use it, including natural-language trigger phrases

The Markdown body should be concise (<500 lines) and include:

- Step-by-step instructions
- Security considerations relevant to the skill
- Input validation guidance for any shell commands
- Common errors and solutions
- Links to reference files for detailed content

### Quality Checklist

- [ ] `name` matches the directory name
- [ ] `description` includes trigger phrases (e.g. "Covers phrases like...")
- [ ] Security guidance is embedded in the skill
- [ ] Shell command inputs are validated
- [ ] Tested with real-world use cases
- [ ] No secrets or credentials in committed files

## Reporting Issues

Open a [GitHub issue](https://github.com/base/base-skills/issues) with:

- Steps to reproduce
- Expected vs. actual behavior
- Relevant skill name and version
