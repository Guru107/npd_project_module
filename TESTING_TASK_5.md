# Testing Guide: Task 5.0 - Filtering and List View Enhancements

This document provides comprehensive test steps for verifying filtering and grouping functionality in the Task list view and Report Builder.

## Prerequisites

1. A Project with multiple Parts (Items) added
2. Tasks generated for multiple parts with different iteration numbers
3. Tasks with different statuses (Open, Working, Completed, Cancelled, Overdue)
4. Tasks across different iterations (at least Iteration 0 and Iteration 1)

## Test 5.9: Filter Functionality

### Test 5.9.1: Filter by Part Number (Item)

**Objective:** Verify that filtering by Part Number (Item) works correctly in the Task list view.

**Steps:**
1. Navigate to **Task** list view (`/app/task`)
2. Click on the **Filter** button (funnel icon)
3. Add a filter: **Part Number** = `[Select a specific Item/Part]`
4. Click **Apply**
5. Verify that only tasks for the selected Part Number are displayed
6. Verify that tasks for other parts are not shown
7. Clear the filter and verify all tasks are shown again

**Expected Result:**
- Filter correctly shows only tasks for the selected Part Number
- Filter can be cleared and all tasks are displayed again

---

### Test 5.9.2: Filter by Iteration Number

**Objective:** Verify that filtering by Iteration Number works correctly.

**Steps:**
1. Navigate to **Task** list view
2. Click on the **Filter** button
3. Add a filter: **Iteration Number** = `0`
4. Click **Apply**
5. Verify that only tasks with iteration_number = 0 are displayed
6. Change filter to **Iteration Number** = `1`
7. Verify that only tasks with iteration_number = 1 are displayed
8. Clear the filter and verify all tasks are shown

**Expected Result:**
- Filter correctly shows only tasks for the selected iteration number
- Filter works for different iteration numbers
- Filter can be cleared

---

### Test 5.9.3: Filter by Project

**Objective:** Verify that filtering by Project works correctly.

**Steps:**
1. Navigate to **Task** list view
2. Click on the **Filter** button
3. Add a filter: **Project** = `[Select a specific Project]`
4. Click **Apply**
5. Verify that only tasks for the selected Project are displayed
6. Verify that tasks from other projects are not shown
7. Clear the filter and verify all tasks are shown

**Expected Result:**
- Filter correctly shows only tasks for the selected Project
- Filter excludes tasks from other projects
- Filter can be cleared

---

### Test 5.9.4: Filter by Status

**Objective:** Verify that filtering by Task Status works correctly.

**Steps:**
1. Navigate to **Task** list view
2. Click on the **Filter** button
3. Add a filter: **Status** = `Open`
4. Click **Apply**
5. Verify that only tasks with status "Open" are displayed
6. Change filter to **Status** = `Completed`
7. Verify that only tasks with status "Completed" are displayed
8. Change filter to **Status** = `Working`
9. Verify that only tasks with status "Working" are displayed
10. Clear the filter and verify all tasks are shown

**Expected Result:**
- Filter correctly shows only tasks with the selected status
- Filter works for different status values
- Filter can be cleared

---

### Test 5.9.5: Multiple Filters Combined

**Objective:** Verify that multiple filters can be combined and work together.

**Steps:**
1. Navigate to **Task** list view
2. Click on the **Filter** button
3. Add multiple filters:
   - **Project** = `[Select Project]`
   - **Part Number** = `[Select Part]`
   - **Iteration Number** = `0`
   - **Status** = `Open`
4. Click **Apply**
5. Verify that only tasks matching ALL filter criteria are displayed
6. Remove one filter (e.g., Status)
7. Verify that tasks matching the remaining filters are displayed
8. Clear all filters and verify all tasks are shown

**Expected Result:**
- Multiple filters work together (AND logic)
- Removing a filter updates the results correctly
- All filters can be cleared

---

### Test 5.9.6: Quick Filter Menu Items

**Objective:** Verify that quick filter menu items work correctly.

**Steps:**
1. Navigate to **Task** list view
2. Click on the **Menu** (three dots) button
3. Click **All Open Tasks**
4. Verify that:
   - Only tasks with status "Open" or "Overdue" are displayed
   - URL is updated to reflect the filter
5. Click **All Working Tasks**
6. Verify that only tasks with status "Working" are displayed
7. Click **All Completed Tasks**
8. Verify that only tasks with status "Completed" are displayed
9. Click **Show Cancelled Tasks** (if available)
10. Verify that cancelled tasks are now visible
11. Click **Hide Cancelled Tasks**
12. Verify that cancelled tasks are hidden again

**Expected Result:**
- Quick filter menu items correctly apply filters
- URL updates to reflect the current filter state
- Filters can be switched between different quick filters
- Show/Hide Cancelled Tasks toggle works correctly

---

### Test 5.9.7: Default Filter (Hide Cancelled)

**Objective:** Verify that cancelled tasks are hidden by default.

**Steps:**
1. Navigate to **Task** list view (fresh page load)
2. Verify that cancelled tasks are NOT displayed by default
3. Check the filter area - verify that "Status != Cancelled" filter is applied by default
4. Manually remove the filter
5. Verify that cancelled tasks are now visible
6. Refresh the page
7. Verify that cancelled tasks are hidden again (default filter restored)

**Expected Result:**
- Cancelled tasks are hidden by default
- Default filter is "Status != Cancelled"
- Default filter is restored on page refresh

---

## Test 5.10: Grouping Functionality

### Test 5.10.1: Group by Part Number (Item)

**Objective:** Verify that grouping by Part Number works correctly in Report Builder.

