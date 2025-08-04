# Icon Design System

## Overview
This document defines the standardized icon usage across the StockFlow application using Bootstrap Icons (bi-*) for consistency and optimal performance.

## General Guidelines

### Icon Library
- **Primary**: Bootstrap Icons (`bi-*`)
- **Fallback**: None (avoid mixing icon libraries)
- **Size Classes**: Use Bootstrap's utility classes (`fs-1`, `fs-2`, etc.) for sizing

### Icon Spacing
- **With Text**: Use `me-1`, `me-2`, or `ms-1`, `ms-2` for spacing
- **Standalone**: No additional spacing needed

## Context-Based Icon Usage

### 1. CRUD Operations
| Action | Icon | Context | Example |
|--------|------|---------|---------|
| Create/Add | `bi-plus` | Adding new items | Add Category, Add Item |
| Read/View | `bi-eye` | Viewing details | View Details |
| Update/Edit | `bi-pencil-square` | Editing existing items | Edit Category, Edit Item |
| Delete | `bi-trash` | Deleting items | Delete Category |
| Save | `bi-check-lg` | Saving forms | Save Changes |
| Cancel | `bi-x-lg` | Canceling actions | Cancel Form |

### 2. Navigation & Lists
| Action | Icon | Context | Example |
|--------|------|---------|---------|
| List View | `bi-list` | Showing all items | All Categories |
| Grid View | `bi-grid` | Grid layout | Product Grid |
| Back/Return | `bi-arrow-left` | Navigation back | Back to List |
| Next/Forward | `bi-arrow-right` | Navigation forward | Next Page |
| Home | `bi-house` | Dashboard/Home | Dashboard |
| Menu | `bi-list` | Navigation menu | Main Menu |

### 3. Data & Information
| Type | Icon | Context | Example |
|------|------|---------|---------|
| Information | `bi-info-circle` | General info | Category Information |
| Statistics | `bi-bar-chart` | Data visualization | Sales Statistics |
| Reports | `bi-file-earmark-text` | Report generation | Monthly Report |
| Search | `bi-search` | Search functionality | Search Items |
| Filter | `bi-funnel` | Filtering data | Filter Results |
| Sort | `bi-sort-down` / `bi-sort-up` | Sorting data | Sort by Name |

### 4. Status & Feedback
| Status | Icon | Context | Example |
|--------|------|---------|---------|
| Success | `bi-check-circle` | Successful operations | Save Success |
| Warning | `bi-exclamation-triangle` | Warning messages | Delete Warning |
| Error | `bi-x-circle` | Error states | Validation Error |
| Loading | `bi-arrow-clockwise` | Loading states | Processing |
| Active/On | `bi-toggle-on` | Active status | Active Category |
| Inactive/Off | `bi-toggle-off` | Inactive status | Inactive Item |

### 5. Settings & Configuration
| Action | Icon | Context | Example |
|--------|------|---------|---------|
| Settings | `bi-gear` | Configuration | Quick Actions |
| Preferences | `bi-sliders` | User preferences | User Settings |
| Tools | `bi-tools` | System tools | Admin Tools |
| Download | `bi-download` | File download | Export Data |
| Upload | `bi-upload` | File upload | Import Data |
| Print | `bi-printer` | Print functionality | Print Report |

### 6. Business Context (Inventory/Catalog)
| Context | Icon | Usage | Example |
|---------|------|-------|---------|
| Categories | `bi-folder` | Category management | Category List |
| Items/Products | `bi-box` | Item/Product management | Item Details |
| Inventory | `bi-boxes` | Stock management | Inventory Level |
| Warehouse | `bi-building` | Location management | Warehouse Info |
| Movement | `bi-arrow-left-right` | Stock movement | Stock Transfer |
| BOM | `bi-diagram-3` | Bill of Materials | BOM Structure |

### 7. User & Authentication
| Context | Icon | Usage | Example |
|---------|------|-------|---------|
| User Profile | `bi-person` | User information | User Profile |
| Login | `bi-box-arrow-in-right` | Login action | Sign In |
| Logout | `bi-box-arrow-right` | Logout action | Sign Out |
| Permissions | `bi-shield-check` | Access control | User Permissions |

## Size Guidelines

### Icon Sizes by Context
- **Page Headers**: `fs-4` or larger
- **Card Headers**: `fs-5` 
- **Buttons**: Default size (no class needed)
- **Small Text**: `fs-6`
- **Large Actions**: `fs-3`

### Button Icon Guidelines
```html
<!-- Primary Action Button -->
<button class="btn btn-primary">
    <i class="bi bi-plus me-2"></i>Add Item
</button>

<!-- Icon-only Button -->
<button class="btn btn-outline-secondary">
    <i class="bi bi-pencil"></i>
</button>

<!-- Small Button -->
<button class="btn btn-sm btn-outline-danger">
    <i class="bi bi-trash"></i>
</button>
```

## Color Guidelines

### Semantic Colors
- **Success Actions**: Use with `text-success` - `bi-check-circle`
- **Warning Actions**: Use with `text-warning` - `bi-exclamation-triangle`
- **Danger Actions**: Use with `text-danger` - `bi-trash`, `bi-x-circle`
- **Info Actions**: Use with `text-info` - `bi-info-circle`
- **Primary Actions**: Use with `text-primary` - `bi-pencil`, `bi-plus`

## Common Patterns

### Card Headers
```html
<div class="card-header">
    <h6 class="card-title mb-0">
        <i class="bi bi-[context-icon] me-2"></i>[Title]
    </h6>
</div>
```

### Action Buttons
```html
<!-- Edit Action -->
<a href="#" class="btn btn-outline-primary">
    <i class="bi bi-pencil me-2"></i>Edit
</a>

<!-- Delete Action -->
<button type="button" class="btn btn-outline-danger">
    <i class="bi bi-trash me-2"></i>Delete
</button>
```

### Status Indicators
```html
<!-- Active Status -->
<span class="badge bg-success">
    <i class="bi bi-check-circle me-1"></i>Active
</span>

<!-- Warning Status -->
<span class="text-warning">
    <i class="bi bi-exclamation-triangle me-1"></i>Warning Message
</span>
```

## Implementation Checklist

### Before Adding Icons
- [ ] Check this guide for appropriate icon
- [ ] Ensure consistent spacing (`me-1`, `me-2`, etc.)
- [ ] Use semantic colors when appropriate
- [ ] Test icon visibility and accessibility
- [ ] Verify icon makes sense in context

### Code Review Points
- [ ] Icons follow established patterns
- [ ] No mixing of icon libraries (only Bootstrap Icons)
- [ ] Proper spacing classes used
- [ ] Semantic meaning matches visual representation
- [ ] Consistent sizing within similar contexts

## Future Considerations

### Custom Icons
If Bootstrap Icons doesn't provide needed icons:
1. Create custom SVG icons following Bootstrap's style
2. Document new icons in this guide
3. Ensure they match Bootstrap's visual weight and style

### Accessibility
- Always provide proper `aria-label` for icon-only buttons
- Ensure sufficient color contrast
- Don't rely solely on icons for meaning - include text when possible

---

**Last Updated**: August 3, 2025  
**Version**: 1.0  
**Maintainer**: StockFlow Development Team
