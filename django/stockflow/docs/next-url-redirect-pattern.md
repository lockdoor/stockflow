# Next URL Redirect Pattern

## Overview
This pattern allows forms to redirect to different destinations after successful submission or cancellation, improving user experience by maintaining context. The system uses two separate parameters:
- **`next`**: For success redirects (after form submission)
- **`prev`**: For cancel redirects (when user cancels form)

## Mixin-Based Implementation

### RedirectMixin Architecture
The system now uses a mixin-based approach with `RedirectMixin` and specialized mixins like `StockMovementRedirectMixin`.

```python
from common.mixins.redirect import RedirectMixin, StockMovementRedirectMixin

class MyCreateView(RedirectMixin, CreateView):
    """Generic view using base RedirectMixin."""
    
    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.created_by = self.request.user
        instance.save()
        
        # Use mixin's redirect method
        return self.redirect_success(instance)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['next_url'] = self.request.GET.get('next', '')
        context['prev_url'] = self.get_prev_redirect_url()
        return context

class StockMovementCreateView(StockMovementRedirectMixin, CreateView):
    """Specialized view using StockMovementRedirectMixin."""
    
    def form_valid(self, form):
        stock_movement = form.save(commit=False)
        stock_movement.created_by = self.request.user
        stock_movement.save()
        
        # Use mixin's redirect method - handles all redirect logic
        return self.redirect_success(stock_movement)
```

### Mixin Methods Available
```python
# Core redirect methods
self.get_success_redirect_url(obj=None)  # Determines success redirect
self.get_prev_redirect_url(obj=None)     # Determines cancel redirect

# Helper methods for easy redirection
self.redirect_success(obj=None)          # Returns HttpResponseRedirect for success
self.redirect_prev(obj=None)             # Returns HttpResponseRedirect for cancel

# Override these for custom defaults
self.get_default_success_url(obj=None)   # Default success URL
self.get_default_prev_url(obj=None)      # Default cancel URL
```

### Template Pattern

#### Links to Forms
```html
<!-- From detail page to edit form -->
<a href="{% url 'app:model-edit' object.pk %}?next={{ request.get_full_path|urlencode }}&prev={{ request.get_full_path|urlencode }}">
    Edit
</a>

<!-- From list page to create form -->
<a href="{% url 'app:model-create' %}?next={{ request.get_full_path|urlencode }}&prev={{ request.get_full_path|urlencode }}">
    Add New
</a>

<!-- Different destinations for success vs cancel -->
<a href="{% url 'app:model-create' %}?next={% url 'app:dashboard' %}&prev={{ request.get_full_path|urlencode }}">
    Add New (redirect to dashboard on success, back here on cancel)
</a>
```

#### Form Template
```html
<form id="model-form" method="post">
    {% csrf_token %}
    
    <!-- Hidden field for next URL (success redirect) -->
    {% if next_url %}
        <input type="hidden" name="next" value="{{ next_url }}">
    {% endif %}
    
    <!-- Form fields here -->
</form>

<!-- Header actions with cancel link -->
{% block header_actions %}
<div class="btn-group" role="group">
    <button type="submit" form="model-form" class="btn btn-primary">
        <i class="bi bi-check-lg"></i> Save
    </button>
    <a href="{{ prev_url }}" class="btn btn-secondary">
        <i class="bi bi-arrow-left"></i> Cancel
    </a>
</div>
{% endblock %}
```

## Usage Examples

### Stock Movement Management (Current Implementation)

#### StockMovementCreateView
```python
from common.mixins.redirect import StockMovementRedirectMixin

class StockMovementCreateView(StockMovementRedirectMixin, WarehousePermissionMixin, LoginRequiredMixin, CreateView):
    model = StockMovement
    form_class = StockMovementForm
    template_name = 'inventory/stock-movement/stock-movement-form.html'
    permission_required_base = 'add_stockmovement'

    def form_valid(self, form):
        try:
            stock_movement = form.save(commit=False)
            stock_movement.created_by = self.request.user
            stock_movement.updated_by = self.request.user
            stock_movement.save()
            
            # Use mixin's redirect method
            return self.redirect_success(stock_movement)
        except ValueError as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['next_url'] = self.request.GET.get('next', '')
        context['prev_url'] = self.get_prev_redirect_url()
        return context
```

#### Custom Model Example (Using Base RedirectMixin)
```python
from common.mixins.redirect import RedirectMixin

class CategoryUpdateView(RedirectMixin, LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'catalog/category/category-form.html'
    permission_required = 'catalog.change_category'

    def form_valid(self, form):
        category = form.save(commit=False)
        category.updated_by = self.request.user
        category.save()
        
        messages.success(self.request, f'Category "{category.name}" was updated successfully.')
        
        # Use mixin's redirect method
        return self.redirect_success(category)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['next_url'] = self.request.GET.get('next', '')
        context['prev_url'] = self.get_prev_redirect_url()
        return context
    
    # Override defaults if needed
    def get_default_success_url(self, category=None):
        if category:
            return reverse('catalog:category-detail', kwargs={'pk': category.pk})
        return reverse('catalog:category-list')
```

