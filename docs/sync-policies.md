# Synchronisation policies

## Source of Truth Principle

**The repository is the only canonical source of truth.** Everything
else — runtime skill files, deployed scripts, generated docs —
is a *derivative*.

Consequence:

    repo  ─── is canonical
    runtime, scripts, deployed artifacts  ─── are derivatives

This is not a preference; it is the project's structural commitment.
Sync flows must respect it:

| Direction | Status |
|---|---|
| `repo -> origin` (push)               | normal |
| `repo -> runtime` (deploy)            | normal |
| `runtime -> repo` (back-fill)         | **exception, never default** |

## Why `runtime -> repo` is exceptional

The runtime is a deployment artifact. It is reachable from disk but
not under the same review discipline as the repo. Changes made on a
running agent host are typically:

- local notes that were never meant to be in the repo,
- political edits under time pressure (during an active session
  with a human in the loop),
- housekeeping that is convenient but not appropriate as
  canonical documentation.

Allowing `runtime -> repo` as a normal flow **leaks these into the
official record** without the discipline that the repo enforces
(commits with messages, tests, CI, code review).

**Memory aim**: future readers should remember the *principle*
("repo is canonical; runtime is derived"), not just the *flow*
("we usually copy files from X to Y"). The flow is a consequence;
the principle is the source.

## When `runtime -> repo` does happen

In the 2026-07-24 session this happened exactly once: the runtime
had accumulated the "Measurement planes" section from CSI.md /
PLANES.md, and the repo was behind. After backing up the runtime
copy, the section was copied into `integrations/hermes/SKILL.md`
directly.

That is the only acceptable pattern:

1. Accept the runtime contents as **evidence**, not authority.
2. Pull the contents into the repo through the normal edit flow
   (`patch` / `write_file`), under the same review discipline as
   any other change.
3. Commit with a message that explicitly cites the runtime back-fill.
4. After the commit, runtime and repo are byte-identical again via
   `repo -> runtime`.

## Operational invariants

The repo MUST always:
- carry the canonical version of every doc the runtime depends on;
- pass `pytest` before any runtime sync;
- have its working tree clean before any push that follows a
  runtime back-fill.

The runtime MUST always:
- be either byte-identical to the repo version of the same file,
  or be a previous version with no pending edits;
- never be edited as a substitute for editing the repo.

If a runtime edit ever appears necessary, the action is:

    Do the edit in the repo.
    Commit.
    Sync repo -> runtime.

Not the other way.