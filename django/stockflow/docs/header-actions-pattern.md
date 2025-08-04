# Header Actions Pattern

## Overview
This document defines the standardized pattern for `header_actions` block across all templates that extend `base-dashboard-header.html`.

## Standard Pattern

### Structure
```html
{% block header_actions %}
{# Header Actions Pattern: Primary + Secondary - docs/header-actions-pattern.md #}
<div class="btn-group" role="group">
    <a href="{{ primary_action_url }}" class="btn btn-primary">
        <i class="bi bi-{{ primary_icon }}"></i> {{ primary_text }}
    </a>
    <a href="{{ back_url }}" class="btn btn-secondary">
        <i class="bi bi-arrow-left"></i> Back to {{ context }}
    </a>
</div>
{% endblock %}
```

### Rules
1. **Always use `btn-group`** - For consistent button grouping
2. **Exactly 2 buttons** - Primary action + Back navigation
3. **Primary button first** - Main action on the left
4. **Secondary button second** - Back navigation on the right
5. **Standard classes**: `btn btn-primary` และ `btn btn-secondary`

## Button Types

### Primary Button (Left)
- **Purpose**: Main action for the current page
- **Class**: `btn btn-primary`
- **Icon**: Context-appropriate Bootstrap icon
- **Examples**:
  - Detail pages: Edit action
  - List pages: Add new item
  - Form pages: Save/Submit

### Secondary Button (Right)  
- **Purpose**: Navigation back to previous context
- **Class**: `btn btn-secondary`
- **Icon**: `bi-arrow-left` (consistent across all pages)
- **Text Pattern**: "Back to [Context]"

## Context-Specific Examples

### Detail Pages
```html
{% block header_actions %}
{# Header Actions Pattern: Edit + Back - docs/header-actions-pattern.md #}
<div class="btn-group" role="group">
    <a href="{% url 'app:model-edit' object.pk %}" class="btn btn-primary">
        <i class="bi bi-pencil-square"></i> Edit [Model]
    </a>
    <a href="{% url 'app:model-list' %}" class="btn btn-secondary">
        <i class="bi bi-arrow-left"></i> Back to List
    </a>
</div>
{% endblock %}
```

### List Pages
```html
{% block header_actions %}
<div class="btn-group" role="group">
    <a href="{% url 'app:model-create' %}" class="btn btn-primary">
        <i class="bi bi-plus"></i> Add [Model]
    </a>
    <a href="{% url 'dashboard' %}" class="btn btn-secondary">
        <i class="bi bi-arrow-left"></i> Back to Dashboard
    </a>
</div>
{% endblock %}
```

### Form Pages (Create/Edit)
```html
{% block header_actions %}
<div class="btn-group" role="group">
    <button type="submit" form="main-form" class="btn btn-primary">
        <i class="bi bi-check-lg"></i> Save [Model]
    </button>
    <a href="{% url 'app:model-list' %}" class="btn btn-secondary">
        <i class="bi bi-arrow-left"></i> Back to List
    </a>
</div>
{% endblock %}
```

## Implementation Examples

### Category Management

#### Category Detail
```html
{% block header_actions %}
<div class="btn-group" role="group">
    <a href="{% url 'catalog:category-edit' category.pk %}" class="btn btn-primary">
        <i class="bi bi-pencil-square"></i> Edit Category
    </a>
    <a href="{% url 'catalog:category-list' %}" class="btn btn-secondary">
        <i class="bi bi-arrow-left"></i> Back to List
    </a>
</div>
{% endblock %}
```

#### Category List
```html
{% block header_actions %}
<div class="btn-group" role="group">
    <a href="{% url 'catalog:category-create' %}" class="btn btn-primary">
        <i class="bi bi-plus"></i> Add Category
    </a>
    <a href="{% url 'dashboard' %}" class="btn btn-secondary">
        <i class="bi bi-arrow-left"></i> Back to Dashboard
    </a>
</div>
{% endblock %}
```

#### Category Form (Create/Edit)
```html
{% block header_actions %}
<div class="btn-group" role="group">
    <button type="submit" form="category-form" class="btn btn-primary">
        <i class="bi bi-check-lg"></i> Save Category
    </button>
    <a href="{% url 'catalog:category-list' %}" class="btn btn-secondary">
        <i class="bi bi-arrow-left"></i> Back to List
    </a>
</div>
{% endblock %}
```

## Icon Reference

### Primary Action Icons
- **Add/Create**: `bi-plus`
- **Edit/Update**: `bi-pencil-square`
- **Save**: `bi-check-lg`
- **Submit**: `bi-send`
- **Process**: `bi-gear`

### Secondary Action Icon
- **Back Navigation**: `bi-arrow-left` (always use this icon)

## Comment Guidelines

### Template Header Comment
Every template should include a header comment documenting:
```html
{% extends 'base-template.html' %}
{% comment %}
  [Template Name] Template
  
  Design Patterns Used:
  - Base Template: [base template name]
  - Header Actions Pattern: [description] (docs/header-actions-pattern.md)
  - Icon System: Bootstrap Icons (docs/icon-design-system.md)
  - [Other patterns used]
  
  Blocks:
  - page_title: [description]
  - page_subtitle: [description]
  - header_actions: [description]
  - [other blocks]
{% endcomment %}

{% load static %}
```

**Important**: `{% extends %}` must always be the first line in Django templates.

### Inline Comments
Use single-line comments for inline documentation:
```html
{% block header_actions %}
{# Header Actions Pattern: Primary + Secondary - docs/header-actions-pattern.md #}
<div class="btn-group" role="group">
    <!-- buttons here -->
</div>
{% endblock %}
```

## Validation Checklist

### Before Implementation
- [ ] Uses `btn-group` wrapper
- [ ] Exactly 2 buttons
- [ ] Primary button uses `btn btn-primary`
- [ ] Secondary button uses `btn btn-secondary`
- [ ] Secondary button uses `bi-arrow-left` icon
- [ ] Text follows "Back to [Context]" pattern

### Code Review Points
- [ ] Button order: Primary → Secondary
- [ ] Consistent icon usage
- [ ] Proper URL patterns
- [ ] Semantic button text
- [ ] Accessibility considerations (aria-labels if needed)

## Common Mistakes to Avoid

❌ **Don't do**:
```html
<!-- Too many buttons -->
<div class="btn-group">
    <a href="#" class="btn btn-primary">Edit</a>
    <a href="#" class="btn btn-info">View</a>
    <a href="#" class="btn btn-secondary">Back</a>
</div>

<!-- Mixed button styles -->
<a href="#" class="btn btn-outline-primary">Edit</a>
<a href="#" class="btn btn-secondary">Back</a>

<!-- Wrong icon for back -->
<a href="#" class="btn btn-secondary">
    <i class="bi bi-house"></i> Back to List
</a>
```

✅ **Do**:
```html
<div class="btn-group" role="group">
    <a href="#" class="btn btn-primary">
        <i class="bi bi-pencil-square"></i> Edit Category
    </a>
    <a href="#" class="btn btn-secondary">
        <i class="bi bi-arrow-left"></i> Back to List
    </a>
</div>
```

---

**Last Updated**: August 3, 2025  
**Version**: 1.0  
**Maintainer**: StockFlow Development Team
