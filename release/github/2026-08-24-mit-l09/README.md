# MIT L09 GitHub public-byte verification

These templates are intentionally unbound. They perform no work on import and
contain no placeholder commit masquerading as final evidence. After a narrow
L09 content commit has been pushed, run the content verifier with its exact
40-hex commit, exact 40-hex parent, and exact changed-file count:

```text
python verify_github_public.py <commit> <parent> <changed-file-count>
```

If a later narrow commit adds only publication/control evidence, use the same
argument pattern with `verify_github_evidence_public.py`. Each command checks
the local immutable commit and parent, reads the public patch identity, compares
every changed file byte-for-byte against the public raw URL, and only then
writes its sanitized receipt. The scripts do not contact upstream maintainers.

Scope wording is bounded to complete MIT Lecture 5, source PDF pages 50–63;
page 64 is explicitly not claimed. The Zenodo checkpoint remains a separate
additive transaction in the existing concept lineage.
