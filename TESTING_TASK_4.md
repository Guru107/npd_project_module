# Testing Guide: Task 4.0 - Task Lifecycle Management

## Overview

This guide helps you test the task lifecycle management features, including automatic cancellation cascades, dependency validation, and list view filtering for cancelled tasks.

## Prerequisites

1. Module installed and custom fields visible
2. At least one Project created with at least one part
3. Initial iteration (iteration 0) tasks generated
4. Understanding of the 18-task sequence:
   - RFQ Data
   - Internal Team Technical Feasibility
   - Supplier Quote & Tooling Sequence
   - Technical Sign Off
   - Commercial with M&M
   - VOB or LOBA
   - TKO Data
   - Comparison of TKO & RFQ Data
   - Commercial with Supplier
   - Time Plan
   - Design Approval Process
   - Buy Off
   - HLTO
   - IPTR
   - PPAP
   - JPTR
   - APQP
   - Handover to Production

---

## Test 4.10: Task Cancellation Cascade

### Objective
Verify that when a task is cancelled, all subsequent tasks in the sequence (same part, same iteration) are automatically cancelled.

### Steps

#### Step 1: Setup Test Project

1. **Create a Project with Parts:**
   - Navigate to: Projects > Project
   - Click "New"
   - Fill in Project Name (e.g., "Cancellation Test Project")
   - In the "Part Numbers" table, add a part:
     - Click "Add Row"
     - Select an Item from the dropdown (e.g., "Part-001")
     - Iteration Number should automatically be 0 (read-only)
   - Click "Save"
   - **Verify:** 18 tasks should be created for iteration 0

2. **Complete Some Tasks:**
   - Navigate to: Projects > Task List
   - Filter by Project = "Cancellation Test Project" and Iteration Number = 0
   - Complete the first 5 tasks in sequence:
     - Task 1: "Part-001 RFQ Data" → Status: "Completed"
     - Task 2: "Part-001 Internal Team Technical Feasibility" → Status: "Completed"
     - Task 3: "Part-001 Supplier Quote & Tooling Sequence" → Status: "Completed"
     - Task 4: "Part-001 Technical Sign Off" → Status: "Completed"
     - Task 5: "Part-001 Commercial with M&M" → Status: "Completed"

#### Step 2: Cancel a Task Mid-Sequence

1. **Cancel Task 6:**
   - Open Task 6: "Part-001 VOB or LOBA"
   - Change status to "Cancelled"
   - Click "Save"
   - **Verify:** Success message appears: "Cancelled X subsequent task(s) in the sequence for Part Part-001 (Iteration 0)"
     - X should be 12 (tasks 7-18)

2. **Verify Cancellation Cascade:**
   - Navigate to: Projects > Task List
   - Filter by Project = "Cancellation Test Project" and Iteration Number = 0
   - **Verify:**
     - Task 6: "Part-001 VOB or LOBA" → Status: "Cancelled"
     - Tasks 7-18: All should have Status: "Cancelled"
     - Tasks 1-5: Should remain "Completed" (not affected)

#### Step 3: Test Cancellation at Different Positions

1. **Create Another Project:**
   - Create a new project "Cancellation Test Project 2" with Part-002
   - Verify 18 tasks created

2. **Cancel Task 1 (First Task):**
   - Open Task 1: "Part-002 RFQ Data"
   - Change status to "Cancelled"
   - Save
   - **Verify:** All tasks 2-18 should be cancelled (17 tasks)

3. **Create Another Project:**
   - Create a new project "Cancellation Test Project 3" with Part-003
   - Complete tasks 1-17
   - Cancel Task 18 (Last Task)
   - **Verify:** Only Task 18 should be cancelled (no subsequent tasks to cancel)

#### Step 4: Test Cancellation in Different Iterations

1. **Create Iteration 1:**
   - In "Cancellation Test Project", create iteration 1 for Part-001
   - Verify tasks are generated starting from the cancelled task

