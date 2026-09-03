# Wiki Schema

This wiki uses the following conventions:

## Categories

- **architecture**: System design, high-level structure, architectural decisions
- **decisions**: Architecture Decision Records (ADRs), design choices
- **patterns**: Reusable patterns, best practices, conventions
- **troubleshooting**: General content
- **environment**: General content
- **onboarding**: General content

## Page Format

Each page has YAML frontmatter:

```yaml
---
page_id: wp-{timestamp}-{uuid8}
title: Page Title
category: category_name
tags: [tag1, tag2]
created: ISO timestamp
updated: ISO timestamp
linked_sessions: [session_id_1, session_id_2]
---
```

## Conventions

1. One concept per page
2. Link related pages using markdown links
3. Tag liberally for discoverability
4. Sessions auto-generate pages in `sessions/`
