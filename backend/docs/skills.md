# Skills

## Category multipliers

The `SkillService.get_category_multiplier(user_id, category)` helper returns a
multiplier based on the average level of a user's skills within the specified
category.

```
multiplier = 1 + (avg_level / 200)
```

The multiplier can be used by other services to scale outcomes like gig
attendance, fame gains or recording quality.
