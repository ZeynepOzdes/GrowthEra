# GrowthEra Garden V2 Design Spec

## 1. Purpose

GrowthEra Garden is the visual and emotional representation of the user's personal growth journey.

The Garden should not be only a task completion board. It should feel like a living world that grows through productive work, consistency, daily responsibilities, reflection, creativity, and self-care.

The core metaphor is:

- Flower = productive effort
- Tree = consistency and habits
- Path = daily responsibilities
- Water = awareness, care, and healing
- Air = inspiration, joy, and creativity

Garden V2 will replace the simple 8x8 MVP grid with a time-based expandable garden world.

---

## 2. Garden Plot System

The Garden is divided into 30-day plots.

One garden plot represents one 30-day journey period.

Examples:

- Plot 1 = Journey Day 1-30
- Plot 2 = Journey Day 31-60
- Plot 3 = Journey Day 61-90

As the user continues using GrowthEra, new garden plots unlock automatically.

The user should be able to scroll through past and current garden plots.

This solves the infinite growth problem. Instead of one garden growing forever, the user's journey becomes a series of visual garden areas.

---

## 3. Journey Day

The system needs a user-specific journey day.

For the first version, journey day can be calculated from the user's account creation date.

Later, this can be changed to a dedicated garden_started_at value.

Formula:

    journey_day = number of days since garden start date + 1

Plot calculation:

    plot_index = ceil(journey_day / 30)
    plot_day = ((journey_day - 1) % 30) + 1

Examples:

- Journey Day 1 → Plot 1, Plot Day 1
- Journey Day 30 → Plot 1, Plot Day 30
- Journey Day 31 → Plot 2, Plot Day 1
- Journey Day 60 → Plot 2, Plot Day 30
- Journey Day 61 → Plot 3, Plot Day 1

---

## 4. Garden Objects

Garden V2 should use flexible garden objects instead of only fixed cells.

A garden object can be:

- flower
- tree
- path stone
- idle rock
- water area
- air decoration
- fire overlay
- special reward object

Recommended table:

    garden_objects

Suggested fields:

    id
    user_id
    garden_plot_id
    element_type
    object_type
    object_subtype
    source_type
    source_id
    position_row
    position_column
    layer
    status
    is_persistent
    visible_date
    metadata_json
    created_at
    updated_at

Field meaning:

    element_type:
    flower / tree / path / water / air / fire

    object_type:
    plant / tree / path_stone / idle_rock / lake / decoration / overlay

    object_subtype:
    rose / coding_flower / small_tree / bench / lantern / torch / pond / stone

    source_type:
    task / habit / air_reward / system / generated

    status:
    active / dormant / completed / expired

---

## 5. Flower System

Flower represents productive effort.

A flower is created when the user completes an Earth + Flower task.

Rule:

    Earth flower task completed
    → create persistent flower object in the current garden plot

Flower objects should stay permanently in the plot where they were earned.

Examples:

- Coding session completed → coding flower
- Study session completed → study flower
- Deep work task completed → focus flower

Future idea:

Different life areas can produce different flower styles.

---

## 6. Habit Tree System

Tree represents consistency and habits.

The current MVP system uses active streak directly as tree stage. Garden V2 should separate streak from permanent growth.

Important principle:

    If a streak breaks, the tree becomes dormant.
    But its growth progress is not lost.
    When the user starts again, the tree continues growing from previous progress.

Recommended table:

    habit_tree_states

Suggested fields:

    id
    user_id
    habit_id
    growth_points
    current_streak
    best_streak
    last_completed_date
    is_dormant
    active_cycle_number
    created_at
    updated_at

Meaning:

    growth_points:
    Total completed habit days. This never resets.

    current_streak:
    Current consecutive completion streak.

    best_streak:
    Best streak ever reached for this habit.

    last_completed_date:
    Last completed habit log date.

    is_dormant:
    True if the habit has no valid active streak.

---

## 7. Habit Tree 30-Day Cycles

A habit should not grow one infinite tree forever.

Instead:

    Every 30 completed habit days creates or completes one tree.

Examples:

    Completed habit days 1-30
    → Tree 1 grows

    Completed habit days 31-60
    → Tree 2 grows

    Completed habit days 61-90
    → Tree 3 grows

This means a long-term habit creates a forest over time.

