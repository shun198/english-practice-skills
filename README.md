# english-practice-skills

Engineer-focused English practice skills inspired by
`shun198/shun198-skills`.

## Skills

- `business-it-english-conversation`: English conversation practice for
  engineers working in code reviews, Issues, Slack, meetings, standups, and
  incident or release discussions.

## Agent-Specific Copies

- Codex: `codex/skills/business-it-english-conversation.md`
- Claude: `claude/skills/business-it-english-conversation.md`
- Cursor: `cursor/skills/shun198-business-it-english-conversation/SKILL.md`

## Source Materials

PDF source materials must stay in Google Drive and must not be committed to this
repository. Markdown source notes should also be referenced from Google Drive
when possible, especially if they originate in ChatGPT Projects.

Current Drive reference:

- Engineer English source PDF
  - Keep the actual Google Drive URL in a local ignored file, not in Git.
  - Suggested local path:
    `skills/business-it-english-conversation/references/private-sources.md`

## Install Locally

Copy or symlink the skill directory into your Codex skills directory:

```bash
ln -s "$PWD/skills/business-it-english-conversation" \
  "${CODEX_HOME:-$HOME/.codex}/skills/business-it-english-conversation"
```
