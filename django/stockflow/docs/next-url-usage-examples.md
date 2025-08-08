# Next URL Usage Examples for Stock Movement Views

## Overview
The StockMovementCreateView and StockMovementUpdateView now support next URL functionality for both success and cancel scenarios.

## How it Works

### Success Redirect Priority (after form submission):
1. `next` parameter from GET or POST request
2. Default behavior (stock movement detail page)

### Cancel Redirect Priority (when clicking Cancel):
1. `next` parameter from GET request
2. Default behavior:
   - Create: Stock movement list
   - Update: Stock movement detail page

## Usage Examples

### 1. Creating Stock Movement with Redirect to Warehouse Page
```html
<!-- From warehouse detail page -->
<a href="{% url 'inventory:stock-movement-create' %}?next={% url 'inventory:warehouse-detail' warehouse.id %}" 
   class="btn btn-primary">
    <i class="bi bi-plus-circle me-1"></i>Add Stock Movement
</a>
```

### 2. Creating Stock Movement with Redirect to Stock Overview
```html
<!-- From stock overview page -->
<a href="{% url 'inventory:stock-movement-create' %}?next={% url 'inventory:stock-overview' %}" 
   class="btn btn-primary">
    <i class="bi bi-plus-circle me-1"></i>Add Movement
</a>
```

### 3. Editing Stock Movement with Custom Redirect
```html
<!-- From any page that wants custom redirect -->
<a href="{% url 'inventory:stock-movement-update' movement.id %}?next={{ request.get_full_path }}" 
   class="btn btn-outline-primary">
    <i class="bi bi-pencil me-1"></i>Edit
</a>
```

### 4. From URL Parameters
```
# Direct URL access with next parameter
/inventory/stockmovement/create/?next=/inventory/warehouse/1/
/inventory/stockmovement/1/edit/?next=/inventory/stock-overview/
```

## Form Behavior

### Success Cases:
- Form submission succeeds → redirects to `next` URL if provided, otherwise default
- Hidden input field preserves `next` parameter through POST request

### Cancel Cases:
- Cancel button → redirects to `next` URL if provided, otherwise default
- Header back button → same behavior as cancel button

## Template Variables Available

The template now has access to:
- `next_url`: The next parameter from GET request
- `cancel_url`: The computed cancel URL based on priority

## Implementation Details

### View Methods Added:
- `get_success_redirect_url(stock_movement)`: Determines success redirect
- `get_cancel_redirect_url()`: Determines cancel redirect
- Enhanced `get_context_data()`: Adds next_url and cancel_url to context

### Template Changes:
- Hidden input field for preserving next parameter
- Dynamic cancel URL in buttons
- Priority-based URL resolution
