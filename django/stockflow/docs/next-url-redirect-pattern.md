# Next URL Redirect Pattern

## Overview
This pattern allows forms to redirect to different destinations after successful submission or cancellation, improving user experience by maintaining context. The system uses two separate parameters:
- **`next`**: For success redirects (after form submission)
- **`prev`**: For cancel redirects (when user cancels form)

## Implementation

### Views Pattern
```python
def get_success_redirect_url(self, instance):
    """Determine where to redirect after successful form submission."""
    # Check for next parameter in request (POST takes priority over GET)
    next_url = self.request.POST.get('next') or self.request.GET.get('next')
    if next_url:
        return next_url
    # Default redirect
    return reverse('app:detail-view', kwargs={'pk': instance.pk})

def get_prev_redirect_url(self):
    """Determine where to redirect when user cancels."""
    # Check for prev parameter in request
    prev_url = self.request.GET.get('prev')
    if prev_url:
        return prev_url
    # Default redirect
    return reverse('app:list-view')

def form_valid(self, form):
    # Save the form
    instance = form.save(commit=False)
    instance.updated_by = self.request.user
    instance.save()
    
    # Add success message
    messages.success(self.request, f'{model_name} was updated successfully.')
    
    # Use success redirect method
    success_url = self.get_success_redirect_url(instance)
    return redirect(success_url)

def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    # Pass URLs to template
    context['next_url'] = self.request.GET.get('next', '')
    context['prev_url'] = self.get_prev_redirect_url()
    return context
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

### Category Management

#### CategoryUpdateView
```python
class CategoryUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'catalog/category/category-form.html'
    permission_required = 'catalog.change_category'

    def get_success_redirect_url(self, category):
        """Determine where to redirect after successful update."""
        # Check for next parameter in request (POST takes priority over GET)
        next_url = self.request.POST.get('next') or self.request.GET.get('next')
        if next_url:
            return next_url
        # Default to category detail page
        return reverse('catalog:category-detail', kwargs={'pk': category.pk})
    
    def get_prev_redirect_url(self):
        """Determine where to redirect when user cancels."""
        # Check for prev parameter in request
        prev_url = self.request.GET.get('prev')
        if prev_url:
            return prev_url
        # Default to category detail page for update
        return reverse('catalog:category-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        category = form.save(commit=False)
        category.updated_by = self.request.user
        category.save()
        
        messages.success(self.request, f'Category "{category.name}" was updated successfully.')
        
        # Use success redirect method
        success_url = self.get_success_redirect_url(category)
        return redirect(success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['next_url'] = self.request.GET.get('next', '')
        context['prev_url'] = self.get_prev_redirect_url()
        return context
```

#### Category Detail Template
```html
<!-- Edit button with next and prev parameters -->
<a href="{% url 'catalog:category-edit' category.pk %}?next={{ request.get_full_path|urlencode }}&prev={{ request.get_full_path|urlencode }}" class="btn btn-primary">
    <i class="bi bi-pencil-square"></i> Edit Category
</a>
```

#### Category Form Template
```html
<form id="category-form" method="post">
    {% csrf_token %}
    
    {% if next_url %}
        <input type="hidden" name="next" value="{{ next_url }}">
    {% endif %}
    
    <!-- Form fields -->
</form>

{% block header_actions %}
<div class="btn-group" role="group">
    <button type="submit" form="category-form" class="btn btn-primary">
        <i class="bi bi-check-lg"></i> Save Category
    </button>
    <a href="{{ prev_url }}" class="btn btn-secondary">
        <i class="bi bi-arrow-left"></i> Cancel
    </a>
</div>
{% endblock %}
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
```python
from django.urls import reverse
from urllib.parse import urlparse

def form_valid(self, form):
    # ... save logic ...
    
    next_url = self.request.GET.get('next') or self.request.POST.get('next')
    if next_url:
        # Validate that next_url is from same domain
        parsed = urlparse(next_url)
        if not parsed.netloc or parsed.netloc == self.request.get_host():
            return redirect(next_url)
    
    return redirect('app:default-view')
```

### Best Practices
1. **Always validate next URLs** - Prevent open redirects
2. **Provide fallback URLs** - Default redirect if next is invalid
3. **Use urlencode filter** - Properly encode URLs in templates
4. **Check for both GET and POST** - Support both parameter methods

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

**Last Updated**: August 8, 2025  
**Version**: 2.0  
**Maintainer**: StockFlow Development Team
