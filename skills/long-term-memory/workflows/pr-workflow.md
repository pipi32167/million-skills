# PR 工作流

- 本地代码变更完成后，从当前分支切出一个功能分支，命名格式为 `{type}-{issue-id}-{short-description}`，其中 `type` 可选 `feature` / `refactor` / `bugfix`，`issue-id` 是对应的 Linear 或内部工单号，`short-description` 用英文短横线连接。
- 示例：`feat-4T-1234-add-skill-system`、`refactor-4T-5678-extract-auth-module`、`bugfix-4T-9999-fix-memory-leak`。
- 切分支后，使用 `git-commit` skill 生成符合 Conventional Commits 规范的提交信息，确保提交历史清晰可追溯。
- 提交完成后，将本地分支推送到 origin：`git push -u origin <branch-name>`，确保远程存在同名分支。
- 使用 GitLab API 创建 Merge Request（MR），调用时需读取 `~/.agents/skills/long-term-memory/.secret-memory` 中的 GitLab access token 进行认证。
- 创建 MR 时，标题应包含 issue-id 和简洁描述，描述区填写变更摘要、测试覆盖情况以及 Reviewer 指派信息。
- MR 创建后，在 Linear 或对应工单系统中关联 MR 链接，保持工作流闭环。
- glab 默认配置的 `agent` token 只有 `read_api`，`glab mr create` 会报 `403 insufficient_scope`；改用有 `api` scope 的 token 并以 `GITLAB_TOKEN=...` 环境变量传入，即可非交互创建（`--title` + `--description "$(cat body.md)"` + `--yes`）。
