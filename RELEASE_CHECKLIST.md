# Release Checklist

Use this checklist before creating a public GitHub Release.

## 1. Scope and Version

- [ ] Confirm release scope (major/minor/patch)
- [ ] Select SemVer tag (example: `v2.2.0`)
- [ ] Confirm changelog entries are complete

## 2. Validation

- [ ] Confirm README setup/config sections match workflow implementation
- [ ] Confirm secrets/variables in docs match `.github/workflows/*.yml`
- [ ] Confirm workflow links and badges resolve
- [ ] Run required tests/checks for release branch

## 3. Release Notes

- [ ] Summarize key changes and migration notes
- [ ] Highlight security-impacting fixes
- [ ] Include known limitations (if any)

## 4. Git and GitHub

- [ ] Create annotated tag
- [ ] Push tag to origin
- [ ] Create GitHub Release from the tag
- [ ] Attach release notes and reference `CHANGELOG.md`

## 5. Post-Release

- [ ] Verify release page visibility
- [ ] Share release announcement
- [ ] Monitor issues for regressions