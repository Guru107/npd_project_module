# NPD Project Module - Installation Guide

## Overview

The NPD Project Module extends ERPNext's Project module to support part-based iteration management for New Product Development (NPD) processes.

## Prerequisites

- Frappe/ERPNext installation
- ERPNext app must be installed
- Bench environment properly configured

## Installation

### Step 1: Install the App

```bash
cd /path/to/frappe-bench
bench --site [your-site] install-app npd_project_module
```

**Example:**
```bash
cd /Users/gurudattkulkarni/Workspace/bench_apps/frappe-bench
bench --site development.localhost install-app npd_project_module
```

### Step 2: Clear Cache

```bash
bench --site [your-site] clear-cache
```

### Step 3: Verify Installation

1. **Check Task Form:**
   - Navigate to: Projects > Task
   - Open any task or create a new one
   - Verify fields are visible:
     - Part Number (after Project field)
     - Iteration Number (read-only, after Part Number)

2. **Check Project Form:**
   - Navigate to: Projects > Project
   - Open any project or create a new one
   - Verify section is visible:
     - Part Numbers (section)
     - Part Numbers table with columns:
       - Part Number (editable)
       - Iteration Number (read-only, default 0)

3. **Check Item Form:**
   - Navigate to: Stock > Item
   - Open any item or create a new one
   - Verify field is visible:
     - Project (Link to Project, after Item Name)

4. **Check Task List View:**
   - Navigate to: Projects > Task List
   - Verify columns are visible:
     - Part Number
     - Iteration Number
   - Verify filters are available in the filter dropdown

## What Gets Installed

### Custom Fields

**Task DocType:**
- `part_number` (Link to Item) - In list view, in standard filter, in global search
- `iteration_number` (Int) - Read-only, default 0, in list view, in standard filter

**Project DocType:**
- `part_numbers_section` (Section Break)
- `part_numbers` (Table) - Links to Project Part Number child table

**Item DocType:**
- `project` (Link to Project) - In list view, in standard filter, in global search

### DocTypes

- `Project Part Number` - Child table for storing part numbers and iteration numbers

### Hooks

- `after_install` - Creates custom fields and configurations
- `before_uninstall` - Cleans up custom fields and configurations

## Idempotency

The installation is idempotent, meaning:
- You can run installation multiple times without errors
- Existing custom fields won't be duplicated
- The app checks for existing resources before creating them

## Uninstallation

### Step 1: Uninstall the App

```bash
bench --site [your-site] uninstall-app npd_project_module --yes --no-backup
```

**Example:**
```bash
bench --site development.localhost uninstall-app npd_project_module --yes --no-backup
```

### Step 2: Verify Cleanup

After uninstallation:
- ✅ Custom fields removed from Task, Project, and Item doctypes
- ✅ Project Part Number doctype removed
- ✅ Database table dropped
- ✅ Module definition removed
- ✅ Desktop icons removed
- ✅ No orphaned data or broken references

### Data Preservation

**Note:** Uninstallation will:
- Remove all custom fields
- Remove the Project Part Number doctype and its data
- Remove any tasks that were created with part numbers

**Warning:** If you have existing projects with part numbers and tasks, uninstalling will remove this data. Make sure to backup your site before uninstalling.

## Troubleshooting

### Custom Fields Not Visible

If custom fields don't appear after installation:

1. Clear cache:
   ```bash
   bench --site [your-site] clear-cache
   ```

2. Reload the page in browser (Ctrl+Shift+R or Cmd+Shift+R)

3. Check if custom fields were created:
   - Go to: Setup > Customize Form
   - Select "Task" doctype - Look for "Part Number" and "Iteration Number" fields
   - Select "Item" doctype - Look for "Project" field

### Installation Fails

If installation fails:

1. Check the error message in terminal
2. Ensure ERPNext is installed: `bench --site [your-site] list-apps`
3. Try reinstalling:
   ```bash
   bench --site [your-site] uninstall-app npd_project_module --yes --no-backup
   bench --site [your-site] install-app npd_project_module
   ```

### Uninstallation Fails

If uninstallation fails:

1. Check the error message
2. Manually remove custom fields via Customize Form
3. Try uninstalling again

## Testing Installation/Uninstallation

To test the idempotent installation:

```bash
# Install
bench --site development.localhost install-app npd_project_module

# Uninstall
bench --site development.localhost uninstall-app npd_project_module --yes --no-backup

# Reinstall
bench --site development.localhost install-app npd_project_module

# Verify no errors and fields are created correctly
```

## Next Steps

After successful installation, you can:
1. Create projects with part numbers
2. Add parts (Items) to the Part Numbers table in projects
3. Link items to projects via the Project field in Item master
4. (Future) Automatically generate tasks for each part
5. (Future) Create iterations for parts
6. (Future) View part-stage matrix reports

