# Next URL Usage Examples for Redirect Mixins

## Overview
The StockFlow application now uses a mixin-based approach for handling redirects. Views inherit from `RedirectMixin` or specialized mixins like `StockMovementRedirectMixin` to provide consistent redirect behavior:
- **`next`**: For success redirects (after form submission)
- **`prev`**: For cancel redirects (when user cancels)

## Mixin-Based Architecture

### Available Mixins
```python
# Base mixin for all views
from common.mixins.redirect import RedirectMixin

# Specialized mixin for StockMovement views  
from common.mixins.redirect import StockMovementRedirectMixin
```

### View Implementation
```python
class StockMovementCreateView(StockMovementRedirectMixin, CreateView):
    def form_valid(self, form):
        stock_movement = form.save(commit=False)
        stock_movement.created_by = self.request.user
        stock_movement.save()
        
        # Mixin handles all redirect logic automatically
        return self.redirect_success(stock_movement)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['next_url'] = self.request.GET.get('next', '')
        context['prev_url'] = self.get_prev_redirect_url()
        return context
```

## How the Mixin System Works

### Redirect Priority Logic
The mixin system automatically handles redirect priorities:

#### Success Redirect Priority (after form submission):
1. `next` parameter from POST request (form submission)
2. `next` parameter from GET request (original link)
3. Default success URL from mixin (`StockMovementRedirectMixin` → detail page)

#### Cancel Redirect Priority (when clicking Cancel):
1. `prev` parameter from GET request  
2. Default previous URL from mixin:
   - **Create views**: List page
   - **Update/Delete views**: Detail page

### Mixin Methods Available
```python
# In your views, these methods are automatically available:
self.redirect_success(obj)           # Redirect using success logic
self.redirect_prev(obj)              # Redirect using cancel logic
self.get_success_redirect_url(obj)   # Get success URL
self.get_prev_redirect_url(obj)      # Get cancel URL
```

## Usage Examples

### 1. Creating Stock Movement with Different Success/Cancel Destinations
```html
<!-- From warehouse detail page -->
<a href="{% url 'inventory:stock-movement-create' %}?next={% url 'inventory:warehouse-detail' warehouse.id %}&prev={{ request.get_full_path|urlencode }}" 
   class="btn btn-primary">
    <i class="bi bi-plus-circle me-1"></i>Add Stock Movement
</a>
<!-- 
Mixin behavior:
- Success: Redirects to warehouse detail (using next parameter)
- Cancel: Returns to current page (using prev parameter)
-->
```

### 2. Creating Stock Movement with Redirect to Stock Overview
```html
<!-- From stock overview page -->
<a href="{% url 'inventory:stock-movement-create' %}?next={% url 'inventory:stock-overview' %}&prev={% url 'inventory:stock-movement-list' %}" 
   class="btn btn-primary">
    <i class="bi bi-plus-circle me-1"></i>Add Movement
</a>
<!-- 
Mixin behavior:
- Success: Goes to stock overview (using next parameter)
- Cancel: Goes to movement list (using prev parameter)
-->
```

### 3. Using Default Mixin Behavior
```html
<!-- Simple link without parameters - uses mixin defaults -->
<a href="{% url 'inventory:stock-movement-create' %}" class="btn btn-primary">
    <i class="bi bi-plus-circle me-1"></i>Add Movement
</a>
<!-- 
Default StockMovementRedirectMixin behavior:
- Success: Goes to stock movement detail page (new movement)
- Cancel: Goes to stock movement list page
-->
```

### 4. Editing Stock Movement with Same Destination for Both
```html
<!-- From any page where both success and cancel should return here -->
<a href="{% url 'inventory:stock-movement-update' movement.id %}?next={{ request.get_full_path|urlencode }}&prev={{ request.get_full_path|urlencode }}" 
   class="btn btn-outline-primary">
    <i class="bi bi-pencil me-1"></i>Edit
</a>
<!-- Both success and cancel return to current page -->
```

### 5. Production Order Integration
```html
<!-- From production order detail page -->
<a href="{% url 'inventory:stock-movement-create' %}?reference_type=production_order&reference_id={{ production_order.id }}&next={% url 'production:production-order-detail' production_order.id %}&prev={{ request.get_full_path|urlencode }}" 
   class="btn btn-success">
    <i class="bi bi-box-arrow-up me-1"></i>Withdraw Materials
</a>
<!-- 
Mixin behavior with additional context:
- Pre-fills form with production order reference
- Success: Returns to production order detail
- Cancel: Returns to current page
-->
```

### 6. From URL Parameters (Direct Access)
```
# Direct URL access with both parameters
/inventory/stockmovement/create/?next=/inventory/warehouse/1/&prev=/inventory/dashboard/
/inventory/stockmovement/1/edit/?next=/inventory/stock-overview/&prev=/inventory/stockmovement/list/

# With production order context
/inventory/stockmovement/create/?reference_type=production_order&reference_id=123&next=/production/order/123/&prev=/production/order/list/
```

## Mixin Implementation Details

