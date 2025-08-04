# Django Template Structure Guidelines

## Template File Structure

### Required Order
Django templates must follow this exact order:

1. **`{% extends %}` tag** - MUST be first line
2. **Documentation comment** - Using `{% comment %}`
3. **`{% load %}` tags** - Load template libraries
4. **Template blocks** - Content blocks

### Example Structure
```html
{% extends 'base-template.html' %}
{% comment %}
  Template documentation here
{% endcomment %}

{% load static %}
{% load custom_tags %}

{% block title %}Page Title{% endblock %}

{% block content %}
<!-- Template content -->
{% endblock %}
```

## Documentation Comment Format

### Required Information
```html
{% comment %}
  [Template Name] Template
  
  Design Patterns Used:
  - Base Template: [base template name]
  - [Pattern Name]: [description] (docs/pattern-file.md)
  - [Other patterns]
  
  Blocks:
  - block_name: [description]
  - [other blocks]
  
  Dependencies:
  - [Required libraries/apps]
  
  Notes:
  - [Any special considerations]
{% endcomment %}
```

### Example - Category Detail Template
```html
{% extends 'base-dashboard-header.html' %}
{% comment %}
  Category Detail Template
  
  Design Patterns Used:
  - Base Template: base-dashboard-header.html
  - Header Actions Pattern: Primary + Back navigation (docs/header-actions-pattern.md)
  - Icon System: Bootstrap Icons (docs/icon-design-system.md)
  - Delete Modal: AJAX DELETE with confirmation
  
  Blocks:
  - page_title: Category name for browser tab
  - title_text: Main heading (category name)
  - subtitle_text: Page description
  - header_actions: Edit + Back buttons
  - dashboard_content: Main content area
  
  Dependencies:
  - catalog app models
  - Bootstrap Modal JS
  
  Notes:
  - Uses AJAX for delete operations
  - Includes next URL redirect pattern
{% endcomment %}

{% load static %}
```

## Common Mistakes

### ❌ Wrong Order
```html
{% load static %}
{% extends 'base.html' %}  <!-- ERROR: extends must be first -->
```

### ❌ Missing Documentation
```html
{% extends 'base.html' %}
{% load static %}
<!-- No documentation comment -->
```

### ❌ Poor Documentation
```html
{% extends 'base.html' %}
{% comment %}
  Some template
{% endcomment %}
<!-- Insufficient documentation -->
```

## Block Naming Conventions

### Standard Block Names
- `title` - Browser tab title
- `page_title` - Main page heading
- `subtitle_text` - Page description
- `header_actions` - Action buttons in header
- `content` / `dashboard_content` - Main content area
- `extra_css` - Additional CSS files
- `extra_js` - Additional JavaScript files

### Custom Block Naming
- Use descriptive names: `category_form`, `item_list`, `statistics_panel`
- Follow snake_case convention
- Be specific: `product_actions` vs `actions`

## Load Tag Guidelines

### Common Load Tags
```html
{% load static %}          <!-- For static files -->
{% load widget_tweaks %}   <!-- For form widget customization -->
{% load humanize %}        <!-- For human-readable formats -->
{% load custom_tags %}     <!-- Project-specific tags -->
```

### Order of Load Tags
```html
{% load static %}
{% load widget_tweaks %}
{% load humanize %}
{% load custom_tags %}
```

## Validation Checklist

### Template Structure
- [ ] `{% extends %}` is first line
- [ ] Documentation comment exists
- [ ] Documentation is complete and accurate
- [ ] Load tags are properly ordered
- [ ] Block names follow conventions

### Documentation Quality
- [ ] Template purpose is clear
- [ ] Design patterns are documented
- [ ] Required blocks are listed
- [ ] Dependencies are noted
- [ ] Special features are explained

### Code Review Points
- [ ] Extends tag placement
- [ ] Documentation completeness
- [ ] Pattern consistency
- [ ] Block naming conventions
- [ ] Load tag organization

## Template Inheritance Hierarchy

### Project Structure
```
base.html
├── dashboard.html
│   ├── base-dashboard-header.html
│   │   ├── category-detail.html
│   │   ├── category-form.html
│   │   └── category-list.html
│   └── inventory-dashboard.html
└── auth.html
    ├── login.html
    └── register.html
```

### Documentation Inheritance
Each template should document:
- Immediate parent template
- Design patterns used at this level
- Blocks added or modified
- Dependencies introduced

---

**Last Updated**: August 4, 2025  
**Version**: 1.0  
**Maintainer**: StockFlow Development Team