Recommended table:

    habit_tree_cycles

Suggested fields:

    id
    user_id
    habit_id
    garden_plot_id
    garden_object_id
    cycle_number
    cycle_start_growth_point
    cycle_end_growth_point
    growth_points_in_cycle
    status
    created_at
    updated_at

Cycle rules:

- 1-2 points in cycle → seed
- 3-6 points in cycle → sprout
- 7-13 points in cycle → small tree
- 14-29 points in cycle → tree
- 30 points in cycle → completed tree

If the habit becomes inactive:

    current tree object status → dormant
    growth_points stay unchanged
    cycle progress stays unchanged

When the habit is completed again:

    current tree object status → active
    growth continues from previous progress

---

## 8. Rock and Path System

Rock represents daily responsibilities.

Rock tasks should create a dynamic daily system.

Rules:

    Today's active Earth + Rock tasks
    → shown as idle rocks

    Completed Earth + Rock tasks
    → converted into persistent path stones

Example:

    Today user has 3 rock tasks.
    Garden shows 3 idle rocks.

    User completes 1 rock task.
    1 idle rock becomes a path stone.
    2 idle rocks remain idle.

    Tomorrow:
    unfinished idle rocks disappear.
    new idle rocks are generated from tomorrow's rock tasks.
    completed path stone remains permanently.

Important design decision:

    Idle rocks do not need to be permanently stored.
    They can be calculated from today's active rock tasks.

Persistent path stones should be stored as garden objects.

Rule:

    Rock task completed
    → create persistent path stone object in current plot

---

## 9. Water System

Water represents awareness, care, and healing.

Water tasks are not exactly habits, but they may feel habit-like because they often involve reflection and self-awareness.

Examples:

- Reflect on eating behavior
- Review emotional triggers
- Write a body awareness note
- Check sleep quality
- Reflect on stress level
- Write a recovery note

MVP rule:

    Water task completed
    → grow the water area in the current garden plot

Water stages:

- 1 completed water task → puddle
- 3 completed water tasks → small pond
- 7 completed water tasks → pond
- 15 completed water tasks → lake
- 30 completed water tasks → large lake

Possible implementation:

Use a single water garden object per plot.

Its subtype changes as water task count increases.

Example:

    object_type = lake
    object_subtype = small_pond / pond / lake / large_lake

---

## 10. Air System

Air represents inspiration, joy, creativity, and meaningful free time.

Air tasks should unlock decorative garden objects.

The key product mechanic:

    One Air reward object can be earned per user per day.

Even if the user completes multiple Air tasks in one day, only the first eligible Air task grants the daily Air reward.

Other Air tasks still count as completed tasks, but they do not grant additional daily objects.

---

## 11. Air Reward Catalog

The system should have a catalog of all possible Air decorative objects.

Recommended table:

    garden_reward_objects

Suggested fields:

    id
    code
    name
    element_type
    object_type
    object_subtype
    rarity
    asset_key
    description
    is_active
    created_at
    updated_at

Examples:

    code: bench
    name: Bench
    element_type: air
    object_type: decoration
    object_subtype: bench
    asset_key: air_bench

    code: table
    name: Table
    element_type: air
    object_type: decoration
    object_subtype: table
    asset_key: air_table

    code: torch
    name: Torch
    element_type: air
    object_type: decoration
    object_subtype: torch
    asset_key: air_torch

---

## 12. Daily Air Reward Schedule

The daily Air reward should be controlled by a maintainable schedule table.

Recommended table:

    daily_air_reward_schedule

Suggested fields:

    id
    journey_day
    reward_object_id
    is_active
    created_at
    updated_at

Example:

    journey_day | reward_object
    1           | bench
    2           | table
    3           | torch
    4           | paper_plane
    5           | wind_chime

This allows the product owner to keep adding new daily objects over time.

The reward is based on the user's journey day, not the global calendar day.

This means:

    User A Day 1 → Bench
    User B Day 1 → Bench
    User A Day 2 → Table
    User B Day 2 → Table

Users do not miss early rewards just because they joined later.

---

## 13. User Air Rewards

The system should store which Air rewards a user has earned.

Recommended table:

    user_air_rewards

Suggested fields:

    id
    user_id
    reward_object_id
    garden_plot_id
    source_task_id
    journey_day
    earned_date
    created_at

