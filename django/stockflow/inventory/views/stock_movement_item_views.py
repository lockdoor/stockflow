from django.core.exceptions import PermissionDenied
from django.views.generic import ListView, CreateView, UpdateView, View
from ..mixins.warehouse import WarehousePermissionMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from inventory.models.stock_movement_item import StockMovementItem
from inventory.models.stock_movement import StockMovement
from inventory.models.stock import Stock
from inventory.models.material_reservation import MaterialReservation
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum
from decimal import Decimal
from common.mixins.redirect import RedirectMixin
import json

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


class StockMovementItemProductionCreateView(RedirectMixin, WarehousePermissionMixin, LoginRequiredMixin, View):
    """
    View for creating stock movement items for production (bulk insert)
    This view handles withdrawal of materials based on production order BOM
    """
    permission_required_base = 'add_stockmovementitem'
    http_method_names = ['get', 'post']

    def get_default_success_url(self, stock_movement=None):
        """Default success URL for production withdrawal - go to stock movement detail"""
        if stock_movement:
            return reverse('inventory:stock-movement-detail', kwargs={'pk': stock_movement.pk})
        return reverse('inventory:stock-movement-list')
    
    def get_default_prev_url(self, stock_movement=None):
        """Default previous URL for production withdrawal - back to production order"""
        if stock_movement and stock_movement.reference_type == StockMovement.ReferenceType.PRODUCTION:
            try:
                from django.urls import reverse
                return reverse('production:production-order-detail', kwargs={'pk': stock_movement.reference_id})
            except:
                pass
        if stock_movement:
            return reverse('inventory:stock-movement-detail', kwargs={'pk': stock_movement.pk})
        return reverse('inventory:stock-movement-list')

    def get_context_data(self, **kwargs):
        """Prepare context data for the production withdrawal form"""
        context = {}
        stock_movement_id = self.kwargs.get('stock_movement_id')
        
        if not stock_movement_id:
            raise Http404("Stock movement ID is required")
            
        try:
            stock_movement = get_object_or_404(StockMovement, id=stock_movement_id)
            
            # Validate that this is a production-related stock movement
            if stock_movement.reference_type != StockMovement.ReferenceType.PRODUCTION:
                raise PermissionDenied("This stock movement is not for production")
                
            if not stock_movement.reference_id:
                raise PermissionDenied("No production order reference found")
            
            # Get production order
            from production.models import ProductionOrder
            production_order = get_object_or_404(ProductionOrder, id=stock_movement.reference_id)
            
            # Get production order BOMs (products to produce)
            production_boms = production_order.boms.select_related('item_sku').all()
            
            if not production_boms.exists():
                raise ValueError("No BOM items found for this production order")
            
            # Prepare BOM data with components
            bom_data = {}
            material_reservations_data = {}
            stock_availability_data = {}
            all_components = set()
            
            from production.models import ProductionOrderBOM
            for prod_bom in production_boms:
                prod_bom: ProductionOrderBOM
                product_sku = prod_bom.item_sku # parent SKU
                
                # Get BOM components for this product
                from catalog.models import BOM
                components = BOM.objects.filter(parent_sku=product_sku).select_related('component_sku')
                
                if components.exists():
                    bom_data[product_sku.sku_code] = {
                        'product_name': product_sku.name,
                        'planned_quantity': float(prod_bom.planned_quantity),
                        'unit': product_sku.unit,
                        'components': {}
                    }
                    
                    for component in components:
                        component_sku = component.component_sku
                        all_components.add(component_sku)
                        
                        bom_data[product_sku.sku_code]['components'][component_sku.sku_code] = {
                            'component_name': component_sku.name,
                            'bom_quantity': float(component.quantity),
                            'unit': component_sku.unit
                        }
            
            # Get material reservations for all components
            if all_components:
                reservations = MaterialReservation.objects.filter(
                    reference_type=MaterialReservation.ReferenceType.PRODUCTION,
                    reference_id=production_order.id,
                    item_sku__in=all_components
                ).select_related('item_sku')
                
                for reservation in reservations:
                    sku_code = reservation.item_sku.sku_code
                    material_reservations_data[sku_code] = {
                        'reserved_quantity': float(reservation.reserved_quantity),
                        'status': reservation.status
                    }
            
            # Get stock availability for all components
            if all_components:
                for component_sku in all_components:
                    # Get total available stock for this component in the warehouse
                    available_stock = Stock.objects.filter(
                        item_sku=component_sku,
                        warehouse=stock_movement.warehouse
                    ).aggregate(
                        total_available=Sum('available_quantity')
                    )['total_available'] or Decimal('0')
                    
                    stock_availability_data[component_sku.sku_code] = {
                        'available_quantity': float(available_stock)
                    }
            
            # Get existing movement items for this stock movement
            existing_movement_items = StockMovementItem.objects.filter(
                stock_movement=stock_movement
            ).select_related('item_sku')
            
            existing_items_data = {}
            for item in existing_movement_items:
                existing_items_data[item.item_sku.sku_code] = {
                    'quantity': float(item.quantity),
                    'note': item.note or '',
                    'id': item.id
                }
            
            context.update({
                'stock_movement': stock_movement,
                'production_order': production_order,
                'warehouse': stock_movement.warehouse,
                'production_boms': production_boms,
                'bom_data': bom_data,
                'material_reservations': material_reservations_data,
                'stock_availability': stock_availability_data,
                'existing_items': existing_items_data,
                'bom_data_json': json.dumps(bom_data),
                'stock_data_json': json.dumps(stock_availability_data),
                'reservations_data_json': json.dumps(material_reservations_data),
                'prev_url': self.get_prev_redirect_url(stock_movement),
                'next_url': self.get_success_redirect_url(stock_movement)
            })
            
        except ProductionOrder.DoesNotExist:
            raise Http404("Production order not found")
        except Exception as e:
            raise Http404(f"Error preparing production data: {str(e)}")
        
        return context

    def get(self, request, *args, **kwargs):
        """Handle GET request - display the production withdrawal form"""
        context = self.get_context_data(**kwargs)
        return render(request, 'inventory/stock-movement-item/stock-movement-item-production-form.html', context)

    def post(self, request, *args, **kwargs):
        """
        Handle POST request - create draft movement items for production withdrawal.
        
        This creates StockMovementItem objects in DRAFT status, allowing users to:
        1. Plan material withdrawal quantities
        2. Review and modify the plan before execution
        3. Confirm the stock movement later to apply actual stock changes
        """
        stock_movement_id = self.kwargs.get('stock_movement_id')
        stock_movement = get_object_or_404(StockMovement, id=stock_movement_id)
        
        # Validate that stock movement is in DRAFT status
        if stock_movement.status != StockMovement.Status.DRAFT:
            messages.error(request, 'Can only add items to draft stock movements')
            return redirect('inventory:stock-movement-detail', pk=stock_movement_id)
        
        try:
            with transaction.atomic():
                created_items = []
                updated_items = []
                errors = []
                
                # Parse form data
                # Expected format: withdraw_qty_<sku_code>, note_<sku_code>
                for key, value in request.POST.items():
                    if key.startswith('withdraw_qty_') and value:
                        sku_code = key.replace('withdraw_qty_', '')
                        quantity = Decimal(value)
                        note = request.POST.get(f'note_{sku_code}', '')
                        
                        if quantity > 0:  # Only process if quantity > 0
                            try:
                                # Get the item SKU
                                from catalog.models import ItemSKU
                                item_sku = ItemSKU.objects.get(sku_code=sku_code)
                                
                                # Check if movement item already exists
                                existing_item = StockMovementItem.objects.filter(
                                    stock_movement=stock_movement,
                                    item_sku=item_sku
                                ).first()
                                
                                if existing_item:
                                    # Update existing item
                                    existing_item.quantity = quantity
                                    existing_item.note = note
                                    existing_item.movement_type = StockMovementItem.MovementType.OUT  # Ensure movement type is OUT for production withdrawal
                                    existing_item.updated_by = request.user
                                    existing_item.save()
                                    updated_items.append(existing_item)
                                else:
                                    # Create new movement item
                                    movement_item = StockMovementItem.objects.create(
                                        stock_movement=stock_movement,
                                        item_sku=item_sku,
                                        movement_type=StockMovementItem.MovementType.OUT,  # Production withdrawal is always OUT
                                        quantity=quantity,
                                        lot_number='DRAFT',  # Use default lot number for draft items
                                        note=note,
                                        created_by=request.user,
                                        updated_by=request.user
                                    )
                                    created_items.append(movement_item)
                                    
                            except ItemSKU.DoesNotExist:
                                errors.append(f'Item SKU {sku_code} not found')
                            except Exception as e:
                                errors.append(f'Error processing {sku_code}: {str(e)}')
                
                # Delete existing items that are not in the current submission
                submitted_skus = set()
                for key in request.POST.keys():
                    if key.startswith('withdraw_qty_'):
                        sku_code = key.replace('withdraw_qty_', '')
                        quantity = request.POST.get(key, '0')
                        if quantity and Decimal(quantity) > 0:
                            submitted_skus.add(sku_code)
                
                # Remove items not in submission
                existing_items = StockMovementItem.objects.filter(stock_movement=stock_movement)
                for item in existing_items:
                    if item.item_sku.sku_code not in submitted_skus:
                        item.delete()
                
                # Prepare success message
                total_processed = len(created_items) + len(updated_items)
                if total_processed > 0:
                    messages.success(
                        request,
                        f'Draft withdrawal plan saved successfully! {total_processed} movement items prepared '
                        f'({len(created_items)} created, {len(updated_items)} updated). '
                        f'You can review and confirm the stock movement when ready.'
                    )
                
                if errors:
                    for error in errors:
                        messages.warning(request, error)
                
                # Use redirect mixin for success redirect
                return self.redirect_success(stock_movement)
                
        except Exception as e:
            messages.error(request, f'Error processing withdrawal: {str(e)}')
            # Use redirect mixin for error redirect
            return self.redirect_prev(stock_movement)

