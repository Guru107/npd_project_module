# Release v1.2.1

## Release Date
2026-07-27

## Note on v1.2.0

This supersedes v1.2.0, which was tagged and then withdrawn. The repository had immutable releases enabled at the time, so deleting the v1.2.0 release left an immutable tag that could not be recreated or moved. v1.2.1 republishes the same work under a fresh version — there is no code difference between the two beyond this note and the version string.

## Overview

This release adds tooling tracking to the NPD Project Module: a customer-PO tooling order doctype with recovery tracking against payments and invoices, a recovery register report, and Project form integration.

Backward compatible — no breaking changes, and no data migration beyond `bench migrate`.

## What's Changed

### Features

- **Feat: Add tooling tracking to Project module** (`332cf47`) — PR #9
  - New `NPD Tooling` doctype: a customer-PO tooling order with child tool lines, so a part needing several tools (each possibly from a different supplier) is tracked as one order
  - Child tables: `NPD Tooling Item` (tool lines), `NPD Tooling Payment` (receipts), `NPD Tooling Invoice` (billing reference)
  - New `Tooling Recovery Register` report: recovery status, ageing from the customer PO date, and outstanding amounts across tooling orders
  - `create_tooling_item_group` patch seeds a `Tooling` Item Group so tool Items classify consistently

- **Feat: Allocate bulk customer payments across tooling POs** (`21565d9`)
  - A single customer receipt can be split across multiple tooling orders

- **Feat: Auto-derive tooling recovery from Sales Invoice allocations** (`c9ccefd`)
  - Recovery combines money paid against linked Sales Invoices with manual advance allocations, so it counts before a tax invoice exists and never double-counts a Payment Entry already applied to a linked invoice

- **Feat: Surface NPD Tooling in the Project Connections tab** (`c2d126f`, `d0c034f`, `4024d3f`) — PR #10
  - Project's Connections tab surfaces NPD Tooling via a custom `DocType Link` created in `after_install`
  - `NPD Tooling.project` matches the Project dashboard's default fieldname, so the connection count resolves automatically
  - An `after_migrate` hook re-asserts the link on every migrate

### Bug Fixes

- **Fix: Address review of Project→NPD Tooling connection** (`b2df1ad`)
  - The idempotency guard matches on `parent` + `link_doctype` rather than pinning `custom=1`, so a site carrying the same link as a standard row from fixtures no longer lists NPD Tooling twice in Connections
  - `remove_project_tooling_connection` on uninstall deletes only the `custom=1` rows this app creates
  - `PROJECT_TOOLING_LINK` is the single spelling of the connection's identity, shared by the install guard, the uninstall cleanup and the tests

- **Fix: Drop manual commit from after_migrate hook** (`a2e6f9c`)
  - Migrate invokes `after_migrate` hooks from its `@atomic` `post_schema_updates` phase, which already commits on success and rolls back on failure; the manual commit was redundant and partially defeated that rollback
  - Resolves the `frappe-manual-commit` blocking finding in the Linters workflow

### Tests

- **Test: Live end-to-end coverage for invoice-derived recovery** (`042ebcf`)
- Project connection tests clean up after themselves, leaving no `DocType Link` on the core Project doctype

### Code Quality

- **Style: Apply pre-commit ruff-format to test_npd_tooling** (`7b87e43`)

## Technical Details

### Why `after_migrate` and not a patch

`custom=1` protects a `DocType Link` from `Customize Form` rewrites, but not from a doctype re-import. When `project.json` changes (any ERPNext upgrade touching Project), Frappe reloads it via `import_file.delete_old_doc` → `delete_doc(..., for_reload=True)` → `delete_from_table`, which drops **every** `DocType Link` row parented to Project, custom ones included. Ordinary migrates skip the re-import on a hash match, so a naive "created → migrated → still there" check passes.

A one-shot patch cannot recover from this: once it is in the Patch Log it never runs again. `install/after_migrate.py` re-runs the idempotent helper after every migrate instead, and runs after both doctype sync and patches, so it sees the post-reload state.

### Uninstall

`before_uninstall` removes the `Tooling` Item Group (only when no Items reference it), the `Tooling Recovery Register` report, and the custom Project connection.

### Files Changed

- `npd_project_module/npd_project_module/doctype/npd_tooling/` (new)
- `npd_project_module/npd_project_module/doctype/npd_tooling_item/` (new)
- `npd_project_module/npd_project_module/doctype/npd_tooling_payment/` (new)
- `npd_project_module/npd_project_module/doctype/npd_tooling_invoice/` (new)
- `npd_project_module/npd_project_module/report/tooling_recovery_register/` (new)
- `npd_project_module/install/after_migrate.py` (new)
- `npd_project_module/patches/v1_0/create_tooling_item_group.py` (new)
- `npd_project_module/tests/test_npd_tooling.py` (new)
- `npd_project_module/install/after_install.py`
- `npd_project_module/uninstall/before_uninstall.py`
- `npd_project_module/hooks.py`
- `npd_project_module/public/js/project.js`
- `npd_project_module/patches.txt`
- `npd_project_module/tests/utils.py`
- `npd_project_module/utils/test_setup.py`

## Verification

- Full app suite **72/72** on Frappe/ERPNext v15
- `pre-commit run --all-files` clean; Linters and CI green on the release commit
- Connection recovery verified empirically: link deleted on a site whose Patch Log already contained the earlier one-shot patch, `bench migrate` restored it and it reappeared in the Project form's Connections

## Upgrading

```bash
bench --site <site> migrate
```

## Previous Release

- [v1.1.0](https://github.com/Guru107/npd_project_module/releases/tag/v1.1.0)

## Contributors

Guru107
