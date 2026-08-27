# File Tree Planning Standard

Before any multi-file implementation, record the intended file tree in the task specification. The tree must list each new, modified, or deleted path, its purpose, responsible component, dependency direction, and validation target. Paths outside the confirmed repository root are not permitted.

```text
project/
├── source-or-module.py       # implementation; unit-test target
├── tests/test-feature.py     # regression coverage; focused test command
└── docs/feature.md           # user/operator contract; policy check
```

The worker must compare the planned tree with the actual change set before completion. Unplanned files, generated artifacts, credentials, caches, and unrelated modifications require removal or explicit review. The tree is planning metadata only; it must not contain secret values or private account data.