2. **Cancel Task in Iteration 1:**
   - Cancel a task in iteration 1 (e.g., task 3 in iteration 1)
   - **Verify:** Only tasks in iteration 1 are affected
   - **Verify:** Tasks in iteration 0 remain unchanged

### Expected Results

✅ When a task is cancelled, all subsequent tasks in the same sequence are automatically cancelled  
✅ Only tasks in the same part and same iteration are affected  
✅ Tasks before the cancelled task remain unchanged  
✅ Cancellation message shows correct count of cancelled tasks  
✅ Cancellation works correctly at any position in the sequence (first, middle, last)  
✅ Cancellation in one iteration does not affect tasks in other iterations  

---

## Test 4.11: Part Deletion

### Objective
Verify that when a part is removed from a project, all associated tasks are deleted.

### Steps

#### Step 1: Setup Test Project

1. **Create a Project with Multiple Parts:**
   - Navigate to: Projects > Project
   - Click "New"
   - Fill in Project Name (e.g., "Part Deletion Test Project")
   - In the "Part Numbers" table, add two parts:
     - Part 1: "Part-001"
     - Part 2: "Part-002"
   - Click "Save"
   - **Verify:** 36 tasks should be created (18 per part)

2. **Verify Tasks Exist:**
   - Navigate to: Projects > Task List
   - Filter by Project = "Part Deletion Test Project"
   - **Verify:** 36 tasks visible (18 for Part-001, 18 for Part-002)

#### Step 2: Remove Part from Project

1. **Remove Part-001:**
   - Open "Part Deletion Test Project"
   - In the "Part Numbers" table, remove the row for "Part-001"
   - Click "Save"
   - **Verify:** Success message or no error

2. **Verify Tasks Deleted:**
   - Navigate to: Projects > Task List
   - Filter by Project = "Part Deletion Test Project"
   - **Verify:** Only 18 tasks remain (all for Part-002)
   - **Verify:** No tasks for Part-001 exist

3. **Verify Part-001 Tasks Are Completely Deleted:**
   - Try to search for tasks with Part Number = "Part-001" and Project = "Part Deletion Test Project"
   - **Verify:** No tasks found

#### Step 3: Verify Item Project Field Cleared

1. **Check Item Master:**
   - Navigate to: Stock > Item
   - Open "Part-001"
   - **Verify:** Project field should be empty (cleared)

2. **Check Part-002:**
   - Open "Part-002"
   - **Verify:** Project field should still be set to "Part Deletion Test Project"

#### Step 4: Test Removing All Parts

1. **Remove Remaining Part:**
   - Open "Part Deletion Test Project"
   - Remove Part-002 from the Part Numbers table
   - Click "Save"
   - **Verify:** No error

2. **Verify All Tasks Deleted:**
   - Navigate to: Projects > Task List
   - Filter by Project = "Part Deletion Test Project"
   - **Verify:** No tasks exist for this project

3. **Verify All Item Project Fields Cleared:**
   - Check both Part-001 and Part-002 in Item master
   - **Verify:** Both should have empty Project fields

### Expected Results

✅ When a part is removed from a project, all associated tasks are deleted  
✅ Tasks are deleted across all iterations for that part  
✅ Item's project field is automatically cleared when part is removed  
✅ Removing all parts results in all tasks being deleted  
✅ No orphaned tasks remain in the system  

---

## Test 4.12: Dependency Validation

### Objective
Verify that tasks cannot be completed before their dependencies are met (within the same iteration).

### Steps

#### Step 1: Setup Test Project

1. **Create a Project:**
   - Navigate to: Projects > Project
   - Click "New"
   - Fill in Project Name (e.g., "Dependency Test Project")
   - Add Part-001 to Part Numbers table
   - Click "Save"
   - **Verify:** 18 tasks created

#### Step 2: Test Dependency Validation - Working Status

