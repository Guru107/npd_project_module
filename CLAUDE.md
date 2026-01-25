# CLAUDE.md - Working with NPD Project Module

This document provides context for Claude Code (and human developers) when working with this codebase.

---

## 1. Project Documentation

### Overview

**NPD Project Module** is a Frappe/ERPNext custom application that extends the standard Project Module to support New Product Development (NPD) processes in manufacturing companies.

### Purpose

This app enables structured tracking of multi-part product development through multiple iterations, with automated task generation and dependency management.

### Key Features

1. **Part-Based Task Management**: Link tasks to specific parts (items) within a project
2. **Iteration Support**: Track multiple iterations of development for each part
3. **Automatic Task Generation**: Generate 18 sequential NPD tasks for each part and iteration
4. **Task Dependencies**: Enforce sequential task completion within iterations
5. **Matrix Reports**: Visualize part-stage completion status across iterations
6. **Project Templates**: Use "NPD Template" to define task sequences

### Technology Stack

- **Framework**: Frappe Framework (v15)
- **ERP**: ERPNext (v15)
- **Language**: Python 3.10+
- **Frontend**: Frappe's JavaScript framework
- **Build System**: flit_core
- **Code Quality**: ruff, eslint, prettier, pre-commit

### Architecture

```
npd_project_module/
├── npd_project_module/        # Main module directory
│   ├── doctype/               # Custom DocTypes (if any)
│   └── ...
├── install/                    # Installation scripts
│   └── after_install.py       # Post-install setup
├── uninstall/                  # Cleanup scripts
├── utils/                      # Core business logic
│   ├── task_generation.py     # Task creation logic
│   ├── project_utils.py       # Project helpers
│   └── task_utils.py          # Task helpers
├── tests/                      # Test suite
├── config/                     # App configuration
├── hooks.py                    # Frappe hooks registration
└── patches/                    # Database migrations
```

### Custom Fields Added

**Task DocType:**
- `part_number`: Links task to a specific part/item
- `iteration_number`: Tracks which iteration the task belongs to

**Project DocType:**
- `part_numbers_section`: Section break for parts
- `part_numbers`: Child table of Project Part Numbers

**Item DocType:**
- `project`: Links item to a project

### NPD Template

The app creates an "NPD Template" with 18 predefined tasks representing stages in the NPD process. These tasks are automatically generated for each part-iteration combination.

### Reports

- **Part Stage Matrix**: Visualizes completion status of parts across different stages and iterations

---

## 2. Guidelines for Working with Claude Code

### Getting Started

When working with this codebase, Claude Code can help you:

- Understand existing code and architecture
- Add new features or modify existing ones
- Debug issues and fix bugs
- Write and run tests
- Generate documentation
- Refactor code while maintaining functionality

### Effective Prompts

**Good Examples:**
- "Show me how task generation works in utils/task_generation.py"
- "Add a new custom field to track task priority"
- "Fix the failing test in test_iteration_management.py"
- "Explain the dependency logic between tasks"
- "Add validation to ensure iteration numbers are sequential"

**What to Avoid:**
- Vague requests like "make it better"
- Requests without context about which part of the app
- Asking to rewrite everything without specific goals

### File Navigation Tips

**Key Files to Reference:**
- `hooks.py` - Entry point for understanding app integrations
- `utils/task_generation.py` - Core task creation logic
- `install/after_install.py` - Setup and initialization
- `tests/` - Examples of how features work
- `README.md` - User-facing documentation

### Testing Approach

Before making changes:
1. Read existing tests to understand expected behavior
2. Run tests to ensure baseline works
3. Make changes incrementally
4. Add tests for new functionality
5. Verify all tests pass

### Common Tasks

**Adding a Custom Field:**
1. Review `install/after_install.py` to see existing field creation
2. Add new field definition following the same pattern
3. Update uninstall script to remove the field
4. Test idempotency of installation

**Modifying Task Generation:**
1. Review `utils/task_generation.py`
2. Understand the 18-task template structure
3. Make changes while maintaining backward compatibility
4. Update tests in `tests/test_task_generation.py`

**Adding a New Report:**
1. Study existing report structure (if any)
2. Follow Frappe's report creation patterns
3. Add report to app configuration
4. Add cleanup to uninstall script

---

## 3. Project-Specific Instructions & Context

### Coding Standards

This project uses **ruff** for Python linting and formatting with the following configuration:

