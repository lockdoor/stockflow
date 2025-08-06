from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import ValidationError
from inventory.models.warehouse import Warehouse
from inventory.forms.warehouse_form import WarehouseForm

class WarehouseListView(LoginRequiredMixin, ListView):
    model = Warehouse
    template_name = 'inventory/warehouse/warehouse-list.html'
    context_object_name = 'warehouses'
    paginate_by = 20
    ordering = 'name'

class WarehouseDetailView(LoginRequiredMixin, DetailView):
    model = Warehouse
    template_name = 'inventory/warehouse/warehouse-detail.html'
    context_object_name = 'warehouse'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add any additional context if needed
        context['stock_movements'] = self.object.stock_movements.all().order_by('-created_at')[:5]
        return context
    
class WarehouseCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    View for creating a new Warehouse
    Full page form workflow
    """
    model = Warehouse
    form_class = WarehouseForm
    template_name = 'inventory/warehouse/warehouse-form.html'
    permission_required = 'inventory.add_warehouse'
    
    def form_valid(self, form):
        try:
            # Set created_by and updated_by to current user
            warehouse = form.save(commit=False)
            warehouse.created_by = self.request.user
            warehouse.updated_by = self.request.user
            
            # Save the warehouse (may still raise validation errors)
            warehouse.save()
            
            # Add success message
            messages.success(self.request, f'Warehouse "{warehouse.name}" was created successfully.')
            
            # Redirect to next URL if provided, otherwise default to warehouse list
            next_url = self.request.GET.get('next') or self.request.POST.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('inventory:warehouse-list')
            
        except (ValueError, ValidationError) as e:
            # Handle all types of business logic validation errors
            form.add_error(None, str(e))
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass next URL to template for hidden form field
        context['next_url'] = self.request.GET.get('next', '')
        return context

class WarehouseUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    View for updating an existing Warehouse
    Full page form workflow
    """
    model = Warehouse
    form_class = WarehouseForm
    template_name = 'inventory/warehouse/warehouse-form.html'
    permission_required = 'inventory.change_warehouse'
    pk_url_kwarg = 'pk'

    def form_valid(self, form):
        try:
            # Set updated_by to current user
            warehouse = form.save(commit=False)
            warehouse.updated_by = self.request.user
            
            # Save the warehouse (may still raise validation errors)
            warehouse.save()
            
            # Add success message
            messages.success(self.request, f'Warehouse "{warehouse.name}" was updated successfully.')
            
            # Redirect to next URL if provided, otherwise default to warehouse detail
            next_url = self.request.GET.get('next') or self.request.POST.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('inventory:warehouse-detail', pk=warehouse.pk)
            
        except (ValueError, ValidationError) as e:
            # Handle business logic validation errors
            form.add_error(None, str(e))
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass next URL to template for hidden form field
        context['next_url'] = self.request.GET.get('next', '')
        return context