**Steps:**
1. Navigate to **Report Builder** (`/app/query-report`)
2. Select **Task** as the DocType
3. Add columns: **Subject**, **Status**, **Part Number**, **Iteration Number**, **Project**
4. Click **Group By** and select **Part Number**
5. Click **Run**
6. Verify that:
   - Tasks are grouped by Part Number
   - Each group shows tasks for a specific Part Number
   - Tasks are organized under their respective Part Number groups
7. Remove grouping and verify tasks are displayed in a flat list

**Expected Result:**
- Tasks are correctly grouped by Part Number
- Grouping can be applied and removed
- Tasks are organized logically within groups

---

### Test 5.10.2: Group by Iteration Number

**Objective:** Verify that grouping by Iteration Number works correctly.

**Steps:**
1. Navigate to **Report Builder**
2. Select **Task** as the DocType
3. Add columns: **Subject**, **Status**, **Part Number**, **Iteration Number**, **Project**
4. Click **Group By** and select **Iteration Number**
5. Click **Run**
6. Verify that:
   - Tasks are grouped by Iteration Number
   - Each group shows tasks for a specific iteration (0, 1, 2, etc.)
   - Tasks are organized under their respective iteration groups
7. Verify that tasks from different iterations are in separate groups

**Expected Result:**
- Tasks are correctly grouped by Iteration Number
- Each iteration forms a separate group
- Tasks are organized logically within iteration groups

---

### Test 5.10.3: Group by Project

**Objective:** Verify that grouping by Project works correctly.

**Steps:**
1. Navigate to **Report Builder**
2. Select **Task** as the DocType
3. Add columns: **Subject**, **Status**, **Part Number**, **Iteration Number**, **Project**
4. Click **Group By** and select **Project**
5. Click **Run**
6. Verify that:
   - Tasks are grouped by Project
   - Each group shows tasks for a specific Project
   - Tasks are organized under their respective Project groups
7. Verify that tasks from different projects are in separate groups

**Expected Result:**
- Tasks are correctly grouped by Project
- Each project forms a separate group
- Tasks are organized logically within project groups

---

### Test 5.10.4: Group by Status

**Objective:** Verify that grouping by Task Status works correctly.

**Steps:**
1. Navigate to **Report Builder**
2. Select **Task** as the DocType
3. Add columns: **Subject**, **Part Number**, **Iteration Number**, **Project**, **Status**
4. Click **Group By** and select **Status**
5. Click **Run**
6. Verify that:
   - Tasks are grouped by Status
   - Each group shows tasks with a specific status (Open, Working, Completed, Cancelled, etc.)
   - Tasks are organized under their respective status groups
7. Verify that tasks with different statuses are in separate groups

**Expected Result:**
- Tasks are correctly grouped by Status
- Each status forms a separate group
- Tasks are organized logically within status groups

---

### Test 5.10.5: Multiple Grouping Levels

**Objective:** Verify that multiple grouping levels work correctly (e.g., Group by Project, then by Part Number).

**Steps:**
1. Navigate to **Report Builder**
2. Select **Task** as the DocType
3. Add columns: **Subject**, **Status**, **Part Number**, **Iteration Number**, **Project**
4. Click **Group By** and select **Project** (first level)
5. Click **Group By** again and select **Part Number** (second level)
6. Click **Run**
7. Verify that:
   - Tasks are first grouped by Project
   - Within each Project group, tasks are further grouped by Part Number
   - Hierarchical grouping structure is displayed correctly
8. Remove one grouping level and verify the remaining grouping still works

**Expected Result:**
- Multiple grouping levels work correctly
- Hierarchical grouping structure is displayed properly
- Removing a grouping level maintains the remaining grouping

---

### Test 5.10.6: Grouping with Filters

**Objective:** Verify that grouping works correctly when filters are applied.

**Steps:**
1. Navigate to **Report Builder**
2. Select **Task** as the DocType
3. Add columns: **Subject**, **Status**, **Part Number**, **Iteration Number**, **Project**
4. Add a filter: **Status** = `Open`
5. Click **Group By** and select **Part Number**
6. Click **Run**
7. Verify that:
   - Only tasks with status "Open" are displayed
   - Tasks are grouped by Part Number
   - Filtered results are correctly grouped
8. Add another filter: **Iteration Number** = `0`
9. Verify that:
   - Only tasks matching both filters are displayed
   - Grouping still works correctly with multiple filters

**Expected Result:**
- Grouping works correctly with filters applied
- Filtered results are properly grouped
- Multiple filters work together with grouping

---

## Summary Checklist

- [ ] Test 5.9.1: Filter by Part Number works correctly
- [ ] Test 5.9.2: Filter by Iteration Number works correctly
- [ ] Test 5.9.3: Filter by Project works correctly
- [ ] Test 5.9.4: Filter by Status works correctly
- [ ] Test 5.9.5: Multiple filters combined work correctly
- [ ] Test 5.9.6: Quick filter menu items work correctly
- [ ] Test 5.9.7: Default filter (hide cancelled) works correctly
- [ ] Test 5.10.1: Group by Part Number works correctly
- [ ] Test 5.10.2: Group by Iteration Number works correctly
- [ ] Test 5.10.3: Group by Project works correctly
- [ ] Test 5.10.4: Group by Status works correctly
- [ ] Test 5.10.5: Multiple grouping levels work correctly
- [ ] Test 5.10.6: Grouping with filters works correctly

---

## Notes

- All filters should be available in both the Task list view and Report Builder
- Grouping is primarily tested in Report Builder, but can also be tested in list view if supported
- Visual indicators for blocked tasks (🔒) should be visible in list view when dependencies are not met
- URL should update when filters are applied via quick filter menu items