### StockMovementRedirectMixin Defaults
```python
# Success URLs (after successful form submission)
- Create: /inventory/stockmovement/{new_id}/     # New movement detail
- Update: /inventory/stockmovement/{id}/         # Updated movement detail  
- Delete: /inventory/stockmovement/list/         # Movement list
- Confirm: /inventory/stockmovement/{id}/        # Confirmed movement detail

# Cancel URLs (when user clicks cancel)
- Create: /inventory/stockmovement/list/         # Movement list
- Update: /inventory/stockmovement/{id}/         # Current movement detail
- Delete: /inventory/stockmovement/{id}/         # Current movement detail
- Confirm: /inventory/stockmovement/{id}/        # Current movement detail
```

### Creating Custom Mixins
```python
# Example: Custom mixin for other models
class WarehouseRedirectMixin(RedirectMixin):
    def get_default_success_url(self, warehouse=None):
        if warehouse:
            return reverse('inventory:warehouse-detail', kwargs={'pk': warehouse.pk})
        return reverse('inventory:warehouse-list')
    
    def get_default_prev_url(self, warehouse=None):
        if warehouse and hasattr(self, 'object') and self.object:
            return reverse('inventory:warehouse-detail', kwargs={'pk': warehouse.pk})
        return reverse('inventory:warehouse-list')
```

## Template Integration

### Form Templates
The template system automatically receives context variables from the mixin:

```html
<form id="stock-movement-form" method="post">
    {% csrf_token %}
    
    <!-- Hidden field for next URL (success redirect) -->
    <!-- This is automatically available from mixin context -->
    {% if next_url %}
        <input type="hidden" name="next" value="{{ next_url }}">
    {% endif %}
    
    <!-- Form fields here -->
</form>

<!-- Header actions with cancel link -->
{% block header_actions %}
<div class="btn-group" role="group">
    <button type="submit" form="stock-movement-form" class="btn btn-primary">
        <i class="bi bi-check-lg"></i> Save
    </button>
    <!-- prev_url is automatically computed by mixin -->
    <a href="{{ prev_url }}" class="btn btn-secondary">
        <i class="bi bi-arrow-left"></i> Cancel
    </a>
</div>
{% endblock %}
```

### Template Variables Available
The mixin automatically provides these context variables:
- `next_url`: The next parameter from GET request (for hidden form field)
- `prev_url`: The computed cancel URL (for cancel button)

### Currently Implemented Views
These views use `StockMovementRedirectMixin`:
- `StockMovementCreateView` - `/inventory/stockmovement/create/`
- `StockMovementUpdateView` - `/inventory/stockmovement/{id}/edit/`
- `StockMovementDeleteView` - `/inventory/stockmovement/{id}/delete/`
- `StockMovementConfirmView` - `/inventory/stockmovement/{id}/confirm/`

## User Experience Scenarios

### Scenario 1: Material Withdrawal from Production Order
1. User views Production Order Detail page (`/production/order/123/`)
2. Clicks "Withdraw Materials" button with parameters:
   ```
   ?reference_type=production_order&reference_id=123
   &next=/production/order/123/&prev=/production/order/123/
   ```
3. **Success Flow**: 
   - Submits withdrawal form
   - `StockMovementRedirectMixin.redirect_success()` processes `next` parameter
   - Returns to Production Order Detail page
4. **Cancel Flow**: 
   - Clicks Cancel button
   - `prev_url` from template context leads back to Production Order Detail page

### Scenario 2: Quick Stock Movement from Warehouse
1. User views Warehouse Detail page (`/inventory/warehouse/5/`)
2. Clicks "Add Movement" → Form with `?next=/inventory/warehouse/5/&prev=/inventory/warehouse/5/`
3. **Success Flow**: Returns to Warehouse Detail (using `next`)
4. **Cancel Flow**: Returns to Warehouse Detail (using `prev`)

### Scenario 3: Default Behavior (No Parameters)
1. User accesses Stock Movement Create directly (`/inventory/stockmovement/create/`)
2. **Success Flow**: 
   - `StockMovementRedirectMixin.get_default_success_url()` is used
   - Redirects to new movement detail page
3. **Cancel Flow**: 
   - `StockMovementRedirectMixin.get_default_prev_url()` is used  
   - Redirects to movement list page

## Benefits of Mixin Architecture

### Code Maintainability
- ✅ **Single source of truth**: All redirect logic in `/common/mixins/redirect.py`
- ✅ **No code duplication**: Removed ~80 lines of duplicate code from views
- ✅ **Consistent behavior**: All views follow same redirect patterns
- ✅ **Easy testing**: Centralized logic is easier to test

### Developer Experience  
- ✅ **Simple to use**: Just inherit from mixin and call `self.redirect_success(obj)`
- ✅ **Flexible**: Can override defaults or create specialized mixins
- ✅ **Clear intent**: Methods like `redirect_success()` are self-documenting

### User Experience
- ✅ **Predictable navigation**: Consistent redirect behavior across the application
- ✅ **Context preservation**: Users return to where they came from
- ✅ **Flexible workflows**: Different redirect destinations for different contexts

---

**Last Updated**: September 2, 2025  
**Version**: 3.0 - Mixin Architecture  
**Maintainer**: StockFlow Development Team
