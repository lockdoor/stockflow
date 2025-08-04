# Next URL Redirect Pattern

## Overview
This pattern allows forms to redirect back to the originating page after successful submission, improving user experience by maintaining context.

## Implementation

### Views Pattern
```python
def form_valid(self, form):
    # Save the form
    instance = form.save(commit=False)
    instance.updated_by = self.request.user
    instance.save()
    
    # Add success message
    messages.success(self.request, f'{model_name} was updated successfully.')
    
    # Redirect to next URL if provided, otherwise default
    next_url = self.request.GET.get('next') or self.request.POST.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('app:default-view', pk=instance.pk)

def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    # Pass next URL to template
    context['next_url'] = self.request.GET.get('next', '')
    return context
```

### Template Pattern

#### Links to Forms
```html
<!-- From detail page to edit form -->
<a href="{% url 'app:model-edit' object.pk %}?next={{ request.get_full_path|urlencode }}">
    Edit
</a>

<!-- From list page to create form -->
<a href="{% url 'app:model-create' %}?next={{ request.get_full_path|urlencode }}">
    Add New
</a>
```

#### Form Template
```html
<form id="model-form" method="post">
    {% csrf_token %}
    
    <!-- Hidden field for next URL -->
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
    <a href="{% if next_url %}{{ next_url }}{% else %}{% url 'app:default-back' %}{% endif %}" class="btn btn-secondary">
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

    def form_valid(self, form):
        category = form.save(commit=False)
        category.updated_by = self.request.user
        category.save()
        
        messages.success(self.request, f'Category "{category.name}" was updated successfully.')
        
        # Redirect to next URL if provided
        next_url = self.request.GET.get('next') or self.request.POST.get('next')
        if next_url:
            return redirect(next_url)
        return redirect('catalog:category-detail', pk=category.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['next_url'] = self.request.GET.get('next', '')
        return context
```

#### Category Detail Template
```html
<!-- Edit button with next parameter -->
<a href="{% url 'catalog:category-edit' category.pk %}?next={{ request.get_full_path|urlencode }}" class="btn btn-primary">
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
    <a href="{% if next_url %}{{ next_url }}{% else %}{% url 'catalog:category-list' %}{% endif %}" class="btn btn-secondary">
        <i class="bi bi-arrow-left"></i> Cancel
    </a>
</div>
{% endblock %}
```

## User Experience Flow

### Scenario 1: Edit from Detail Page
1. User views Category Detail page
2. Clicks "Edit Category" → Goes to form with `?next=/category/detail/1/`
3. Submits form → Redirects back to Category Detail page

### Scenario 2: Edit from List Page  
1. User views Category List page
2. Clicks "Edit" on a category → Goes to form with `?next=/category/list/`
3. Submits form → Redirects back to Category List page

### Scenario 3: Create from Dashboard
1. User views Dashboard
2. Clicks "Add Category" → Goes to form with `?next=/dashboard/`
3. Submits form → Redirects back to Dashboard

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

**Last Updated**: August 4, 2025  
**Version**: 1.0  
**Maintainer**: StockFlow Development Team
