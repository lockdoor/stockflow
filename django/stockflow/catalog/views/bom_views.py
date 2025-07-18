from django.views.generic import ListView, CreateView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.core.exceptions import ValidationError
# forms
from catalog.forms.bom_form import BOMForm
from catalog.forms.bom_update_form import BOMUpdateForm
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
    """
    View for creating a new BOM entry.
    Uses HTMX to handle form submission and updates the BOM list dynamically.
    Requires parent_id in URL kwargs to associate the BOM with a parent ItemSKU.
    """
    model = BOM
    form_class = BOMForm
    template_name = 'catalog/bom/partials/bom-form.html'
    permission_required = 'catalog.add_bom'
    
    def get_initial(self):
        """
        Set initial form data including parent_sku validation.
        """
        initial = super().get_initial()
        parent_id = self.kwargs.get('parent_id')
        if not parent_id:
            from django.http import Http404
            raise Http404("Parent ID is required to create a BOM.")
        
        # Validate parent exists and store for context
        self.parent_sku = get_object_or_404(ItemSKU, pk=parent_id)
        return initial
    
    def get_context_data(self, **kwargs):
        """
        Add categories and parent_sku to context for template use.
        """
        context = super().get_context_data(**kwargs)
        # Ensure parent_sku is available (from get_initial)
        if not hasattr(self, 'parent_sku'):
            parent_id = self.kwargs.get('parent_id')
            if parent_id:
                self.parent_sku = get_object_or_404(ItemSKU, pk=parent_id)
        
        context['category'] = Category.objects.all().order_by('name')
        context['parent_sku'] = self.parent_sku
        return context

    def get_form_kwargs(self):
        """
        Add parent_sku to form kwargs so form validation can access it.
        """
        kwargs = super().get_form_kwargs()
        # Ensure parent_sku is available
        if not hasattr(self, 'parent_sku'):
            parent_id = self.kwargs.get('parent_id')
            if parent_id:
                self.parent_sku = get_object_or_404(ItemSKU, pk=parent_id)
        
        kwargs['parent_sku'] = self.parent_sku
        return kwargs

    def form_valid(self, form):
        """
        Handle successful form submission.
        Creates BOM with audit fields and returns HTMX response.
        """
        try:
            # Set audit fields before saving
            bom = form.save(commit=False)
            bom.created_by = self.request.user
            bom.updated_by = self.request.user
            
            # Save the BOM (may still raise validation errors)
            bom.save()
            
            # Prepare context with the newly created BOM
            context = {'bom': bom}
            
            # Render the new BOM row for insertion into the table
            response = render(self.request, 'catalog/bom/partials/bom-row.html', context)
            
            # Add HTMX trigger for success notifications
            response['HX-Trigger'] = 'success'
            
            return response
            
        except (ValueError, ValidationError) as e:
            # Handle all types of business logic validation errors
            form.add_error(None, str(e))
            return self.form_invalid(form)

    def form_invalid(self, form):
        """
        Handle form validation errors.
        Returns the form with errors highlighted to be displayed in the container.
        """
        # Ensure parent_sku is available for context
        if not hasattr(self, 'parent_sku'):
            parent_id = self.kwargs.get('parent_id')
            if parent_id:
                self.parent_sku = get_object_or_404(ItemSKU, pk=parent_id)
        
        response = render(self.request, self.template_name, {
            'form': form,
            'parent_sku': self.parent_sku,
            'category': Category.objects.all().order_by('name'),
            'form_errors': True,
            'error_message': 'Please correct the errors below.'
        })
        
        # Configure HTMX to target the form container for replacement
        response['HX-Retarget'] = '#bom-form-container'
        response['HX-Reswap'] = 'innerHTML'
        
        return response
    
class BomUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    View for updating an existing BOM entry.
    Only allows editing of quantity field - parent_sku and component_sku cannot be changed.
    Uses HTMX to handle form submission and update the BOM row dynamically.
    """
    model = BOM
    form_class = BOMUpdateForm
    template_name = 'catalog/bom/partials/bom-form.html'  # Use same template as create
    permission_required = 'catalog.change_bom'
    pk_url_kwarg = 'pk'
    
    def get_context_data(self, **kwargs):
        """
        Add categories and BOM instance to context for template use.
        """
        context = super().get_context_data(**kwargs)
        context['category'] = Category.objects.all().order_by('name')
        context['bom'] = self.object  # The BOM being updated
        context['parent_sku'] = self.object.parent_sku
        return context

    def form_valid(self, form):
        """
        Handle successful form submission.
        Updates BOM with audit fields and returns HTMX response.
        """
        try:
            # Set audit fields before saving
            bom = form.save(commit=False)
            bom.updated_by = self.request.user
            
            # Save the BOM (may still raise validation errors)
            bom.save()
            
            # Prepare context with the updated BOM
            context = {'bom': bom}
            
            # Render the updated BOM row for replacement
            response = render(self.request, 'catalog/bom/partials/bom-row.html', context)
            
            # Add HTMX trigger for success notifications
            response['HX-Trigger'] = 'success'
            
            return response
            
        except (ValueError, ValidationError) as e:
            # Handle all types of business logic validation errors
            form.add_error(None, str(e))
            return self.form_invalid(form)

    def form_invalid(self, form):
        """
        Handle form validation errors.
        Returns the form with errors highlighted to be displayed in the container.
        """
        response = render(self.request, self.template_name, {
            'form': form,
            'bom': self.object,
            'parent_sku': self.object.parent_sku,
            'category': Category.objects.all().order_by('name'),
            'form_errors': True,
            'error_message': 'Please correct the errors below.'
        })
        
        # Configure HTMX to target the form container for replacement
        response['HX-Retarget'] = '#bom-form-container'
        response['HX-Reswap'] = 'innerHTML'
        
        return response

class BomDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'catalog.delete_bom'
    
    def delete(self, request, pk):
        try:
            bom = BOM.objects.get(pk=pk)
            bom.delete()
            return HttpResponse("")
        except BOM.DoesNotExist:
            return HttpResponse(status=404)