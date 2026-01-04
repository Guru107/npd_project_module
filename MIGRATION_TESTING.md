# Migration Testing Guide

## Testing Custom Fields and Child Table Setup

### Prerequisites
- Ensure you're in the frappe-bench directory
- Ensure the site is running

### Step 1: Run Migration
```bash
cd /Users/gurudattkulkarni/Workspace/bench_apps/frappe-bench
bench --site development.localhost migrate
```

### Step 2: Verify Custom Fields in Task Doctype
1. Open Frappe/ERPNext in browser
2. Navigate to Task List (Projects > Task)
3. Open any existing task or create a new one
4. Verify the following fields are visible:
   - **Part Number** (Data field, after Project field)
   - **Iteration Number** (Int field, read-only, after Part Number field)

### Step 3: Verify Child Table in Project Doctype
1. Navigate to Project List (Projects > Project)
2. Open any existing project or create a new one
3. Verify the following section is visible:
   - **Part Numbers** section
   - **Part Numbers** table with columns:
     - Part Number (editable)
     - Iteration Number (read-only, default 0)

### Step 4: Test Idempotency
Run the migration again to ensure no duplicates are created:
```bash
bench --site npd.local migrate
```

Check that no errors occur and no duplicate fields are created.

### Expected Results
- ✅ Migration completes without errors
- ✅ Custom fields appear in Task form
- ✅ Part Numbers table appears in Project form
- ✅ Fields are in correct positions (after specified fields)
- ✅ Iteration Number is read-only
- ✅ Re-running migration doesn't create duplicates

### Troubleshooting

If migration fails:
1. Check the error message in terminal
2. Verify all Python files have correct syntax
3. Ensure all __init__.py files exist in directory structure
4. Check patches.txt has correct module paths

If fields don't appear:
1. Clear cache: `bench --site npd.local clear-cache`
2. Reload the page in browser (Ctrl+Shift+R)
3. Check if custom fields were created: Go to Customize Form and search for Task/Project

### Rollback (if needed)
To remove custom fields manually:
1. Go to Customize Form
2. Select "Task" doctype
3. Find and remove "Part Number" and "Iteration Number" fields
4. Select "Project" doctype
5. Find and remove "Part Numbers" section and table field

### Next Steps
After successful migration testing, proceed to:
- Task 2.0: Implement Automatic Task Generation with Dependencies

