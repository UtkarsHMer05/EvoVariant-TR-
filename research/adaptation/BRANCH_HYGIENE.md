# Adaptation Branch Hygiene

## Scope

This audit covers the branch-only changes present when the post-hoc adaptation
work began. It does not modify `main` or the frozen baseline tag.

## Starting state

| Item | Value |
|---|---|
| Branch | `research/posthoc-foundation-adaptation` |
| Starting branch HEAD | `0a9a94f999a09acb933b7663ff588919a3a4a12d` |
| `main` HEAD | `30b515314d5f8c8be7c83c96b1f576fb7225c869` |
| Frozen tag | `evovariant-tr-baseline-v1` -> `1003bc5a20973145e0e096ff7b0f3424045d07e6` |
| Starting worktree | clean |
| Branch-only commit | `0a9a94f` (`starting`) |

## Branch-only audit

The branch-only commit added 58 files and no adaptation source, protocol, or
test code. Every path was classified before cleanup.

### Local Modal skill carryover: delete

These 50 files are a bundled `.agents/skills/modal` documentation mirror. They
are local agent tooling, not repository adaptation work, and are absent from
`main`:

```text
.agents/skills/modal/SKILL.md
.agents/skills/modal/references/api/{App,Client,CloudBucketMount,Cls,Cron,Dict,Environment,Error,FilePatternMatcher,Function,FunctionCall,Image,NetworkFileSystem,Period,Probe,Proxy,Queue,Retries,Sandbox,SandboxSnapshot,Secret,Server,Tunnel,Volume,Workspace,asgi_app,batched,billing,concurrent,config,container_process,current_input_id,enable_output,enter,exception,exit,fastapi_endpoint,file_io,forward,interact,intro,io_streams,is_local,method,parameter,types,web_server,wsgi_app}.md
```

The brace expression above is a compact inventory of the 49 API reference
files; the recorded Git name-status audit confirmed each concrete path.

### Historical paid Evo2 approval carryover: delete

These five approval records belong to the earlier `ML-DEV-BUDGETED-001` paid
Modal/Evo2 work, not this study's `$0` free-Colab contract:

```text
artifacts/approvals/formal_64_preflight_20260921.json
artifacts/approvals/formal_phase6_resume_20260922.json
artifacts/approvals/formal_phase7_continuation_20260922.json
artifacts/approvals/formal_phase7_representation_20260922.json
artifacts/approvals/overnight_completion_20260922.json
```

### Historical paid Evo2 Phase-6 carryover: delete

These three records document a prior paid/partial Evo2 run and are not
adaptation evidence:

```text
artifacts/phase6/formal_budgeted_preflight_gate_overnight_20260922.json
artifacts/phase6/formal_phase6_resume_preflight_20260922.json
artifacts/phase6/phase6_formal_evo2_20260921_full_overnight_20260922_partial.json
```

## Cleanup action

Delete only the 58 classified branch-only paths in a normal cleanup commit.
Do not rewrite history, modify `main`, modify `evovariant-tr-baseline-v1`,
or reuse the old paid approvals for the new study. The old files remain
recoverable in Git history if provenance review later requires them.

## Acceptance

After the cleanup commit, verify:

```text
correct branch = true
main unchanged = true
baseline tag unchanged = true
carryover audited = true
adaptation branch clean = true
```

The final commit and verification outputs are recorded below after cleanup.

## Final verification

Cleanup commit: `63cad2d` (`chore: clean adaptation branch baseline`).

```text
correct branch = true
main unchanged = true
baseline tag unchanged = true
carryover audited = true
adaptation branch worktree clean = true
net branch-only content after cleanup = this audit document only
```
