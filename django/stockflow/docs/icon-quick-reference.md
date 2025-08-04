# Icon Quick Reference

## Common Icons Cheat Sheet

### Actions (สำหรับปุ่มและการกระทำ)
```html
<!-- CRUD Operations -->
<i class="bi bi-plus"></i>          <!-- Add/Create -->
<i class="bi bi-pencil-square"></i> <!-- Edit/Update -->
<i class="bi bi-trash"></i>         <!-- Delete -->
<i class="bi bi-eye"></i>           <!-- View/Read -->
<i class="bi bi-check-lg"></i>      <!-- Save/Confirm -->
<i class="bi bi-x-lg"></i>          <!-- Cancel/Close -->

<!-- Navigation -->
<i class="bi bi-list"></i>          <!-- List View -->
<i class="bi bi-grid"></i>          <!-- Grid View -->
<i class="bi bi-arrow-left"></i>    <!-- Back -->
<i class="bi bi-arrow-right"></i>   <!-- Forward -->
<i class="bi bi-house"></i>         <!-- Home -->
```

### Status & Feedback (สำหรับสถานะและการแจ้งเตือน)
```html
<i class="bi bi-check-circle"></i>        <!-- Success -->
<i class="bi bi-exclamation-triangle"></i> <!-- Warning -->
<i class="bi bi-x-circle"></i>            <!-- Error -->
<i class="bi bi-info-circle"></i>         <!-- Information -->
<i class="bi bi-arrow-clockwise"></i>     <!-- Loading -->
```

### Business Context (สำหรับงาน Inventory/Catalog)
```html
<i class="bi bi-folder"></i>         <!-- Categories -->
<i class="bi bi-box"></i>            <!-- Items/Products -->
<i class="bi bi-boxes"></i>          <!-- Inventory -->
<i class="bi bi-building"></i>       <!-- Warehouse -->
<i class="bi bi-diagram-3"></i>      <!-- BOM -->
<i class="bi bi-arrow-left-right"></i> <!-- Movement -->
```

### Data & Tools (สำหรับข้อมูลและเครื่องมือ)
```html
<i class="bi bi-bar-chart"></i>      <!-- Statistics -->
<i class="bi bi-gear"></i>           <!-- Settings -->
<i class="bi bi-search"></i>         <!-- Search -->
<i class="bi bi-funnel"></i>         <!-- Filter -->
<i class="bi bi-download"></i>       <!-- Download -->
<i class="bi bi-upload"></i>         <!-- Upload -->
```

## Template Patterns

### Card Header with Icon
```html
<div class="card-header">
    <h5 class="card-title mb-0">
        <i class="bi bi-info-circle me-2"></i>Category Information
    </h5>
</div>
```

### Button with Icon
```html
<button class="btn btn-outline-primary">
    <i class="bi bi-pencil me-2"></i>Edit Category
</button>
```

### Status Badge
```html
<span class="badge bg-success">
    <i class="bi bi-check-circle me-1"></i>Active
</span>
```

## Context Mapping for StockFlow

### Category Management
- **List**: `bi-list` - All Categories
- **Add**: `bi-plus` - Add Category  
- **Edit**: `bi-pencil` - Edit Category
- **Delete**: `bi-trash` - Delete Category
- **Info**: `bi-info-circle` - Category Information
- **Stats**: `bi-bar-chart` - Statistics

### Item Management  
- **Items**: `bi-box` - Items/Products
- **Add**: `bi-plus` - Add Item
- **Edit**: `bi-pencil` - Edit Item
- **BOM**: `bi-diagram-3` - Bill of Materials

### Inventory
- **Stock**: `bi-boxes` - Inventory Level
- **Movement**: `bi-arrow-left-right` - Stock Movement
- **Warehouse**: `bi-building` - Location

### Common UI Elements
- **Settings**: `bi-gear` - Quick Actions
- **Search**: `bi-search` - Search Items
- **Home**: `bi-house` - Dashboard
- **Warning**: `bi-exclamation-triangle` - Cannot delete
