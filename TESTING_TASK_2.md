# Testing Guide: Task 2.12 - 2.14

## Overview

This guide helps you test the automatic task generation and dependency enforcement features.

## Prerequisites

1. Module installed and custom fields visible
2. At least one Project created
3. At least one Item created in the system

## Test 2.12: Task Generation

### Objective
Verify that 18 tasks are created per part with correct naming when a project is saved.

### Steps

1. **Create a Project:**
   - Navigate to: Projects > Project
   - Click "New"
   - Fill in Project Name (e.g., "Test Project")
   - In the "Part Numbers" table, add a part:
     - Click "Add Row"
     - Select an Item from the dropdown (e.g., "Part-001")
     - Iteration Number should automatically be 0 (read-only)
   - Click "Save"

2. **Verify Task Generation:**
   - Navigate to: Projects > Task List
   - Filter by Project = "Test Project"
   - You should see 18 tasks created
   - Task names should follow format: "[Item Name] [Task Name]"
     - Example: "Part-001 RFQ Data", "Part-001 Internal Team Technical Feasibility", etc.

3. **Verify Task Details:**
   - Open any task
   - Verify fields:
     - Project: Should be set to "Test Project"
     - Part Number: Should be set to the Item you selected
     - Iteration Number: Should be 0 (read-only)

4. **Test with Multiple Parts:**
   - Edit the Project
   - Add another part to the Part Numbers table (e.g., "Part-002")
   - Save the Project
   - Verify: 18 more tasks should be created (total 36 tasks for 2 parts)

### Expected Results

✅ 18 tasks created for each part  
✅ Task names follow format: "[Item Name] [Task Name]"  
✅ All tasks have correct Project, Part Number, and Iteration Number  
✅ Tasks are created in sequential order  
✅ No duplicate tasks created if you save the project again

---

## Test 2.13: Dependency Enforcement (Within Same Iteration)

### Objective
Verify that tasks cannot be completed before the previous task is completed (within the same iteration).

### Steps

1. **Create a Project with Parts:**
   - Create a new Project with at least one part
   - Verify 18 tasks are created

2. **Test Dependency Enforcement:**
   - Navigate to: Projects > Task List
   - Filter by Project = your test project
   - Find the second task in the sequence (e.g., "Part-001 Internal Team Technical Feasibility")
   - Try to change its status to "Working" or "Completed"
   - **Expected:** You should see an error message:
     - "Cannot complete task [Task Name] as its dependent task [Previous Task] is not completed/cancelled. Dependencies are enforced within the same iteration only."

3. **Complete Tasks in Order:**
   - Complete the first task (e.g., "Part-001 RFQ Data")
     - Open the task
     - Change status to "Completed"
     - Save
   - Now try to complete the second task
     - **Expected:** Should work without error

4. **Test "Working" Status:**
   - Create a new project with parts
   - Try to set the second task status to "Working" before completing the first
   - **Expected:** Should show dependency error

### Expected Results

✅ Cannot complete task 2 before task 1 is completed  
✅ Cannot set task 2 to "Working" before task 1 is completed  
✅ After task 1 is completed, task 2 can be completed  
✅ Error messages clearly indicate which dependency is blocking  
✅ Error messages mention "within the same iteration only"

---

## Test 2.14: Cross-Iteration Independence

### Objective
Verify that dependencies are only enforced within the same iteration (tasks from different iterations don't block each other).

### Steps

1. **Create Initial Iteration:**
   - Create a Project with one part
   - Complete first 3 tasks (RFQ Data, Internal Team Technical Feasibility, Supplier Quote & Tooling Sequence)
   - Cancel the 4th task (Technical Sign Off)
   - This simulates a failed iteration

2. **Create Second Iteration:**
   - (This will be implemented in Task 3.0, but for now manually test)
   - Manually create tasks for iteration 1:
     - Create new tasks with same part but iteration_number = 1
     - Start from "Technical Sign Off" (the cancelled task)
   - OR wait for Task 3.0 implementation

3. **Test Cross-Iteration Independence:**
   - In Iteration 0: Leave task 3 (Supplier Quote) as "Open"
   - In Iteration 1: Try to complete task 1 (RFQ Data)
   - **Expected:** Should work! Iteration 1 tasks should not be blocked by Iteration 0 tasks

4. **Verify Dependencies Work Within Iteration:**
   - In Iteration 1: Try to complete task 2 before task 1
   - **Expected:** Should show dependency error (within same iteration)

### Expected Results

✅ Tasks from Iteration 0 don't block tasks from Iteration 1  
✅ Tasks from Iteration 1 don't block tasks from Iteration 0  
✅ Dependencies still work correctly within the same iteration  
✅ Each iteration's tasks are independent

---

## Test Additional Features

### Test Automatic Cancellation

1. **Cancel a Task Mid-Sequence:**
   - Create a project with parts
   - Complete first 2 tasks
   - Cancel the 3rd task
   - **Expected:** All subsequent tasks (4-18) should be automatically cancelled

2. **Verify Cancellation:**
   - Check task list
   - Tasks 4-18 should have status "Cancelled"
   - You should see a message: "Cancelled X subsequent task(s) in the sequence"

### Test Part Removal

1. **Remove a Part:**
   - Edit a project
   - Remove a part from the Part Numbers table
   - Save the project
   - **Expected:** All tasks for that part should be deleted
   - Item's project field should be cleared

### Test Project Deletion

1. **Delete a Project:**
   - Delete a project that has tasks and items assigned
   - **Expected:** 
     - All tasks should be deleted
     - All Item project references should be cleared
     - No errors should occur

---

## Troubleshooting

### Tasks Not Generated

- Check if project was saved successfully
- Check if parts were added to Part Numbers table
- Check browser console for errors
- Clear cache: `bench --site [site] clear-cache`

### Dependency Errors Not Showing

- Verify tasks have `part_number` and `iteration_number` fields set
- Check that `before_validate` hook is registered in hooks.py
- Clear cache and reload page

### Tasks Not Cancelling Automatically

- Verify `on_update` hook is registered
- Check that task has `part_number` and `iteration_number` set
- Check error logs for any issues

---

## Success Criteria

✅ **Task 2.12:** All 18 tasks created correctly with proper naming  
✅ **Task 2.13:** Dependencies enforced - cannot complete task before previous task  
✅ **Task 2.14:** Cross-iteration independence - tasks from different iterations don't block each other  
✅ Automatic cancellation works  
✅ Part removal works  
✅ Project deletion works

