# Testing Guide: Task 3.11 - 3.12 (Iteration Management)

## Overview

This guide helps you test the iteration creation functionality and iteration limit enforcement.

## Prerequisites

1. Module installed and custom fields visible
2. At least one Project created with at least one part
3. Initial iteration (iteration 0) tasks generated
4. At least one task cancelled in the latest iteration

---

## Test 3.11: Iteration Creation

### Objective
Verify that new iterations can be created from cancelled tasks, with proper task generation and obsolete marking.

### Steps

#### Step 1: Setup Initial Iteration

1. **Create a Project with Parts:**
   - Navigate to: Projects > Project
   - Click "New"
   - Fill in Project Name (e.g., "Iteration Test Project")
   - In the "Part Numbers" table, add a part:
     - Click "Add Row"
     - Select an Item from the dropdown (e.g., "Part-001")
     - Iteration Number should automatically be 0 (read-only)
   - Click "Save"
   - **Verify:** 18 tasks should be created for iteration 0

2. **Complete Some Tasks:**
   - Navigate to: Projects > Task List
   - Filter by Project = "Iteration Test Project" and Iteration Number = 0
   - Complete the first 3 tasks in sequence:
     - Task 1: "Part-001 RFQ Data" → Status: "Completed"
     - Task 2: "Part-001 Internal Team Technical Feasibility" → Status: "Completed"
     - Task 3: "Part-001 Supplier Quote & Tooling Sequence" → Status: "Completed"

3. **Cancel a Task (Simulate Failure):**
   - Open Task 4: "Part-001 Technical Sign Off"
   - Change status to "Cancelled"
   - Save
   - **Verify:** All subsequent tasks (5-18) should be automatically cancelled

#### Step 2: Create New Iteration

1. **Open Iteration Dialog:**
   - Navigate to: Projects > Project
   - Open "Iteration Test Project"
   - Click the "Create New Iteration" button (should appear in Actions menu)
   - **Verify:** Dialog opens with part selection dropdown

2. **Select Part and View Info:**
   - Select "Part-001" from the Part Number dropdown
   - **Verify:** Iteration information displays:
     - Latest Iteration: 0
     - Cancelled Task: "Part-001 Technical Sign Off"
     - New Iteration Will Start From: "Part-001 Technical Sign Off"
     - Warning about incomplete tasks (if any)

3. **Create Iteration:**
   - Click "Create Iteration" button
   - **Verify:** Success message appears:
     - "Created new iteration 1 for Part Part-001. Generated X tasks starting from Part-001 Technical Sign Off."
     - Message about obsolete tasks (if any)

#### Step 3: Verify Task Generation

1. **Check New Tasks:**
   - Navigate to: Projects > Task List
   - Filter by Project = "Iteration Test Project" and Iteration Number = 1
   - **Verify:**
     - Tasks are created starting from "Technical Sign Off" (task 4 in sequence)
     - Tasks created: "Technical Sign Off" through "Handover to Production" (15 tasks total)
     - Task names follow format: "Part-001 [Task Name]"
     - All tasks have:
       - Project: "Iteration Test Project"
       - Part Number: "Part-001"
       - Iteration Number: 1
       - Status: "Open"

2. **Verify Task Dependencies:**
   - Open any task from iteration 1 (except the first one)
   - Check the "Depends On" table
   - **Verify:** Each task depends on the previous task in the same iteration
   - **Verify:** Tasks do NOT depend on tasks from iteration 0

3. **Verify Sequential Dependencies:**
   - Try to complete the second task in iteration 1 before the first
   - **Expected:** Should show dependency error
   - Complete the first task in iteration 1
   - Now try to complete the second task
   - **Expected:** Should work without error

#### Step 4: Verify Obsolete Marking

1. **Check Previous Iteration Tasks:**
   - Navigate to: Projects > Task List
   - Filter by Project = "Iteration Test Project" and Iteration Number = 0
   - **Verify:**
     - Tasks 1-3: Status = "Completed" (should remain completed)
     - Task 4: Status = "Cancelled" (the cancelled task)
     - Tasks 5-18: Status = "Cancelled" (should be marked as obsolete/cancelled)