1. **Try to Set Task 2 to Working:**
   - Navigate to: Projects > Task List
   - Open Task 2: "Part-001 Internal Team Technical Feasibility"
   - Try to change status to "Working"
   - Click "Save"
   - **Expected:** Error message:
     - "Cannot working task [Task Name] (Part: Part-001, Iteration: 0) as its dependent task [Previous Task] is not completed/cancelled. Dependencies are enforced within the same iteration only."

2. **Verify Task Status Not Changed:**
   - **Verify:** Task 2 status remains "Open" (not changed to "Working")

#### Step 3: Test Dependency Validation - Completed Status

1. **Try to Complete Task 2:**
   - Open Task 2: "Part-001 Internal Team Technical Feasibility"
   - Try to change status to "Completed"
   - Click "Save"
   - **Expected:** Same error message as above

2. **Complete Task 1 First:**
   - Open Task 1: "Part-001 RFQ Data"
   - Change status to "Completed"
   - Click "Save"
   - **Verify:** Task 1 is now "Completed"

3. **Now Complete Task 2:**
   - Open Task 2: "Part-001 Internal Team Technical Feasibility"
   - Change status to "Completed"
   - Click "Save"
   - **Verify:** Task 2 is now "Completed" (no error)

#### Step 4: Test Multiple Dependencies

1. **Try to Complete Task 5:**
   - Open Task 5: "Part-001 Commercial with M&M"
   - Try to change status to "Completed"
   - Click "Save"
   - **Expected:** Error message mentioning Task 4 as dependency

2. **Complete Tasks in Sequence:**
   - Complete Task 3: "Part-001 Supplier Quote & Tooling Sequence"
   - Complete Task 4: "Part-001 Technical Sign Off"
   - Now try to complete Task 5
   - **Verify:** Task 5 can be completed without error

#### Step 5: Test Cancelled Dependency

1. **Cancel Task 3:**
   - Open Task 3: "Part-001 Supplier Quote & Tooling Sequence"
   - Change status to "Cancelled"
   - Save
   - **Verify:** Tasks 4-18 are automatically cancelled