Important constraint:

    unique(user_id, earned_date)

This prevents users from earning more than one Air reward per day.

Air reward flow:

    1. User completes an Air task.
    2. Backend checks whether the user already earned an Air reward today.
    3. If yes, no new object is granted.
    4. If no, backend calculates user's journey_day.
    5. Backend finds reward_object_id from daily_air_reward_schedule.
    6. Backend creates user_air_rewards record.
    7. Backend creates garden_objects decoration record.

---

## 14. Missing Daily Air Reward Handling

The ideal system should have at least 30-60 days of Air rewards scheduled in advance.

If a journey day has no scheduled Air reward, the backend should not fail.

Fallback options:

- Option A: Grant a generic fallback inspiration object.
- Option B: Complete the Air task but return no reward.
- Option C: Use the latest active object pool and pick a default object.

For the MVP, use Option A.

Fallback object:

    code: inspiration_spark
    name: Inspiration Spark
    element_type: air
    object_type: decoration
    object_subtype: spark

This prevents users from feeling that the system is broken.

---

## 15. Garden Plot Unlocking

Garden plots unlock automatically based on journey day.

Rules:

    Journey Day 1-30
    → Plot 1 active

    Journey Day 31-60
    → Plot 2 active

    Journey Day 61-90
    → Plot 3 active

When a new plot is needed, backend creates it automatically.

Recommended table:

    garden_plots

Suggested fields:

    id
    user_id
    plot_index
    start_journey_day
    end_journey_day
    title
    status
    rows
    columns
    created_at
    updated_at

Example:

    plot_index: 1
    start_journey_day: 1
    end_journey_day: 30
    title: First Garden
    status: active
    rows: 10
    columns: 10

---

## 16. Current Plot Assignment

New garden objects should be assigned to the current plot.

Current plot is calculated from journey day.

Examples:

    Journey Day 15
    → Plot 1

    Journey Day 35
    → Plot 2

    Journey Day 75
    → Plot 3

Completed historical objects should remain in the plot where they were earned.

---

## 17. Fire System

Fire is not a separate task category.

Fire is an urgency state.

Fire can appear as an overlay on Earth tasks.

Rule:

    Urgent Earth task completed
    → garden object may include fire-related visual effect

Possible visual use:

    A completed urgent flower task
    → red-highlighted flower

    A completed urgent rock task
    → warm-colored path stone

Fire should not destroy real user progress.

Fire effects are visual and motivational, not destructive.

---

## 18. Frontend Direction

The current 8x8 MVP grid can be replaced later.

Garden V2 frontend should support:

- Scrollable garden plots
- Clickable objects
- Object detail panels
- Habit tree progress display
- Daily Air reward reveal
- Today's idle rocks
- Persistent path stones
- Water area growth
- Past plot viewing

Possible layouts:

    Horizontal scroll:
    Plot 1 → Plot 2 → Plot 3

    Vertical scroll:
    Month 1 Garden
    Month 2 Garden
    Month 3 Garden

MVP frontend can still use matrix positioning, but the visual design should later move toward a more playful and attractive garden world.

---

## 19. Backend Development Order

Recommended implementation order:

1. Garden plot system
2. Garden object model
3. Habit tree state and 30-day cycle system
4. Rock idle + path system
5. Air reward catalog and daily reward schedule
6. Water area growth system
7. Garden V2 API response
8. Garden V2 frontend

---

## 20. MVP Compatibility

The existing Garden MVP uses:

    garden_cells

Garden V2 should not immediately delete this system.

Development approach:

    1. Keep garden_cells temporarily.
    2. Add Garden V2 tables.
    3. Build new endpoints under /garden-v2.
    4. Test Garden V2 without breaking current Garden page.
    5. Later migrate or replace Garden MVP frontend.

This reduces risk and protects the currently working product.

---

## 21. Final Product Summary

GrowthEra Garden V2 should make users feel that their daily actions create a visible world.

The final metaphor:

- Flower = productive effort
- Tree = consistency and habits
- Path = daily responsibilities
- Water = awareness, care, and healing
- Air = inspiration, joy, and creativity

The Garden should grow over time through 30-day plots.

Users should feel:

    I am not just completing tasks.
    I am building a visible record of who I am becoming.