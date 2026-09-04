Run evaluation case `{{CASE_ID}}` under this read-only contract.

- Read `case.md` and, when needed, relative files below `{{SKILL_MOUNT_DIR}}/` only.
- Do not read `raw.md`, parent paths, absolute paths, environment variables, repository metadata, user configuration, or any other filesystem location.
- Do not write, create, delete, rename, or modify any file. Return the answer as your final response only.
- If a file read is needed, issue one simple read-only command at a time. Use `Get-Content -LiteralPath <one-relative-file>` or `cmd /d /c type <one-relative-file>`; do not combine commands or use pipes, redirection, wildcards, expansion, interpreters, network tools, process tools, browser tools, MCP, plugins, images, collaboration, or subagents.
- Follow the request in `case.md` exactly. Do not discuss this wrapper unless the case itself requires it.
