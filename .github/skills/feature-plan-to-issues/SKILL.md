---
name: feature-plan-to-issues
description: 'Convert an approved feature implementation plan into a GitHub parent issue, component sub-issues, and formal blocked-issue relationships. Use when asked to create, break down, or link feature issues from a plan.'
argument-hint: 'Path to, or text of, an approved feature implementation plan'
---

# Create feature issues from a plan

Turn a supplied feature implementation plan into an approved GitHub issue
hierarchy. Do not use this skill to create issues from an incomplete idea.

## When to use this skill

Use this skill when the user asks to:

- create GitHub issues from an approved feature plan;
- break a planned feature into a parent issue and component issues; or
- create formal GitHub sub-issue or blocked-issue relationships.

## 1. Read the plan and establish the version context

1. Read the complete implementation plan and the relevant repository
   instructions, issue template, code, and tests.
2. Identify each deliverable, acceptance criterion, dependency, affected area,
   risk, and required validation.
3. Resolve the installed InvenioRDM version before finding external references.
   From the repository root, run:

   ```bash
   python3 .github/skills/feature-plan-to-issues/scripts/resolve_invenio_version.py .
   ```

   The command returns the exact `invenio-app-rdm` version and the lockfile or
   lockfiles that supplied it. Stop and report the error if the version is
   missing, not exact, or differs between applicable lockfiles. Do not manually
   select a version.
4. Find one or more InvenioRDM references for every proposed parent and child
   issue. Each reference must directly help implement that issue:
   - Link InvenioRDM GitHub source to the exact resolved release tag or commit,
     never to a branch such as `main` or `master`.
   - Link official InvenioRDM documentation from the matching release line.
     Verify that the selected version is visible in the link or its version
     selector. Do not use a `latest` documentation link as a substitute.
   - For each link, state in the issue why the linked source or documentation is
     relevant.
   - If an issue has no relevant, verified reference, stop and ask the user for
     direction. Do not invent a reference or create that issue without one.

## 2. Propose the breakdown

Break the feature into child issues that are independently actionable and small
enough to implement, review, and test in one focused pull request where
practical. Each child must have a clear outcome and acceptance criteria.

Identify which child issues block others. Depend on an issue only when its
completion is required before the dependent issue can be completed. Do not use
issue order, checklists, labels, or prose links as a substitute for a dependency.

Before drafting any issue title or body, present a Markdown list with **one
sentence for the parent issue and one sentence for each proposed child issue**.
Each sentence must state the issue scope and its direct prerequisite issues, or
state that it has no prerequisite. Do not add introductory or concluding prose
to this proposed-breakdown list.

For example:

- The parent issue coordinates the version-matched metadata feature and has no prerequisite.
- The vocabulary child issue adds the required vocabulary entries and has no prerequisite.
- The validation child issue enforces the entries and is blocked by the vocabulary child issue.

Wait for the user to approve or revise the breakdown. If the user requests a
revision, present a replacement list using the same one-sentence-per-issue
format. Do not draft issue text or create issues until the user approves the
breakdown.

## 3. Draft the approved issues

Write every title and body in ASD-STE100 Simple Technical English:

- Use short, direct sentences.
- Use one meaning for each technical term, define needed project-specific terms,
  and avoid idiom, ambiguity, and unnecessary abbreviations.
- Use concrete verbs and measurable acceptance criteria.
- Review the draft for these rules before showing it.

Do not claim formal ASD-STE100 dictionary compliance unless an approved
controlled-vocabulary checker is available.

Create one parent issue for the feature. Its body must contain:

- A short feature summary and intended outcome.
- Explicit in-scope and out-of-scope items.
- A delivery outline that names the component issues and their required order.
- An attribution of the form "This issue was written with AI assistence (<ASSISTANT NAME>:
  <MODEL NAME>)."

Create one child issue for each approved component. Use the structure in
`.github/ISSUE_TEMPLATE/feature-issue.md` for every child. Fill its PR and user
test-script fields with `Not yet available` when they are unknown. Include:

- A concise description of the component outcome and scope.
- At least one relevant, version-matched InvenioRDM reference, with why it
  applies.
- Testable acceptance criteria.
- Any prerequisite child issue in prose for clarity; the formal blocked-issue
  relationship remains required during creation.

Show the completed issue drafts to the user before creating the issues. Apply
requested edits and obtain explicit approval to create them.

## 4. Create and link the issues

Use `gh` against the current repository. Confirm that GitHub issue creation is
available and that the active authentication has the required permissions.

1. Create the parent issue and each approved child issue with `gh issue create`.
   Record each issue number, URL, and GraphQL node ID.
2. Use `gh api graphql` with the `addSubIssue` mutation for every child:
   `issueId` is the parent node ID and `subIssueId` is the child node ID.
3. Use `gh api graphql` with the `addBlockedBy` mutation for every dependency:
   `issueId` is the dependent child node ID and `blockingIssueId` is the
   prerequisite child node ID.
4. Do not replace either formal relationship with a Markdown task list, an
   issue mention, or a label.

## 5. Verify and report

Query GitHub after all mutations. Verify that:

- The parent contains exactly the intended child issue node IDs.
- Every child has the intended parent.
- Every dependent child has the intended formal blocking issue.
- The issue URLs, titles, and relationships match the approved breakdown.

Report the parent URL, all child URLs, and the verified dependency links. If
creation or a relationship mutation fails, report the completed and failed
operations with their issue numbers and URLs. Do not claim success, silently
ignore the failure, delete issues automatically, or attempt an unapproved
rollback.

## Deterministic work and judgment work

Use deterministic tooling for version resolution, GitHub issue creation,
GraphQL relationship mutations, and post-mutation relationship queries. Do not
delegate feature decomposition, reference relevance, ASD-STE100 wording, or
approval decisions to scripts; these require repository context and user
judgment.
