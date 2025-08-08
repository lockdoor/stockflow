# Next URL Usage Examples for Stock Movement Views

## Overview
The StockMovementCreateView and StockMovementUpdateView now support separate redirect parameters for success and cancel scenarios:
- **`next`**: For success redirects (after form submission)
- **`prev`**: For cancel redirects (when user cancels)

## How it Works

### Success Redirect Priority (after form submission):
1. `next` parameter from GET or POST request
2. Default behavior (stock movement detail page)

### Cancel Redirect Priority (when clicking Cancel):
1. `prev` parameter from GET request
2. Default behavior:
   - Create: Stock movement list
   - Update: Stock movement detail page

## Usage Examples

### 1. Creating Stock Movement with Different Success/Cancel Destinations
```html
<!-- From warehouse detail page -->
<a href="{% url 'inventory:stock-movement-create' %}?next={% url 'inventory:warehouse-detail' warehouse.id %}&prev={{ request.get_full_path|urlencode }}" 
   class="btn btn-primary">
    <i class="bi bi-plus-circle me-1"></i>Add Stock Movement
</a>
<!-- Success: Goes to warehouse detail, Cancel: Back to current page -->
```

### 2. Creating Stock Movement with Redirect to Stock Overview
```html
<!-- From stock overview page -->
<a href="{% url 'inventory:stock-movement-create' %}?next={% url 'inventory:stock-overview' %}&prev={% url 'inventory:stock-movement-list' %}" 
   class="btn btn-primary">
    <i class="bi bi-plus-circle me-1"></i>Add Movement
</a>
<!-- Success: Goes to stock overview, Cancel: Goes to movement list -->
```

### 3. Editing Stock Movement with Same Destination for Both
```html
<!-- From any page where both success and cancel should return here -->
<a href="{% url 'inventory:stock-movement-update' movement.id %}?next={{ request.get_full_path|urlencode }}&prev={{ request.get_full_path|urlencode }}" 
   class="btn btn-outline-primary">
    <i class="bi bi-pencil me-1"></i>Edit
</a>
<!-- Both success and cancel return to current page -->
```

### 4. From URL Parameters
```
# Direct URL access with both parameters
/inventory/stockmovement/create/?next=/inventory/warehouse/1/&prev=/inventory/dashboard/
/inventory/stockmovement/1/edit/?next=/inventory/stock-overview/&prev=/inventory/stockmovement/list/
```

## Form Behavior

### Success Cases:
- Form submission succeeds → redirects to `next` URL if provided, otherwise default
- Hidden input field preserves `next` parameter through POST request

### Cancel Cases:
- Cancel button → redirects to `prev` URL if provided, otherwise default
- Header back button → same behavior as cancel button

## Template Variables Available

The template now has access to:
- `next_url`: The next parameter from GET request (for success redirects)
- `prev_url`: The computed cancel URL based on prev parameter (for cancel redirects)

## Implementation Details

### View Methods Added:
- `get_success_redirect_url(stock_movement)`: Determines success redirect using `next`
- `get_prev_redirect_url()`: Determines cancel redirect using `prev`
- Enhanced `get_context_data()`: Adds next_url and prev_url to context

### Template Changes:
- Hidden input field for preserving next parameter
- Dynamic cancel URL in buttons using prev_url
- Separate parameter handling for different redirect scenarios