2. **Verify Incomplete Tasks Marked:**
   - If there were any incomplete tasks (status = "Open" or "Working") in iteration 0:
     - They should now be marked as "Cancelled" (obsolete)
   - Count the cancelled tasks in iteration 0
   - **Verify:** Count matches the warning message shown during iteration creation

#### Step 5: Verify Iteration Number Update

1. **Check Project Part Numbers Table:**
   - Navigate to: Projects > Project
   - Open "Iteration Test Project"
   - Scroll to "Part Numbers" table
   - **Verify:** Iteration Number for "Part-001" is updated to 1

2. **Verify Iteration Number is Read-Only:**
   - Try to manually edit the Iteration Number field
   - **Expected:** Field should be read-only (cannot be edited)

#### Step 6: Test Multiple Iterations

1. **Create Second Iteration:**
   - Complete first 2 tasks in iteration 1
   - Cancel task 3 in iteration 1
   - Click "Create New Iteration" button
   - Select "Part-001"
   - Create iteration 2
   - **Verify:** New iteration 2 is created with tasks starting from cancelled task

2. **Verify All Iterations Exist:**
   - Navigate to: Projects > Task List
   - Filter by Project = "Iteration Test Project" and Part Number = "Part-001"
   - Group by Iteration Number
   - **Verify:** You can see tasks from iterations 0, 1, and 2

### Expected Results

✅ Dialog opens correctly with part selection  
✅ Iteration information displays correctly (latest iteration, cancelled task, warnings)  
✅ New iteration created successfully  
✅ Tasks generated starting from cancelled task  
✅ Correct number of tasks created (from cancelled task to end of sequence)  
✅ Task dependencies work correctly within new iteration  
✅ Incomplete tasks from previous iteration marked as obsolete (Cancelled)  
✅ Completed tasks from previous iteration remain completed  
✅ Iteration number updated in Project Part Numbers table  
✅ Multiple iterations can be created sequentially  

---

## Test 3.12: Iteration Limit

### Objective
Verify that the system prevents creating more than 10 iterations (iterations 0-9) for a part.

### Steps

#### Step 1: Create Maximum Iterations (0-9)

**Option A: Manual Creation (for testing)**
- Create iterations 0 through 9 manually by:
  - Completing some tasks
  - Cancelling a task
  - Creating new iteration
  - Repeat until iteration 9 is reached

**Option B: Use Console/API (for faster testing)**
- Use Frappe console or API to create iterations programmatically
- Ensure iterations 0-9 exist with at least one cancelled task in iteration 9

#### Step 2: Attempt to Create 11th Iteration

1. **Verify Current State:**
   - Navigate to: Projects > Project
   - Open your test project
   - Check Part Numbers table
   - **Verify:** Iteration Number shows 9 (or highest iteration)

2. **Attempt to Create New Iteration:**
   - Ensure iteration 9 has at least one cancelled task
   - Click "Create New Iteration" button
   - Select the part that has iteration 9
   - **Verify:** Dialog shows:
     - Latest Iteration: 9
     - Error message: "Maximum iteration limit (10) reached. Cannot create new iteration."
     - "Create Iteration" button should be disabled or show error

3. **Try to Create Iteration:**
   - Click "Create Iteration" button (if enabled)
   - **Expected:** Error message should appear:
     - "Part [Part-001] has reached the maximum iteration limit of 10. Cannot create more iterations."
   - **Verify:** No new iteration is created
   - **Verify:** Iteration number remains 9

#### Step 3: Verify Limit Enforcement

1. **Check Task List:**
   - Navigate to: Projects > Task List
   - Filter by Project and Part Number
   - Group by Iteration Number
   - **Verify:** Only iterations 0-9 exist
   - **Verify:** No iteration 10 exists

2. **Check Project Part Numbers Table:**
   - Navigate to: Projects > Project
   - Open your test project
   - Check Part Numbers table
   - **Verify:** Iteration Number is still 9 (not 10)

3. **Verify Error Message:**
   - The error message should clearly state:
     - Which part reached the limit
     - Maximum iteration limit (10)
     - That no more iterations can be created

### Expected Results

