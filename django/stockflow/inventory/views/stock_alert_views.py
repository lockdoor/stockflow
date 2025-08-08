"""
Stock Alert Views

Views for managing stock alerts including create, edit, list, and delete operations.
Supports both standard and AJAX requests for flexible UI interactions.

Author: StockFlow Team
Created: 2025
"""

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.core.paginator import Paginator
from inventory.models.stock_alert import StockAlert
from inventory.models.warehouse import Warehouse
from catalog.models import ItemSKU
from inventory.forms.stock_alert_form import StockAlertForm, StockAlertSearchForm, BulkStockAlertForm


class StockAlertListView(LoginRequiredMixin, ListView):
    """List view for stock alerts with search and filtering"""
    model = StockAlert
    template_name = 'inventory/stock_alert/stock-alert-list.html'
    context_object_name = 'stock_alerts'
    paginate_by = 20
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter queryset based on search parameters"""
        queryset = super().get_queryset().select_related(
            'item_sku', 'warehouse', 'created_by', 'updated_by'
        )
        
        # Get search parameters
        item_sku_id = self.request.GET.get('item_sku')
        warehouse_id = self.request.GET.get('warehouse')
        is_enabled = self.request.GET.get('is_enabled')
        search = self.request.GET.get('search')
        
        # Apply filters
        if item_sku_id:
            queryset = queryset.filter(item_sku_id=item_sku_id)
        
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)
        
        if is_enabled == 'true':
            queryset = queryset.filter(is_enabled=True)
        elif is_enabled == 'false':
            queryset = queryset.filter(is_enabled=False)
        
        if search:
            queryset = queryset.filter(
                Q(item_sku__sku_code__icontains=search) |
                Q(item_sku__name__icontains=search) |
                Q(warehouse__name__icontains=search) |
                Q(warehouse__code__icontains=search)
            )
        
        return queryset

    def get_context_data(self, **kwargs):
        """Add search form and summary statistics to context"""
        context = super().get_context_data(**kwargs)
        
        # Initialize search form with current parameters
        search_form = StockAlertSearchForm(self.request.GET or None)
        context['search_form'] = search_form
        
        # Add summary statistics
        all_alerts = StockAlert.objects.all()
        context['total_alerts'] = all_alerts.count()
        context['enabled_alerts'] = all_alerts.filter(is_enabled=True).count()
        context['disabled_alerts'] = all_alerts.filter(is_enabled=False).count()
        
        return context


class StockAlertDetailView(LoginRequiredMixin, DetailView):
    """Detail view for a single stock alert"""
    model = StockAlert
    template_name = 'inventory/stock_alert/stock-alert-detail.html'
    context_object_name = 'stock_alert'

    def get_queryset(self):
        """Optimize query with select_related"""
        return super().get_queryset().select_related(
            'item_sku', 'warehouse', 'created_by', 'updated_by'
        )


class StockAlertCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Create view for new stock alerts"""
    model = StockAlert
    form_class = StockAlertForm
    template_name = 'inventory/stock_alert/stock-alert-form.html'
    permission_required = 'inventory.add_stockalert'

    def get_initial(self):
        """Pre-populate form with query parameters"""
        initial = super().get_initial()
        
        # Get item and warehouse from query parameters
        item_id = self.request.GET.get('item')
        warehouse_id = self.request.GET.get('warehouse')
        
        if item_id:
            try:
                item = ItemSKU.objects.get(id=item_id)
                if item.is_active:
                    initial['item_sku'] = item
            except ItemSKU.DoesNotExist:
                pass
        
        if warehouse_id:
            try:
                warehouse = Warehouse.objects.get(id=warehouse_id, is_active=True)
                initial['warehouse'] = warehouse
            except Warehouse.DoesNotExist:
                pass
        
        return initial

    def get_context_data(self, **kwargs):
        """Add additional context"""
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Create Stock Alert'
        context['form_action'] = 'Create'
        
        # Add pre-selected item and warehouse info if available
        item_id = self.request.GET.get('item')
        warehouse_id = self.request.GET.get('warehouse')
        
        if item_id:
            try:
                context['preselected_item'] = ItemSKU.objects.get(id=item_id)
            except ItemSKU.DoesNotExist:
                pass
        
        if warehouse_id:
            try:
                context['preselected_warehouse'] = Warehouse.objects.get(id=warehouse_id)
            except Warehouse.DoesNotExist:
                pass
        
        return context

    def form_valid(self, form):
        """Handle successful form submission"""
        try:
            with transaction.atomic():
                # Save the stock alert with audit fields
                stock_alert = form.save(user=self.request.user)
                
                # Add success message
                messages.success(
                    self.request, 
                    f'Stock alert for {stock_alert.item_sku.sku_code} in {stock_alert.warehouse.name} was created successfully.'
                )
                
                return redirect('inventory:stock-alert-detail', pk=stock_alert.pk)
                
        except ValidationError as e:
            # Handle validation errors
            for field, errors in e.error_dict.items():
                for error in errors:
                    form.add_error(field, error)
            return self.form_invalid(form)
        except Exception as e:
            messages.error(self.request, f'An error occurred: {str(e)}')
            return self.form_invalid(form)


class StockAlertUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Update view for editing stock alerts"""
    model = StockAlert
    form_class = StockAlertForm
    template_name = 'inventory/stock_alert/stock-alert-form.html'
    permission_required = 'inventory.change_stockalert'

    def get_context_data(self, **kwargs):
        """Add additional context"""
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Edit Stock Alert - {self.object.item_sku.sku_code}'
        context['form_action'] = 'Update'
        return context

    def form_valid(self, form):
        """Handle successful form submission"""
        try:
            with transaction.atomic():
                # Save the stock alert with audit fields
                stock_alert = form.save(user=self.request.user)
                
                # Add success message
                messages.success(
                    self.request, 
                    f'Stock alert for {stock_alert.item_sku.sku_code} in {stock_alert.warehouse.name} was updated successfully.'
                )
                
                return redirect('inventory:stock-alert-detail', pk=stock_alert.pk)
                
        except ValidationError as e:
            # Handle validation errors
            for field, errors in e.error_dict.items():
                for error in errors:
                    form.add_error(field, error)
            return self.form_invalid(form)
        except Exception as e:
            messages.error(self.request, f'An error occurred: {str(e)}')
            return self.form_invalid(form)


class StockAlertDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Delete view for stock alerts"""
    model = StockAlert
    template_name = 'inventory/stock_alert/stock-alert-confirm-delete.html'
    success_url = reverse_lazy('inventory:stock-alert-list')
    permission_required = 'inventory.delete_stockalert'

    def delete(self, request, *args, **kwargs):
        """Handle delete with success message"""
        stock_alert = self.get_object()
        messages.success(
            request, 
            f'Stock alert for {stock_alert.item_sku.sku_code} in {stock_alert.warehouse.name} was deleted successfully.'
        )
        return super().delete(request, *args, **kwargs)


class StockAlertBulkActionView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Handle bulk actions on stock alerts"""
    permission_required = 'inventory.change_stockalert'

    def post(self, request, *args, **kwargs):
        """Process bulk actions"""
        form = BulkStockAlertForm(request.POST)
        
        if form.is_valid():
            action = form.cleaned_data['action']
            alert_ids = form.cleaned_data['selected_alerts']
            
            try:
                with transaction.atomic():
                    alerts = StockAlert.objects.filter(id__in=alert_ids)
                    count = alerts.count()
                    
                    if action == 'enable':
                        alerts.update(is_enabled=True, updated_by=request.user)
                        messages.success(request, f'{count} stock alert(s) enabled successfully.')
                    
                    elif action == 'disable':
                        alerts.update(is_enabled=False, updated_by=request.user)
                        messages.success(request, f'{count} stock alert(s) disabled successfully.')
                    
                    elif action == 'delete':
                        if not request.user.has_perm('inventory.delete_stockalert'):
                            messages.error(request, 'You do not have permission to delete stock alerts.')
                            return redirect('inventory:stock-alert-list')
                        
                        alerts.delete()
                        messages.success(request, f'{count} stock alert(s) deleted successfully.')
                    
            except Exception as e:
                messages.error(request, f'An error occurred: {str(e)}')
        
        else:
            messages.error(request, 'Invalid form data.')
        
        return redirect('inventory:stock-alert-list')


class StockAlertToggleView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """AJAX view to toggle stock alert enable/disable status"""
    permission_required = 'inventory.change_stockalert'

    def post(self, request, pk):
        """Toggle alert status via AJAX"""
        stock_alert = get_object_or_404(StockAlert, pk=pk)
        
        try:
            stock_alert.is_enabled = not stock_alert.is_enabled
            stock_alert.updated_by = request.user
            stock_alert.save()
            
            return JsonResponse({
                'success': True,
                'is_enabled': stock_alert.is_enabled,
                'message': f'Alert {"enabled" if stock_alert.is_enabled else "disabled"} successfully.'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
