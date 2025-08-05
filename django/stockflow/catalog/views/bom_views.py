from django.views.generic import ListView, CreateView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.urls import reverse
# forms
from catalog.forms.bom_form import BOMForm

# models
from catalog.models.bom import BOM
from catalog.models.category import Category
from catalog.models.item import ItemSKU

class BomListByParentIDView(LoginRequiredMixin, ListView):
    """
    ListView for displaying BOMs filtered by parent ItemSKU.
    Uses HTMX for dynamic content loading.
    """
    model = BOM
    template_name = 'catalog/bom/partials/bom-list.html'
    context_object_name = 'boms'
    paginate_by = 20
    
    def get_queryset(self):
        """
        Get BOMs filtered by parent_sku with proper ordering.
        Orders by created_at (descending) for consistent ordering.
        """
        parent_id = self.kwargs.get('parent_id')
        if not parent_id:
            from django.http import Http404
            raise Http404("Parent ID is required to list BOMs.")
        
        # Validate parent exists and store for context
        self.parent_sku = get_object_or_404(ItemSKU, pk=parent_id)
        
        return BOM.objects.filter(
            parent_sku=self.parent_sku
        ).select_related(
            'component_sku', 
            'parent_sku',
            'created_by',
            'updated_by'
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        """
        Add parent_sku to context for template use.
        """
        context = super().get_context_data(**kwargs)
        context['parent_sku'] = self.parent_sku
        return context

class BomCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    template_name = 'catalog/bom/bom-form.html'
    form_class = BOMForm
    permission_required = 'catalog.add_bom'
    http_method_names = ['get', 'post']
    
    def dispatch(self, request, *args, **kwargs):
        self.parent_sku = get_object_or_404(ItemSKU, pk=kwargs.get('parent_id'))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        Add parent_sku to context for template use.
        """
        context = super().get_context_data(**kwargs)
        context['parent_sku'] = self.parent_sku
        # get all items is active for select as component_sku
        context['components'] = ItemSKU.get_active().select_related('category')
        # get existing BOMs for this parent
        context['boms'] = BOM.objects.filter(
            parent_sku=self.parent_sku
        ).select_related('component_sku', 'component_sku__category').order_by('-created_at')
        return context
    
    def get_form_kwargs(self):
        """
        Pass parent_sku to the form.
        """
        kwargs = super().get_form_kwargs()
        kwargs['parent_sku'] = self.parent_sku
        return kwargs
    
    def form_valid(self, form):
        """
        Handle successful form submission.
        """
        try:
            # Set parent_sku and audit fields
            bom: BOM = form.save(commit=False)
            bom.parent_sku = self.parent_sku
            bom.created_by = self.request.user
            bom.updated_by = self.request.user
            bom.save()
            
            messages.success(
                self.request, 
                f'Component "{bom.component_sku.sku_code}" added to BOM successfully!'
            )
            
            # Redirect back to the same form to continue adding components
            return redirect('catalog:bom-create', parent_id=self.parent_sku.pk)
            
        except (ValueError, ValidationError) as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """
        Handle form validation errors.
        """
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)
    
    
class BomUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    View for updating an existing BOM entry.
    Only allows editing of quantity field - parent_sku and component_sku cannot be changed.
    """
    model = BOM
    form_class = BOMForm
    template_name = 'catalog/bom/bom-form.html'
    permission_required = 'catalog.change_bom'
    pk_url_kwarg = 'pk'
    
    def get_context_data(self, **kwargs):
        """
        Add categories and BOM instance to context for template use.
        """
        context = super().get_context_data(**kwargs)
        context['parent_sku'] = self.object.parent_sku
        context['components'] = ItemSKU.objects.filter(is_active=True)
        context['boms'] = BOM.objects.filter(
            parent_sku=self.object.parent_sku
        ).select_related('component_sku', 'component_sku__category').order_by('-created_at')
        return context

    def form_valid(self, form):
        """
        Handle successful form submission.
        Updates BOM with audit fields and redirects back to BOM form.
        """
        try:
            # Set audit fields before saving
            bom: BOM = form.save(commit=False)
            bom.updated_by = self.request.user
            
            # Save the BOM (may still raise validation errors)
            bom.save()
            
            messages.success(
                self.request,
                f'BOM component "{bom.component_sku.sku_code}" updated successfully!'
            )
            
            # Redirect back to BOM form
            return redirect('catalog:bom-create', parent_id=bom.parent_sku.pk)
            
        except (ValueError, ValidationError) as e:
            # Handle all types of business logic validation errors
            form.add_error(None, str(e))
            return self.form_invalid(form)

    def form_invalid(self, form):
        """
        Handle form validation errors.
        """
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)

class BomDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'catalog.delete_bom'
    
    def post(self, request, pk):
        """
        Handle DELETE request to remove BOM entry.
        """
        try:
            bom = get_object_or_404(BOM, pk=pk)
            parent_id = bom.parent_sku.pk
            component_name = bom.component_sku.sku
            
            bom.delete()
            
            messages.success(
                request,
                f'Component "{component_name}" removed from BOM successfully!'
            )
            
            return redirect('catalog:bom-create', parent_id=parent_id)
            
        except Exception as e:
            messages.error(request, f'Error removing component: {str(e)}')
            return redirect('catalog:bom-create', parent_id=parent_id)