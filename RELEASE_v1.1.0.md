# Release v1.1.0

## Release Date
2026-03-18

## Overview

This release includes bug fixes and improvements to make the NPD Project Module tests more robust and reliable.

## What's Changed

### Bug Fixes

- **Fix: Implement robust test setup to prevent flaky tests** (`0b0275b`)
  - Created `test_setup.py` with `before_tests()` hook for ERPNext fixtures
  - Enabled `before_tests` hook in `hooks.py` to run during test initialization
  - Updated `tests/utils.py` to handle ERPNext warehouse naming (company suffix)
  - Updated CI workflow to run ERPNext fixtures installer
  - Resolves: `LinkValidationError` when creating test warehouses due to missing "All Warehouses" root warehouse

- **Fix: Handle warehouse naming with company suffix** (`ce0b8fd`, `b3ac8ec`)
  - Fixed warehouse existence checks to handle ERPNext's company suffix pattern (e.g., "All Warehouses - _TC")
  - Prevents duplicate entry errors during test runs

- **Fix: Add nosemgrep comment for frappe.db.commit()** (`24927f7`)
  - Added semgrep exclusion for manual database commit required to persist test fixtures

### Code Quality

- **Style: Fix ruff formatting in test_setup.py** (`8d7f3f2`)
- **Lint changes** (`78589e5`)

### Maintenance

- **Chore: Remove claude workflows and add AGENT.md** (`3d78e06`)
  - Removed claude-code-review.yml workflow
  - Removed claude.yml workflow
  - Added AGENT.md placeholder file

### Feature Updates

- **Sequence change in NPD Template** (`9a6c9f6`)
- **Remove duplicate** (`8c432e7`)
- **Fix docname in test** (`b3ac8ec`)
- **Remove item name** (`2df2c12`)
- **Add warehouse fixture** (`69c41e2`)

## Technical Details

### Test Infrastructure Improvements

1. **New `before_tests()` hook** ensures proper ERPNext fixtures are installed before tests run
2. **Robust warehouse detection** uses `LIKE` queries instead of exact name matches to handle company suffixes
3. **CI workflow updated** to run `erpnext.setup.setup_wizard.operations.install_fixtures.install` during setup

### Files Changed

- `npd_project_module/utils/test_setup.py` (new)
- `npd_project_module/hooks.py`
- `npd_project_module/tests/utils.py`
- `.github/workflows/ci.yml`

## Previous Release

- [v1.0.0](https://github.com/Guru107/npd_project_module/releases/tag/v1.0.0)

## Contributors

Guru107