- **Line length**: 110 characters
- **Python version**: 3.10+
- **Indentation**: Tabs (as per ERPNext standards)
- **Quote style**: Double quotes
- **Pre-commit hooks**: Enabled (must be installed)

### Pre-commit Setup

Before making commits, install pre-commit:

```bash
cd apps/npd_project_module
pre-commit install
```

This ensures code is automatically formatted and linted before commits.

### Important Conventions

1. **Idempotency**: Installation and uninstallation must be idempotent
   - Check if resources exist before creating
   - Safe to run multiple times
   - No duplicate custom fields

2. **Custom Fields Naming**:
   - Use snake_case for field names
   - Prefix with descriptive context (e.g., `part_number`, not just `number`)

3. **Error Handling**:
   - Use Frappe's `frappe.throw()` for user-facing errors
   - Log errors appropriately
   - Validate inputs at API boundaries

4. **Testing**:
   - Write tests for all new features
   - Use the test utilities in `tests/utils.py`
   - Follow existing test patterns
   - Ensure tests are isolated and don't depend on external state

### Development Workflow

1. **Setup**:
   ```bash
   bench get-app https://github.com/[repo] --branch develop
   bench --site [site-name] install-app npd_project_module
   ```

2. **Development**:
   - Make changes in feature branches
   - Follow git-flow: branch from `develop`, PR back to `develop`
   - Main branch: `develop`

3. **Testing**:
   ```bash
   bench --site [site-name] run-tests --app npd_project_module
   ```

4. **Linting**:
   ```bash
   ruff check .
   ruff format .
   ```

### Current Branch

- **Active Branch**: `feature/iteration-transperancy`
- **Base Branch**: `develop`
- **Status**: Clean working tree

### Key Dependencies

- **Frappe Framework**: ~15.0.0 (managed by bench)
- **ERPNext**: Required for Project and Item doctypes

### Known Limitations

1. Tasks must be completed sequentially within an iteration
2. Template is hardcoded to 18 tasks
3. Custom fields are added to core ERPNext doctypes

### Testing Notes

The `tests/` directory contains comprehensive test coverage:

- `test_task_generation.py` - Task creation logic
- `test_project_utils.py` - Project utilities
- `test_task_utils.py` - Task utilities
- `test_iteration_management.py` - Iteration tracking
- `test_integration.py` - End-to-end workflows
- `test_part_stage_matrix.py` - Report functionality

### When Modifying Code

**Always consider:**
- Will this break existing projects?
- Is the change backward compatible?
- Do custom fields need migration?
- Does uninstall need updating?
- Are there tests to verify behavior?

### Debugging Tips

1. **Check Frappe logs**:
   ```bash
   bench --site [site-name] logs
   ```

2. **Use Frappe console**:
   ```bash
   bench --site [site-name] console
   ```

3. **Clear cache after changes**:
   ```bash
   bench --site [site-name] clear-cache
   ```

4. **Rebuild after JS/CSS changes**:
   ```bash
   bench build --app npd_project_module
   ```

### Documentation Files

This project maintains several documentation files:

- `README.md` - Installation and features
- `INSTALLATION.md` - Detailed installation guide
- `PROGRESS.md` - Development progress tracking
- `REFACTOR_TO_HOOKS.md` - Architectural decisions
- `TASK_*_COMPLETE.md` - Task completion records
- `TESTING_TASK_*.md` - Testing documentation
- `MIGRATION_TESTING.md` - Migration testing guide

### Contributing

When contributing code:
1. Follow the coding standards above
2. Write tests for new features
3. Update documentation as needed
4. Ensure pre-commit hooks pass
5. Test installation/uninstallation idempotency
6. Consider impact on existing data

### License

MIT License - See `license.txt`

---

## Quick Reference

### Useful Commands

```bash
# Install app
bench --site [site] install-app npd_project_module

# Uninstall app
bench --site [site] uninstall-app npd_project_module --yes --no-backup

# Run tests
bench --site [site] run-tests --app npd_project_module

# Clear cache
bench --site [site] clear-cache

# Lint code
ruff check .
ruff format .

# Rebuild
bench build --app npd_project_module
```

### Key Concepts

- **Part**: An item/component being developed
- **Iteration**: A development cycle (e.g., v1, v2, prototype, final)
- **NPD Template**: Predefined sequence of 18 development tasks
- **Part-Task**: A task linked to a specific part and iteration

### Contact

- **Author**: Guru107
- **Email**: connect@gurudatt.in

---

*Last Updated: January 2026*
