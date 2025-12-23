### Npd Project Module

Customization on top of existing Project Module in ERPNext to support NPD (New Product Development) process in a manufacturing company.

## Features

- **Part-Based Task Management**: Link tasks to specific parts (items) within a project
- **Iteration Support**: Track multiple iterations of development for each part
- **Automatic Task Generation**: Generate 18 sequential NPD tasks for each part and iteration
- **Task Dependencies**: Enforce sequential task completion within iterations
- **Matrix Reports**: Visualize part-stage completion status across iterations
- **Project Templates**: Use "NPD Template" to define task sequences

## Installation

### Prerequisites

- Frappe Framework installed
- ERPNext installed
- Bench CLI configured

### Step 1: Get the App

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch develop
```

### Step 2: Install the App

```bash
bench --site [your-site] install-app npd_project_module
```

**Example:**
```bash
bench --site development.localhost install-app npd_project_module
```

### Step 3: Verify Installation

After installation, verify that:

1. **Custom Fields Created:**
   - Task doctype: `part_number`, `iteration_number`
   - Project doctype: `part_numbers` (child table)
   - Item doctype: `project`

2. **NPD Template Created:**
   - Go to: Project > Project Template
   - Look for "NPD Template" with 18 tasks

3. **Report Available:**
   - Go to: Reports > Part Stage Matrix

### Idempotency

The installation is **idempotent**, meaning:
- ✅ You can run installation multiple times without errors
- ✅ Existing custom fields won't be duplicated
- ✅ The app checks for existing resources before creating them
- ✅ NPD Template is only created/updated if needed

**Test idempotency:**
```bash
# Run installation multiple times
bench --site [your-site] install-app npd_project_module
bench --site [your-site] install-app npd_project_module  # Should show "already installed"
```

## Uninstallation

### Step 1: Backup (Recommended)

Before uninstalling, backup your site:

```bash
bench --site [your-site] backup --with-files
```

### Step 2: Uninstall the App

```bash
bench --site [your-site] uninstall-app npd_project_module --yes --no-backup
```

**Example:**
```bash
bench --site development.localhost uninstall-app npd_project_module --yes --no-backup
```

**Note:** Use `--no-backup` only if you're sure you don't need a backup. For production, always backup first.

### Step 3: Verify Uninstallation

After uninstallation, verify that:

1. ✅ Custom fields removed from Task, Project, and Item doctypes
2. ✅ NPD Template removed
3. ✅ Part Stage Matrix report removed
4. ✅ Project Part Number doctype removed
5. ✅ No broken references or orphaned data

### What Gets Removed

The uninstallation process removes:

- **Custom Fields:**
  - Task: `part_number`, `iteration_number`
  - Project: `part_numbers_section`, `part_numbers`
  - Item: `project`

- **Templates:**
  - Project Template: "NPD Template" (and its template tasks)

- **Reports:**
  - Part Stage Matrix report

- **DocTypes:**
  - Project Part Number (child table)

- **Hooks:**
  - All registered hooks are automatically removed by Frappe

### Data Preservation

**⚠️ Warning:** Uninstallation will:
- Remove all custom fields and their data
- Remove the Project Part Number child table and its data
- Remove NPD Template and template tasks
- Remove custom reports

**Important:** If you have existing projects with part numbers and tasks, uninstalling will remove this data. Always backup your site before uninstalling.

## Troubleshooting

### Custom Fields Not Visible

If custom fields don't appear after installation:

1. **Clear cache:**
   ```bash
   bench --site [your-site] clear-cache
   ```

2. **Reload the page** in browser (Ctrl+Shift+R or Cmd+Shift+R)

3. **Check custom fields:**
   - Go to: Setup > Customize Form
   - Select "Task" doctype - Look for "Part Number" and "Iteration Number" fields
   - Select "Item" doctype - Look for "Project" field

### Installation Fails

If installation fails:

1. Check the error message in terminal
2. Ensure ERPNext is installed: `bench --site [your-site] list-apps`
3. Check Frappe version compatibility
4. Review logs: `bench --site [your-site] logs`

### Uninstallation Fails

If uninstallation fails:

1. Check the error message in terminal
2. Manually remove custom fields if needed:
   - Go to: Setup > Customize Form
   - Remove custom fields manually
3. Check for dependencies:
   - Ensure no active projects are using the custom fields
   - Remove or update dependent configurations

### NPD Template Not Created

If NPD Template is not created:

1. Check if template already exists with a different name
2. Run template creation manually:
   ```bash
   bench --site [your-site] console
   ```
   Then in console:
   ```python
   from npd_project_module.install.after_install import create_npd_template
   create_npd_template()
   frappe.db.commit()
   ```

## Reinstallation

After uninstallation, you can reinstall the app:

```bash
bench --site [your-site] install-app npd_project_module
```

The reinstallation will:
- ✅ Create all custom fields again
- ✅ Create NPD Template again
- ✅ Set up all configurations

**Note:** Any data that was removed during uninstallation will not be restored.

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/npd_project_module
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### License

mit
