# Task Checklist

- [x] Implement Template Modifications
    - [x] Check/Run `modify_word_template.py` to tidy up the Word template structure (add branding, etc.) if not already done.
    - [x] Create `create_test_samples.py` with Multi-Item support logic.
- [ ] Verify Templates
    - [x] Run `create_test_samples.py`.
    - [ ] **Fix Bug**: Word file corruption (Duplicate SDT IDs).
        - [x] Modify `create_test_samples.py` to regenerate random IDs for copied SDTs.
        - [x] Re-run generation.
    - [x] **Debug**: File still corrupt.
        - [x] Run `verify_template_integrity.py` (Save simple copy).
        - [x] Modify `create_test_samples.py` to **Flatten SDTs** (Unwrap content) in cloned rows.
        - [x] Verify generated Word PDF (headers, multi-row).
    - [ ] Verify generated Excel (rows, calculations).
