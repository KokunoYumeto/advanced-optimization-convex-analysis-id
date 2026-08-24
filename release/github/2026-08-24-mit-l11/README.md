# MIT L11 GitHub public-byte verification

The content verifier is bound only at runtime to an exact commit, parent, and
changed-file count. It reads the immutable public patch and every changed raw
file, compares those bytes with the local commit, and then writes the sanitized
receipt. It does not contact upstream maintainers.

```text
python verify_github_public.py <commit> <parent> <changed-file-count>
```

After the narrow publication-evidence commit is pushed, verify that commit in
the same way:

```text
python verify_github_evidence_public.py <commit> <parent> <changed-file-count>
```

The verified content boundary is complete MIT Lecture 7, source PDF pages
86–97; page 98 is explicitly not claimed. Zenodo publication and its anonymous
readback are recorded separately in the existing concept lineage. This MIT
material is the separately licensed companion, while Habring
arXiv:2607.11664v1 remains the canonical editable-source spine.

