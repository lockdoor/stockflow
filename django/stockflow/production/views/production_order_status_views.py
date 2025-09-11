"""
Production Order Status Management Views

This module handles status transitions for production orders including:
- Cancellation workflow
- WIP material returns
- Order closure
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView
from django.http import Http404, JsonResponse
from django.core.exceptions import PermissionDenied
from django.db import transaction

from production.models import ProductionOrder, WIPStockMovement
from inventory.models import StockMovement
from production.mixins.production_permissions import ProductionPermissionMixin

class ProductionOrderCancelConfirmView(LoginRequiredMixin, ProductionPermissionMixin, TemplateView):
    """
    View to show cancellation confirmation page with WIP materials summary
    """
    template_name = 'production/orders/production-order-cancel-confirm.html'
    permission_required_base = 'change_productionorder'
    
    def get_object(self):
        """Get production order object"""
        return get_object_or_404(ProductionOrder, id=self.kwargs['pk'])
    
    def dispatch(self, request, *args, **kwargs):
        """Check if order can be cancelled"""
        self.object = self.get_object()
        
        if not self.object.can_cancel():
            messages.error(
                request, 
                f"Production order #{self.object.id} cannot be cancelled. Current status: {self.object.get_status_display()}"
            )
            return redirect('production:production-order-detail', pk=self.object.id)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """Prepare context data for cancellation confirmation"""
        context = super().get_context_data(**kwargs)
        
        production_order = self.object
        context['production_order'] = production_order
        
        # Get WIP materials that need to be returned
        wip_materials = production_order.get_wip_materials_summary()
        context['wip_materials'] = wip_materials
        
        # Get existing stock movements for this production order
        stock_movements = StockMovement.objects.filter(
            reference_type=StockMovement.ReferenceType.PRODUCTION,
            reference_id=production_order.id
        ).prefetch_related('movement_items').order_by('-created_at')
        context['stock_movements'] = stock_movements
        
        return context


class ProductionOrderCancelView(LoginRequiredMixin, ProductionPermissionMixin, View):
    """
    View to handle production order cancellation
    """
    permission_required_base = 'change_productionorder'
    
    def post(self, request, pk):
        """Handle cancellation POST request"""
        production_order = get_object_or_404(ProductionOrder, id=pk)
        
        # Check if order can be cancelled
        if not production_order.can_cancel():
            messages.error(
                request, 
                f"Production order #{production_order.id} cannot be cancelled. Current status: {production_order.get_status_display()}"
            )
            return redirect('production:production-order-detail', pk=production_order.id)
        
        # Validate confirmation checkbox
        if not request.POST.get('confirm_cancel'):
            messages.error(request, "You must confirm the cancellation by checking the confirmation box.")
            return redirect('production:production-order-cancel-confirm', pk=production_order.id)
        
        try:
            # Get cancellation reason if provided
            cancel_reason = request.POST.get('cancel_reason', '').strip()
            
            # Cancel the production order
            production_order.cancel_production(user=request.user)
            
            # Add cancellation reason to notes if provided
            if cancel_reason:
                if production_order.note:
                    production_order.note += f"\n\n[CANCELLED] {cancel_reason}"
                else:
                    production_order.note = f"[CANCELLED] {cancel_reason}"
                production_order.save()
            
            # Check if there are WIP materials
            if production_order.has_wip_materials():
                messages.warning(
                    request,
                    f"Production order #{production_order.id} has been cancelled. "
                    f"Please return WIP materials to complete the cancellation process."
                )
            else:
                messages.success(
                    request,
                    f"Production order #{production_order.id} has been cancelled successfully."
                )
            
        except Exception as e:
            messages.error(request, f"Error cancelling production order: {str(e)}")
            return redirect('production:production-order-cancel-confirm', pk=production_order.id)
        
        # Redirect to next URL or production order detail
        next_url = request.POST.get('next')
        if next_url:
            return redirect(next_url)
        return redirect('production:production-order-detail', pk=production_order.id)


class ProductionOrderReturnWIPView(LoginRequiredMixin, ProductionPermissionMixin, TemplateView):
    """
    View to manage WIP materials return for cancelled production orders
    """
    template_name = 'production/orders/production-order-return-wip.html'
    permission_required_base = 'change_productionorder'
    
    def get_object(self):
        """Get production order object"""
        return get_object_or_404(ProductionOrder, id=self.kwargs['pk'])
    
    def dispatch(self, request, *args, **kwargs):
        """Check if order allows WIP material returns"""
        self.object = self.get_object()
        
        if not self.object.can_return_wip_materials():
            messages.error(
                request, 
                f"Production order #{self.object.id} is not in a state that allows WIP material returns. "
                f"Current status: {self.object.get_status_display()}"
            )
            return redirect('production:production-order-detail', pk=self.object.id)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """Prepare context data for WIP return page"""
        context = super().get_context_data(**kwargs)
        
        production_order = self.object
        context['production_order'] = production_order
        
        # Get WIP materials that need to be returned
        wip_materials = production_order.get_wip_materials_summary()
        context['wip_materials'] = wip_materials
        
        # Get recent stock movements (returns) for this production order
        recent_movements = StockMovement.objects.filter(
            reference_type=StockMovement.ReferenceType.PRODUCTION,
            reference_id=production_order.id,
            # movement_type=StockMovement.MovementType.IN  # Only IN movements (returns)
        ).prefetch_related('movement_items').order_by('-created_at')[:5]
        context['recent_movements'] = recent_movements
        
        return context
    
    @transaction.atomic
    def post(self, request, pk):
        """Handle bulk WIP materials return"""
        production_order = get_object_or_404(ProductionOrder, id=pk)
        
        # Check if order allows WIP material returns
        if not production_order.can_return_wip_materials():
            messages.error(
                request,
                f"Production order #{production_order.id} is not in a state that allows WIP material returns. "
                f"Current status: {production_order.get_status_display()}"
            )
            return redirect('production:production-order-detail', pk=production_order.id)
        
        try:
            # Get WIP materials that need to be returned
            wip_materials = production_order.get_wip_materials_summary()
            
            if not wip_materials:
                messages.info(request, "No WIP materials to return.")
                return redirect('production:production-order-detail', pk=production_order.id)
            
            # Create bulk return stock movement
            from inventory.models import StockMovementItem
            
            # Create stock movement for returning WIP materials
            stock_movement = StockMovement.objects.create(
                warehouse=production_order.warehouse,
                reference_type=StockMovement.ReferenceType.PRODUCTION,
                reference_id=production_order.id,
                note=f"Bulk return of WIP materials from cancelled production order #{production_order.id}",
                created_by=request.user,
                updated_by=request.user
            )
            
            # Add movement items for each WIP material
            from production.utils.wip_lot_generator import generate_wip_return_lot_number
            
            movement_items_created = 0
            for material in wip_materials:
                if material['balance'] > 0:
                    # Generate unique lot number for this WIP return
                    lot_number = generate_wip_return_lot_number(
                        production_order_id=production_order.id,
                        item_sku_id=material['item_sku'].id
                    )
                    
                    StockMovementItem.objects.create(
                        stock_movement=stock_movement,
                        item_sku=material['item_sku'],
                        quantity=material['balance'],
                        movement_type='IN',  # Return WIP materials back to inventory
                        lot_number=lot_number,
                        expiry_date=None,  # No expiry for returned WIP materials
                        note=f"Return from Production Order #{production_order.id}",
                        created_by=request.user,
                        updated_by=request.user
                    )
                    movement_items_created += 1
            
            if movement_items_created > 0:
                # Create WIP stock movements to reduce WIP stock balances
                for material in wip_materials:
                    if material['balance'] > 0:
                        # Create WIP stock movement to record the return (OUT from WIP)
                        WIPStockMovement.objects.create(
                            production_order=production_order,
                            source_stock_movement=stock_movement,  # Reference to the stock movement
                            movement_type=WIPStockMovement.MovementType.RETURN,
                            item_sku=material['item_sku'],
                            quantity=material['balance'],
                            note=f"Return WIP materials to inventory via stock movement #{stock_movement.id}",
                            created_by=request.user,
                            updated_by=request.user
                        )
                
                # Return material reservations if any exist
                try:
                    production_order.return_all_material_reservations(user=request.user)
                except Exception as e:
                    # Log the error but don't fail the whole operation
                    messages.warning(
                        request,
                        f"WIP materials returned successfully, but encountered issue returning reservations: {str(e)}"
                    )
                
                # Confirm the stock movement to execute the returns
                stock_movement.confirm(user=request.user)
                
                messages.success(
                    request,
                    f"Successfully created bulk return movement #{stock_movement.id} with {movement_items_created} items. "
                    f"WIP materials have been returned to stock."
                )
                
                # Check if production order can now be closed as cancelled
                production_order.refresh_from_db()
                if not production_order.has_wip_materials():
                    try:
                        production_order.close_as_cancelled(user=request.user)
                        messages.success(
                            request,
                            f"Production order #{production_order.id} has been automatically closed as cancelled. "
                            f"All WIP materials have been returned to inventory."
                        )
                    except ValueError as e:
                        messages.warning(
                            request,
                            f"WIP materials returned successfully, but could not auto-close order: {str(e)}"
                        )
                
                return redirect('production:production-order-detail', pk=production_order.id)
            else:
                # Delete empty movement if no items were created
                stock_movement.delete()
                messages.warning(request, "No WIP materials with positive balance found to return.")
                
        except Exception as e:
            messages.error(request, f"Error creating bulk return movement: {str(e)}")
        
        return redirect('production:production-order-return-wip', pk=production_order.id)


class ProductionOrderCloseCompletedView(LoginRequiredMixin, ProductionPermissionMixin, View):
    """
    View to close production order as completed
    """
    permission_required_base = 'change_productionorder'
    
    def post(self, request, pk):
        """Handle close as completed POST request"""
        production_order = get_object_or_404(ProductionOrder, id=pk)
        
        try:
            production_order.close_as_completed(user=request.user)
            messages.success(
                request,
                f"Production order #{production_order.id} has been closed as completed successfully."
            )
        except ValueError as e:
            messages.error(request, f"Error closing production order: {str(e)}")
        except Exception as e:
            messages.error(request, f"Unexpected error: {str(e)}")
        
        return redirect('production:production-order-detail', pk=production_order.id)


class ProductionOrderCloseCancelledView(LoginRequiredMixin, ProductionPermissionMixin, View):
    """
    View to close production order as cancelled (after WIP materials returned)
    """
    permission_required_base = 'change_productionorder'
    
    def post(self, request, pk):
        """Handle close as cancelled POST request"""
        production_order = get_object_or_404(ProductionOrder, id=pk)
        
        try:
            production_order.close_as_cancelled(user=request.user)
            messages.success(
                request,
                f"Production order #{production_order.id} has been closed as cancelled. "
                f"All WIP materials have been returned to inventory."
            )
        except ValueError as e:
            messages.error(request, f"Error closing production order: {str(e)}")
        except Exception as e:
            messages.error(request, f"Unexpected error: {str(e)}")
        
        return redirect('production:production-order-detail', pk=production_order.id)


class ProductionOrderStatusAPI(LoginRequiredMixin, ProductionPermissionMixin, View):
    """
    API endpoint to check production order status and WIP materials
    """
    permission_required_base = 'view_productionorder'
    
    def get(self, request, pk):
        """Get production order status information as JSON"""
        try:
            production_order = get_object_or_404(ProductionOrder, id=pk)
            
            # Get WIP materials summary
            wip_materials = production_order.get_wip_materials_summary()
            wip_summary = []
            for material in wip_materials:
                wip_summary.append({
                    'item_sku_code': material['item_sku'].sku_code,
                    'item_name': material['item_sku'].name,
                    'balance': float(material['balance']),
                    'unit': material['item_sku'].unit,
                    'warehouse_name': material['warehouse'].name,
                })
            
            data = {
                'id': production_order.id,
                'status': production_order.status,
                'status_display': production_order.get_status_display(),
                'status_with_context': production_order.get_status_display_with_context(),
                'can_cancel': production_order.can_cancel(),
                'can_close': production_order.can_close(),
                'is_active': production_order.is_active(),
                'is_finished': production_order.is_finished(),
                'has_wip_materials': production_order.has_wip_materials(),
                'was_completed_successfully': production_order.was_completed_successfully(),
                'was_cancelled': production_order.was_cancelled(),
                'can_return_wip_materials': production_order.can_return_wip_materials(),
                'wip_materials': wip_summary,
                'wip_materials_count': len(wip_summary)
            }
            
            return JsonResponse(data)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
