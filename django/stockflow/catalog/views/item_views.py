from django.views.generic import ListView, CreateView, UpdateView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import render
from django.core.exceptions import ValidationError

# from catalog.forms.category_form import CategoryForm
from catalog.models.item import ItemSKU
# froms
from catalog.forms.item_form import ItemForm

class ItemIndexView(LoginRequiredMixin, TemplateView):
    template_name = 'catalog/item/item-index.html'

class ItemListView(LoginRequiredMixin, ListView):
    model = ItemSKU
    template_name = 'catalog/item/partials/item-list.html'
    context_object_name = 'items'
    ordering = ['-created_at']
    
class ItemCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    View for creating a new Item
    Uses HTMX to handle form submission and updates the item list dynamically
    """
    model = ItemSKU
    form_class = ItemForm
    template_name = 'catalog/item/partials/item-form.html'
    permission_required = 'catalog.add_itemsku'

    def form_valid(self, form):
        try:
            # Set created_by and updated_by to current user
            item = form.save(commit=False)
            item.created_by = self.request.user
            item.updated_by = self.request.user
                
            # Save the item (may still raise validation errors)
            item.save()
            
            # Prepare context with the newly created item
            context = {'item': item}
            
            # Render the new item row for insertion into the table
            response = render(self.request, 'catalog/item/partials/item-row.html', context)
            
            # Add HTMX trigger for success notifications
            response['HX-Trigger'] = 'success'
            
            return response
            
        except (ValueError, ValidationError) as e:
            # Handle all types of business logic validation errors
            form.add_error(None, str(e))
            return self.form_invalid(form)
        
    def form_invalid(self, form):
        """
        Handle form validation errors
        Returns the form with errors highlighted to be displayed in the modal
        """
        response = render(self.request, self.template_name, {
            'form': form,
            'form_errors': True,
            'error_message': 'Please correct the errors below.'
        })
        
        # Configure HTMX to target the form container for replacement
        response['HX-Retarget'] = '#item-form-container'
        response['HX-Reswap'] = 'innerHTML'
        
        return response
    
class ItemUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    View for updating an existing Item
    Uses HTMX to handle form submission and update the item row dynamically
    """
    model = ItemSKU
    form_class = ItemForm
    template_name = 'catalog/item/partials/item-form.html'
    permission_required = 'catalog.change_itemsku'
    pk_url_kwarg = 'pk'

    def form_valid(self, form):
        try:
            # Set updated_by to current user
            item = form.save(commit=False)
            item.updated_by = self.request.user
            
            # Let the model handle all validation including business logic
            # The model's clean and save methods will raise appropriate exceptions
            item.save()
            
            # Prepare context with the updated item
            context = {'item': item}
            response = render(self.request, 'catalog/item/partials/item-row.html', context)
            response['HX-Trigger'] = 'success'
            return response
            
        except (ValueError, ValidationError) as e:
            # Handle business logic validation errors
            form.add_error(None, str(e))
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """
        Handle form validation errors
        Returns the form with errors highlighted to be displayed in the modal
        """
        response = render(self.request, self.template_name, {
            'form': form,
            'form_errors': True,
            'error_message': 'Please correct the errors below.'
        })
        response['HX-Retarget'] = '#item-form-container'
        response['HX-Reswap'] = 'innerHTML'
        return response

class ItemDetailView(LoginRequiredMixin, DetailView):
    model = ItemSKU
    template_name = 'catalog/item/item-detail.html'
    context_object_name = 'item'