✅ System correctly identifies when iteration limit is reached  
✅ Error message displays clearly  
✅ No new iteration is created when limit is reached  
✅ Iteration number remains at 9 (maximum)  
✅ Dialog shows error/warning about limit  
✅ Cannot bypass limit through UI or API  

---

## Additional Test Scenarios

### Test Edge Cases

1. **No Cancelled Task:**
   - Create a project with parts
   - Complete all tasks in iteration 0 (or leave them all open)
   - Try to create new iteration
   - **Expected:** Error: "No cancelled task found in the latest iteration. Cannot create new iteration without a cancelled task."

2. **No Previous Iteration:**
   - Create a new project with parts
   - Immediately try to create new iteration (before any tasks exist)
   - **Expected:** Error: "No previous iteration found. Initial iteration (0) should be created automatically when parts are added to the project."

3. **Multiple Parts in Project:**
   - Create project with 2 parts (Part-A and Part-B)
   - Part-A: Create iterations 0-9
   - Part-B: Create iteration 0 only
   - **Verify:** Can still create iteration 1 for Part-B (limit is per part, not per project)

4. **Partial Task Completion:**
   - Create iteration 0, complete tasks 1-5, cancel task 6
   - Create iteration 1 starting from task 6
   - Complete tasks 1-3 in iteration 1, cancel task 4
   - Create iteration 2 starting from task 4
   - **Verify:** Each iteration starts from its cancelled task correctly

### Test UI/UX

1. **Dialog Information Display:**
   - Verify all information is displayed correctly
   - Verify warnings are shown for incomplete tasks
   - Verify error messages are clear and actionable

2. **Button States:**
   - Verify "Create Iteration" button is disabled when:
     - No part selected
     - Maximum iteration limit reached
     - No cancelled task found
   - Verify button is enabled when:
     - Valid part selected
     - Cancelled task exists
     - Iteration limit not reached

3. **Form Refresh:**
   - After creating iteration, verify form refreshes
   - Verify iteration number updates in Part Numbers table
   - Verify new tasks appear in task list

---

## Troubleshooting

### Iteration Creation Fails

- **Check for cancelled task:** Ensure latest iteration has at least one cancelled task
- **Check iteration limit:** Verify iteration count is less than 10
- **Check browser console:** Look for JavaScript errors
- **Check server logs:** Look for Python errors in bench logs
- **Clear cache:** `bench --site [site] clear-cache`

### Tasks Not Generated Correctly

- **Verify cancelled task index:** Check that tasks start from correct position in sequence
- **Verify task count:** Should create tasks from cancelled task to end (not all 18)
- **Check dependencies:** Verify dependencies are set correctly within iteration

### Obsolete Tasks Not Marked

- **Check task status:** Verify incomplete tasks are marked as "Cancelled"
- **Check iteration number:** Ensure correct iteration number is used
- **Check server logs:** Look for errors in marking process

### Iteration Limit Not Enforced

- **Verify iteration count:** Check actual iteration numbers in database
- **Check validation logic:** Ensure `validate_iteration_limit()` is called
- **Test with console:** Try creating iteration via API/console to verify server-side validation

---

## Success Criteria

✅ **Task 3.11:** New iterations created successfully from cancelled tasks  
✅ **Task 3.11:** Tasks generated correctly starting from cancelled task  
✅ **Task 3.11:** Incomplete tasks from previous iteration marked as obsolete  
✅ **Task 3.11:** Iteration number updated in Project Part Numbers table  
✅ **Task 3.12:** System prevents creating 11th iteration  
✅ **Task 3.12:** Clear error message shown when limit reached  
✅ **Task 3.12:** No new iteration created when limit is reached  
✅ Dialog displays correct information and warnings  
✅ All edge cases handled correctly  
✅ UI/UX is intuitive and user-friendly  

---

## Notes

- Iterations are numbered 0-9 (10 total iterations)
- Each iteration must have at least one cancelled task to create the next iteration
- Incomplete tasks from previous iteration are marked as "Cancelled" (obsolete)
- Completed tasks remain completed across iterations
- Iteration limit is enforced per part, not per project
- Task dependencies only work within the same iteration

