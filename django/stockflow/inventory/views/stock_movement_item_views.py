from django.core.exceptions import PermissionDenied
from django.views.generic import ListView, CreateView, UpdateView, View
from ..mixins.warehouse import WarehousePermissionMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from inventory.models.stock_movement_item import StockMovementItem
from inventory.models.stock_movement import StockMovement
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.contrib import messages

# forms
from ..forms.stock_movement_item_form import StockMovementItemForm

class StockItemMovementCreateView(WarehousePermissionMixin, LoginRequiredMixin, CreateView):
    model = StockMovementItem
    form_class = StockMovementItemForm
    template_name = 'inventory/stock-movement-item/stock-movement-item-form.html'
    permission_required_base = 'add_stockmovementitem' 
    http_method_names = ['get', 'post']
    
    def get_form_kwargs(self):
        """Add stock_movement_id to form kwargs"""
        kwargs = super().get_form_kwargs()
        kwargs['stock_movement_id'] = self.kwargs.get('stock_movement_id')
        return kwargs
    
    def get_initial(self):
        """Set initial data for the form"""
        initial = super().get_initial()
        stock_movement_id = self.kwargs.get('stock_movement_id')
        if stock_movement_id:
            initial['stock_movement'] = stock_movement_id
        return initial
    
    def get_context_data(self, **kwargs):
        """Add context data needed for the form page"""
        context = super().get_context_data(**kwargs)
        stock_movement_id = self.kwargs.get('stock_movement_id')
        
        if stock_movement_id:
            try:
                stock_movement = get_object_or_404(StockMovement, id=stock_movement_id)
                context['stock_movement'] = stock_movement
                context['warehouse'] = stock_movement.warehouse
                
                # Get existing movement items for display
                movement_items = StockMovementItem.objects.filter(
                    stock_movement=stock_movement
                ).order_by('-created_at')
                context['movement_items'] = movement_items
                
            except StockMovement.DoesNotExist:
                raise Http404("Stock movement not found")
        
        return context

    def form_valid(self, form):
        """Handle successful form submission with redirect"""
        try:
            movement_item = form.save(commit=False)
            movement_item.created_by = self.request.user
            movement_item.updated_by = self.request.user
            
            # Set stock_movement from URL parameter
            stock_movement_id = self.kwargs.get('stock_movement_id')
            if stock_movement_id:
                stock_movement = get_object_or_404(StockMovement, id=stock_movement_id)
                movement_item.stock_movement = stock_movement
            
            movement_item.save()
            
            # Add success message
            messages.success(
                self.request, 
                f'Successfully added movement item for {movement_item.item_sku.sku_code}'
            )
            
            # Redirect back to the same page to show updated list
            return redirect('inventory:movement-create', 
                          stock_movement_id=self.kwargs.get('stock_movement_id'))
                          
        except ValueError as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)
        
    def form_invalid(self, form):
        """Handle form validation errors"""
        messages.error(self.request, 'Please correct the errors below.')
        return self.render_to_response(self.get_context_data(form=form))

class StockItemMovementUpdateView(WarehousePermissionMixin, LoginRequiredMixin, UpdateView):
    model = StockMovementItem
    form_class = StockMovementItemForm
    template_name = 'inventory/stock-movement-item/stock-movement-item-form.html'  # ใช้ template เดียวกัน
    permission_required_base = 'change_stockmovementitem'
    http_method_names = ['post']
    context_object_name = 'movement_item'
    
    def get_object(self):
        """Get the specific movement item to update"""
        stock_movement_id = self.kwargs.get('stock_movement_id')
        pk = self.kwargs.get('pk')
        
        try:
            movement_item = get_object_or_404(
                StockMovementItem, 
                pk=pk, 
                stock_movement_id=stock_movement_id
            )
            return movement_item
        except StockMovementItem.DoesNotExist:
            raise Http404("Movement item not found")
    
    def get_form_kwargs(self):
        """Add stock_movement_id to form kwargs"""
        kwargs = super().get_form_kwargs()
        kwargs['stock_movement_id'] = self.kwargs.get('stock_movement_id')
        return kwargs
    
    def get_context_data(self, **kwargs):
        """Add context data needed for the form page"""
        context = super().get_context_data(**kwargs)
        stock_movement_id = self.kwargs.get('stock_movement_id')
        
        if stock_movement_id:
            try:
                stock_movement = get_object_or_404(StockMovement, id=stock_movement_id)
                context['stock_movement'] = stock_movement
                context['warehouse'] = stock_movement.warehouse
                
                # Get all movement items for display (same as create view)
                movement_items = StockMovementItem.objects.filter(
                    stock_movement=stock_movement
                ).order_by('-created_at')
                context['movement_items'] = movement_items
                
                # Flag เพื่อบอกว่าเป็น update mode
                context['is_update'] = True
                
            except StockMovement.DoesNotExist:
                raise Http404("Stock movement not found")
        
        return context

    def form_valid(self, form):
        """Handle successful form submission with redirect"""
        try:
            movement_item = form.save(commit=False)
            movement_item.updated_by = self.request.user
            
            # Ensure stock_movement is set correctly
            stock_movement_id = self.kwargs.get('stock_movement_id')
            if stock_movement_id:
                stock_movement = get_object_or_404(StockMovement, id=stock_movement_id)
                movement_item.stock_movement = stock_movement
            
            movement_item.save()
            
            # Add success message
            messages.success(
                self.request, 
                f'Successfully updated movement item for {movement_item.item_sku.sku_code}'
            )
            
            # Redirect กลับไปหน้า create form เหมือน BOM pattern
            return redirect('inventory:movement-create', 
                          stock_movement_id=self.kwargs.get('stock_movement_id'))
                          
        except ValueError as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)
        
    def form_invalid(self, form):
        """Handle form validation errors"""
        messages.error(self.request, 'Please correct the errors below.')
        return self.render_to_response(self.get_context_data(form=form))

  
class StockItemMovementDeleteView(WarehousePermissionMixin, LoginRequiredMixin, View):
    permission_required_base = 'delete_stockmovementitem'
    http_method_names = ['post']
    
    def get_object(self):
        """Get the specific movement item to delete"""
        stock_movement_id = self.kwargs.get('stock_movement_id')
        pk = self.kwargs.get('pk')
        
        try:
            movement_item = get_object_or_404(
                StockMovementItem, 
                pk=pk, 
                stock_movement_id=stock_movement_id
            )
            
            # Check if stock movement is not confirmed
            if movement_item.stock_movement.status == 'CONFIRMED':
                raise PermissionDenied("Cannot delete items from confirmed stock movements")
                
            return movement_item
        except StockMovementItem.DoesNotExist:
            raise Http404("Movement item not found")
    
    def post(self, request, *args, **kwargs):
        """Handle delete request"""
        try:
            movement_item = self.get_object()
            item_sku_code = movement_item.item_sku.sku_code
            stock_movement_id = movement_item.stock_movement.pk
            
            # Delete the movement item
            movement_item.delete()
            
            # Add success message
            messages.success(
                request, 
                f'Successfully deleted movement item for {item_sku_code}'
            )
            
            # Redirect back to the movement form page
            return redirect('inventory:movement-create', stock_movement_id=stock_movement_id)
            
        except PermissionDenied as e:
            messages.error(request, str(e))
            return redirect('inventory:movement-create', 
                          stock_movement_id=self.kwargs.get('stock_movement_id'))
        except Exception as e:
            messages.error(request, f'Error deleting movement item: {str(e)}')
            return redirect('inventory:movement-create', 
                          stock_movement_id=self.kwargs.get('stock_movement_id'))