2. **Try to Complete Task 4:**
   - Open Task 4: "Part-001 Technical Sign Off"
   - Try to change status to "Completed"
   - **Expected:** Error (task is cancelled, but if it wasn't, it would show dependency error)

3. **Verify Cancelled Tasks Can't Be Completed:**
   - **Verify:** Cancelled tasks cannot be changed to "Completed" or "Working"

### Expected Results

✅ Cannot set task status to "Working" if dependencies not met  
✅ Cannot set task status to "Completed" if dependencies not met  
✅ Error messages clearly indicate which dependency is blocking  
✅ Error messages mention "within the same iteration only"  
✅ After dependencies are met, tasks can be completed  
✅ Validation works for tasks with multiple dependencies  
✅ Cancelled tasks cannot be set to "Working" or "Completed"  

---

## Test 4.13: Cross-Iteration Independence

### Objective
Verify that tasks from different iterations don't block each other (dependencies are only enforced within the same iteration).

### Steps

#### Step 1: Setup Multiple Iterations

1. **Create Project with Part:**
   - Navigate to: Projects > Project
   - Click "New"
   - Fill in Project Name (e.g., "Cross-Iteration Test Project")
   - Add Part-001 to Part Numbers table
   - Click "Save"
   - **Verify:** 18 tasks created for iteration 0

2. **Complete Tasks in Iteration 0:**
   - Complete tasks 1-3 in iteration 0:
     - Task 1: "Part-001 RFQ Data" → Completed
     - Task 2: "Part-001 Internal Team Technical Feasibility" → Completed
     - Task 3: "Part-001 Supplier Quote & Tooling Sequence" → Completed

3. **Cancel Task 4 in Iteration 0:**
   - Cancel Task 4: "Part-001 Technical Sign Off"
   - **Verify:** Tasks 5-18 in iteration 0 are automatically cancelled

4. **Create Iteration 1:**
   - Open "Cross-Iteration Test Project"
   - Click "Create New Iteration"
   - Select Part-001
   - Click "Create Iteration"
   - **Verify:** 15 tasks created for iteration 1 (starting from Task 4)

#### Step 2: Test Cross-Iteration Independence

1. **Complete Task 1 in Iteration 1:**
   - Navigate to: Projects > Task List
   - Filter by Project = "Cross-Iteration Test Project" and Iteration Number = 1
   - Open Task 1 in iteration 1: "Part-001 Technical Sign Off"
   - Change status to "Completed"
   - Click "Save"
   - **Verify:** Task completes without error (no dependency on iteration 0 tasks)

2. **Complete Task 2 in Iteration 1:**
   - Open Task 2 in iteration 1: "Part-001 Commercial with M&M"
   - Change status to "Completed"
   - Click "Save"
   - **Verify:** Task completes without error (depends only on Task 1 in iteration 1)

3. **Verify Iteration 0 Tasks Unchanged:**
   - Filter by Iteration Number = 0
   - **Verify:** Tasks 1-3 remain "Completed"
   - **Verify:** Tasks 4-18 remain "Cancelled"
   - **Verify:** No changes to iteration 0 tasks

#### Step 3: Test Dependency Within Same Iteration

1. **Try to Skip Task in Iteration 1:**
   - Filter by Iteration Number = 1
   - Try to complete Task 3 in iteration 1 before Task 2 is completed
   - **Expected:** Error message (dependency within same iteration)

2. **Complete Tasks in Order:**
   - Complete Task 2 in iteration 1
   - Now complete Task 3 in iteration 1
   - **Verify:** Works without error

#### Step 4: Test Multiple Iterations

1. **Create Iteration 2:**
   - Complete more tasks in iteration 1, then cancel one
   - Create iteration 2
   - **Verify:** Tasks in iteration 2 are independent of iterations 0 and 1

2. **Verify Independence:**
   - Complete tasks in iteration 2
   - **Verify:** No dependency errors related to iterations 0 or 1
   - **Verify:** Dependencies only checked within iteration 2

### Expected Results

✅ Tasks in iteration 1 can be completed independently of iteration 0  
✅ Tasks in iteration 1 don't depend on iteration 0 tasks  
✅ Dependencies are only enforced within the same iteration  
✅ Completing tasks in one iteration doesn't affect other iterations  
✅ Each iteration maintains its own sequential dependency chain  
✅ Multiple iterations can exist independently for the same part  

---

## Test 4.8-4.9: Cancelled Task Filtering

### Objective
Verify that cancelled/obsolete tasks are hidden from active views by default but remain accessible when needed.

### Steps

#### Step 1: Setup Test Data

1. **Create Project with Cancelled Tasks:**
   - Create a project "Filter Test Project" with Part-001
   - Complete tasks 1-3
   - Cancel task 4
   - **Verify:** Tasks 5-18 are automatically cancelled

#### Step 2: Test Default Filter

1. **View Task List:**
   - Navigate to: Projects > Task List
   - Filter by Project = "Filter Test Project"
   - **Verify:** Only non-cancelled tasks are visible (tasks 1-3)
   - **Verify:** Cancelled tasks (4-18) are NOT visible

2. **Check Filter:**
   - Look at the filter bar
   - **Verify:** Filter shows "Status != Cancelled" (or similar)

#### Step 3: Show Cancelled Tasks

1. **Use Menu to Show Cancelled Tasks:**
   - In the Task List view, click the menu (three dots or Actions)
   - Click "Show Cancelled Tasks"
   - **Verify:** All tasks are now visible (including cancelled ones)
   - **Verify:** Filter bar shows cancelled tasks are included

2. **Verify Cancelled Tasks Visible:**
   - **Verify:** Tasks 4-18 are now visible with status "Cancelled"
   - **Verify:** Tasks 1-3 remain visible with status "Completed"

#### Step 4: Hide Cancelled Tasks Again

1. **Use Menu to Hide Cancelled Tasks:**
   - Click the menu again
   - Click "Hide Cancelled Tasks"
   - **Verify:** Cancelled tasks are hidden again
   - **Verify:** Only non-cancelled tasks visible

#### Step 5: Manual Filter Override

1. **Manually Add Cancelled Filter:**
   - In the filter bar, add filter: Status = Cancelled
   - **Verify:** Only cancelled tasks are visible

2. **Remove All Filters:**
   - Remove all status filters
   - **Verify:** All tasks visible (both cancelled and non-cancelled)

3. **Restore Default:**
   - Use "Hide Cancelled Tasks" menu item
   - **Verify:** Default filter restored (cancelled tasks hidden)

#### Step 6: Test with Multiple Projects

1. **Create Another Project:**
   - Create "Filter Test Project 2" with Part-002
   - Cancel some tasks
   - **Verify:** Default filter applies to all projects
   - **Verify:** Cancelled tasks hidden by default

### Expected Results

✅ Cancelled tasks are hidden from active views by default  
✅ Default filter excludes cancelled tasks  
✅ Users can show cancelled tasks using menu option  
✅ Users can hide cancelled tasks using menu option  
✅ Users can manually override filters to see cancelled tasks  
✅ Cancelled tasks remain accessible when needed  
✅ Filter behavior is consistent across all projects  

---

## Test Summary Checklist

Use this checklist to verify all features are working correctly:

### Task Cancellation Cascade (4.10)
- [ ] Cancelling a task cancels all subsequent tasks in sequence
- [ ] Only tasks in same part and iteration are affected
- [ ] Cancellation message shows correct count
- [ ] Works correctly at any position (first, middle, last)
- [ ] Different iterations are independent

### Part Deletion (4.11)
- [ ] Removing part deletes all associated tasks
- [ ] Tasks deleted across all iterations
- [ ] Item project field is cleared
- [ ] Removing all parts deletes all tasks
- [ ] No orphaned tasks remain

### Dependency Validation (4.12)
- [ ] Cannot set status to "Working" if dependencies not met
- [ ] Cannot set status to "Completed" if dependencies not met
- [ ] Error messages are clear and informative
- [ ] After dependencies met, tasks can be completed
- [ ] Works for tasks with multiple dependencies

### Cross-Iteration Independence (4.13)
- [ ] Tasks in different iterations don't block each other
- [ ] Dependencies only enforced within same iteration
- [ ] Each iteration maintains own dependency chain
- [ ] Multiple iterations can exist independently

### Cancelled Task Filtering (4.8-4.9)
- [ ] Cancelled tasks hidden by default
- [ ] Can show cancelled tasks via menu
- [ ] Can hide cancelled tasks via menu
- [ ] Manual filter override works
- [ ] Cancelled tasks remain accessible

---

## Troubleshooting

### Issue: Cancellation cascade not working
- **Check:** Verify `on_update` hook is registered in `hooks.py`
- **Check:** Check browser console for JavaScript errors
- **Check:** Verify `frappe.flags.in_task_generation` is not set during cancellation

### Issue: Dependency validation not working
- **Check:** Verify `validate` hook is registered in `hooks.py`
- **Check:** Verify `before_validate` hook is filtering dependencies correctly
- **Check:** Check task's `depends_on` table has correct dependencies

### Issue: Cancelled tasks still visible
- **Check:** Clear browser cache and reload
- **Check:** Verify `task_list.js` is loaded (check browser console)
- **Check:** Verify `doctype_list_js` is registered in `hooks.py`

### Issue: Part deletion not deleting tasks
- **Check:** Verify `on_update` hook in `project_hooks.py` is called
- **Check:** Check for errors in server logs
- **Check:** Verify `delete_tasks_for_part` function is working

---

## Notes

- All tests should be performed in a development/test environment
- Some tests may require multiple browser refreshes to see changes
- If you encounter issues, check the browser console and server logs
- Task status changes may take a moment to reflect in the list view
- Cancelled tasks are marked with "Cancelled" status, not "Obsolete" (as per current implementation)