## Creating Custom Redirect Mixins

### Specialized Mixins
You can create specialized mixins for different model types:

```python
# In common/mixins/redirect.py
class CategoryRedirectMixin(RedirectMixin):
    """Specialized redirect mixin for Category views."""
    
    def get_default_success_url(self, category=None):
        if category:
            return reverse('catalog:category-detail', kwargs={'pk': category.pk})
        return reverse('catalog:category-list')
    
    def get_default_prev_url(self, category=None):
        if category and hasattr(self, 'object') and self.object:
            # For update operations, prefer detail page
            return reverse('catalog:category-detail', kwargs={'pk': category.pk})
        return reverse('catalog:category-list')

class ProductionOrderRedirectMixin(RedirectMixin):
    """Specialized redirect mixin for ProductionOrder views."""
    
    def get_default_success_url(self, production_order=None):
        if production_order:
            return reverse('production:production-order-detail', kwargs={'pk': production_order.pk})
        return reverse('production:production-order-list')
```

### Usage in Views
```python
from common.mixins.redirect import CategoryRedirectMixin

class CategoryCreateView(CategoryRedirectMixin, CreateView):
    model = Category
    form_class = CategoryForm
    
    def form_valid(self, form):
        category = form.save(commit=False)
        category.created_by = self.request.user
        category.save()
        
        # Automatically uses CategoryRedirectMixin defaults
        return self.redirect_success(category)
```

## User Experience Flow

### Parameters Usage
- **`next`**: Controls where to go after successful form submission
- **`prev`**: Controls where to go when user cancels the form

### Scenario 1: Edit from Detail Page
1. User views Category Detail page
2. Clicks "Edit Category" → Goes to form with `?next=/category/detail/1/&prev=/category/detail/1/`
3. **Success**: Submits form → Redirects to Category Detail page (using `next`)
4. **Cancel**: Clicks Cancel → Redirects to Category Detail page (using `prev`)

### Scenario 2: Edit from List Page  
1. User views Category List page
2. Clicks "Edit" on a category → Goes to form with `?next=/category/list/&prev=/category/list/`
3. **Success**: Submits form → Redirects to Category List page (using `next`)
4. **Cancel**: Clicks Cancel → Redirects to Category List page (using `prev`)

### Scenario 3: Different Success/Cancel Destinations
1. User views Dashboard
2. Clicks "Add Category" → Goes to form with `?next=/dashboard/&prev=/category/list/`
3. **Success**: Submits form → Redirects to Dashboard (using `next`)
4. **Cancel**: Clicks Cancel → Redirects to Category List (using `prev`)

## Security Considerations

### URL Validation
The `RedirectMixin` includes basic URL validation, but you can enhance it:

```python
from django.urls import reverse
from urllib.parse import urlparse

class SecureRedirectMixin(RedirectMixin):
    """Enhanced redirect mixin with additional security."""
    
    def get_success_redirect_url(self, obj=None):
        next_url = self.request.POST.get('next') or self.request.GET.get('next')
        if next_url:
            # Validate that next_url is from same domain
            parsed = urlparse(next_url)
            if not parsed.netloc or parsed.netloc == self.request.get_host():
                return next_url
        
        return self.get_default_success_url(obj)
```

### Best Practices
1. **Use specialized mixins** - Create model-specific mixins for consistent behavior
2. **Override defaults when needed** - Customize default URLs for specific use cases
3. **Always validate URLs** - Prevent open redirects in custom implementations
4. **Use helper methods** - Use `redirect_success()` and `redirect_prev()` for cleaner code
5. **Test redirect flows** - Verify all success and cancel paths work correctly

## Mixin Architecture Benefits

### Code Reusability
- Single implementation for all redirect logic
- Consistent behavior across all views
- Easy to extend and customize

### Maintainability  
- Centralized redirect logic in `/common/mixins/redirect.py`
- No duplicate code across views
- Easy to update behavior globally

### Current Implementations
The following views currently use redirect mixins:
- `StockMovementCreateView` - Uses `StockMovementRedirectMixin`
- `StockMovementUpdateView` - Uses `StockMovementRedirectMixin`  
- `StockMovementDeleteView` - Uses `StockMovementRedirectMixin`
- `StockMovementConfirmView` - Uses `StockMovementRedirectMixin`

## Common Use Cases

### Modal Forms
```html
<!-- Button to open modal form -->
<button data-bs-toggle="modal" data-bs-target="#editModal" 
        data-url="{% url 'app:model-edit' object.pk %}?next={{ request.get_full_path|urlencode }}">
    Edit
</button>
```

### AJAX Forms
```javascript
// Include next URL in AJAX form submission
$('#form').on('submit', function(e) {
    const nextUrl = $('#next-url').val();
    // ... AJAX submission ...
    // On success: window.location.href = nextUrl || defaultUrl;
});
```

---

**Last Updated**: September 2, 2025  
**Version**: 3.0 - Mixin Architecture  
**Maintainer**: StockFlow Development Team
