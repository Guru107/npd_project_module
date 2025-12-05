# Refactoring: Project DocType Override to Doc Events Hooks

## Overview

Refactored Task 2.0 implementation from overriding the Project DocType class to using Frappe's `doc_events` hooks. This is a cleaner approach that follows Frappe best practices.

## What Changed

### Before (Class Override)
- Used `override_doctype_class` hook to override the entire Project class
- Created `custom/doctype/project/project.py` with custom Project class
- Class methods: `validate()`, `after_insert()`, `on_update()`

### After (Doc Events Hooks)
- Uses `doc_events` hook to register event handlers
- Created `custom/doctype/project/project_hooks.py` with hook functions
- Hook functions: `after_insert()`, `on_update()`, and shared `after_save()` function

## Benefits of Using Hooks

1. **Cleaner Separation**: Hook functions are separate from the core DocType class
2. **Better Maintainability**: Easier to understand and modify
3. **Follows Frappe Patterns**: Uses standard Frappe hook mechanism
4. **Less Intrusive**: Doesn't override the entire class, just adds event handlers
5. **Easier Testing**: Hook functions can be tested independently

## File Structure

```
npd_project_module/
├── npd_project_module/
│   ├── custom/
│   │   └── doctype/
│   │       └── project/
│   │           ├── __init__.py
│   │           └── project_hooks.py    # Hook functions (NEW)
│   └── hooks.py                         # Updated with doc_events
```

## Implementation Details

### Hook Registration (`hooks.py`)

```python
doc_events = {
	"Project": {
		"after_insert": "npd_project_module.custom.doctype.project.project_hooks.after_insert",
		"on_update": "npd_project_module.custom.doctype.project.project_hooks.on_update"
	}
}
```

### Hook Functions (`project_hooks.py`)

1. **`after_save(doc, method, is_new=False)`**
   - Main function that handles both insert and update cases
   - `is_new=True` for new documents, `is_new=False` for updates
   - Generates tasks for new parts
   - Deletes tasks for removed parts

2. **`after_insert(doc, method)`**
   - Called when Project is first created
   - Delegates to `after_save()` with `is_new=True`

3. **`on_update(doc, method)`**
   - Called when Project is updated
   - Delegates to `after_save()` with `is_new=False`

4. **Helper Functions:**
   - `_handle_part_removal()` - Handles deletion of tasks for removed parts
   - `_get_existing_part_numbers()` - Gets parts that already have tasks

## Logic Flow

### For New Projects (after_insert)
1. User creates new Project with parts
2. `after_insert` hook triggers
3. `after_save()` called with `is_new=True`
4. Generates tasks for ALL parts in the project

### For Updated Projects (on_update)
1. User adds/removes parts from existing Project
2. `on_update` hook triggers
3. `after_save()` called with `is_new=False`
4. Determines new parts by checking which parts don't have tasks yet
5. Generates tasks for new parts only
6. Deletes tasks for removed parts

## Key Differences

| Aspect | Class Override | Doc Events Hooks |
|--------|---------------|------------------|
| Hook Type | `override_doctype_class` | `doc_events` |
| File | `project.py` (class) | `project_hooks.py` (functions) |
| Method Signature | `def method(self):` | `def method(doc, method):` |
| Access to Doc | `self` | `doc` parameter |
| Maintainability | Lower (overrides entire class) | Higher (just adds hooks) |
| Frappe Pattern | Less standard | More standard |

## Testing

The functionality remains the same:
- ✅ Tasks are generated for new parts
- ✅ Tasks are generated when parts are added to existing projects
- ✅ Tasks are deleted when parts are removed
- ✅ Duplicate prevention still works
- ✅ Sequential dependencies are created

## Migration Notes

- Old `project.py` file has been deleted
- No database changes required
- Clear cache after deployment: `bench --site [site] clear-cache`

## Next Steps

Continue with remaining tasks:
- Task 3.0: Implement Iteration Management System
- Task 4.0: Implement Task Lifecycle Management

