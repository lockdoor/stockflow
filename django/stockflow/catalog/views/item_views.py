from django.views.generic import ListView, CreateView, UpdateView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import render
from django.core.exceptions import ValidationError

# from catalog.forms.category_form import CategoryForm
from catalog.models.item import ItemSKU
from catalog.models.bom import BOM
# froms
from catalog.forms.item_form import ItemForm

class ItemListView(LoginRequiredMixin, ListView):
    model = ItemSKU
    template_name = 'catalog/item/item-list.html'
    context_object_name = 'items'
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Get items with optional category filtering
        """
        queryset = super().get_queryset()
        
        # Filter by category if provided
        category_id = self.request.GET.get('category')
        if category_id:
            try:
                queryset = queryset.filter(category_id=category_id)
            except (ValueError, TypeError):
                pass  # Ignore invalid category IDs
                
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add category filter info to context
        category_id = self.request.GET.get('category')
        if category_id:
            try:
                from catalog.models.category import Category
                context['filtered_category'] = Category.objects.get(pk=category_id)
            except (Category.DoesNotExist, ValueError, TypeError):
                context['filtered_category'] = None
        else:
            context['filtered_category'] = None
            
        return context
    
class ItemCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    View for creating a new Item
    Full page form workflow
    """
    model = ItemSKU
    form_class = ItemForm
    template_name = 'catalog/item/item-form.html'
    permission_required = 'catalog.add_itemsku'

    def form_valid(self, form):
        try:
            # Set created_by and updated_by to current user
            item = form.save(commit=False)
            item.created_by = self.request.user
            item.updated_by = self.request.user
                
            # Save the item (may still raise validation errors)
            item.save()
            
            # Add success message
            from django.contrib import messages
            messages.success(self.request, f'Item "{item.name}" was created successfully.')
            
            # Redirect to next URL if provided, otherwise default to item list
            from django.shortcuts import redirect
            next_url = self.request.GET.get('next') or self.request.POST.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('catalog:item-list')
            
        except (ValueError, ValidationError) as e:
            # Handle all types of business logic validation errors
            form.add_error(None, str(e))
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass next URL to template for hidden form field
        context['next_url'] = self.request.GET.get('next', '')
        
        # Pre-select category if provided
        category_id = self.request.GET.get('category')
        if category_id and not context['form'].instance.pk:
            try:
                from catalog.models.category import Category
                context['preselected_category'] = Category.objects.get(pk=category_id)
                # Set initial value for the form
                context['form'].initial['category'] = category_id
            except (Category.DoesNotExist, ValueError, TypeError):
                context['preselected_category'] = None
        else:
            context['preselected_category'] = None
            
        return context
    
class ItemUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    View for updating an existing Item
    Full page form workflow
    """
    model = ItemSKU
    form_class = ItemForm
    template_name = 'catalog/item/item-form.html'
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
            
            # Add success message
            from django.contrib import messages
            messages.success(self.request, f'Item "{item.name}" was updated successfully.')
            
            # Redirect to next URL if provided, otherwise default to item detail
            from django.shortcuts import redirect
            next_url = self.request.GET.get('next') or self.request.POST.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('catalog:item-detail', pk=item.pk)
            
        except (ValueError, ValidationError) as e:
            # Handle business logic validation errors
            form.add_error(None, str(e))
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass next URL to template for hidden form field
        context['next_url'] = self.request.GET.get('next', '')
        return context

class ItemDetailView(LoginRequiredMixin, DetailView):
    model = ItemSKU
    template_name = 'catalog/item/item-detail.html'
    context_object_name = 'item'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object.can_have_bom:
            # If item can have BOM, add BOM components to context with optimized query
            context['boms'] = BOM.objects.filter(
                parent_sku=self.object
            ).select_related(
                'component_sku', 
                'component_sku__category'
            ).order_by('-created_at')
        else:
            context['boms'] = None
            
        # Add primary image if exists
        if self.object.has_primary_image():
            context['primary_image'] = self.object.images.filter(is_primary=True).first()
        
        return context
