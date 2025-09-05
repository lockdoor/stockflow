from django.views.generic import CreateView, DetailView, UpdateView, DeleteView, ListView, RedirectView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse

from ..models import ProductionOrder
from ..forms.production_order_form import ProductionOrderForm


class ProductionOrderCreateView(PermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = ProductionOrder
    permission_required = 'production.add_productionorder'
    form_class = ProductionOrderForm
    template_name = 'production/orders/production-order-form.html'

    def form_valid(self, form):
        try:
            production_order = form.save(commit=False)
            production_order.created_by = self.request.user
            production_order.updated_by = self.request.user
            production_order.save()
            return super().form_valid(form)
        except Exception as e:
            print(e)
            # Handle the exception (e.g., log it, return an error response, etc.)
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumb_items'] = [
            {'name': 'Dashboard', 'url': 'dashboard'},
            {'name': 'Production', 'url': reverse('production:dashboard')},
            {'name': 'New Production Order', 'url': None}
        ]
        context['prev_url'] = self.get_prev_redirect_url()
        return context
    
    def get_success_url(self):
        return reverse('production:production-order-detail', args=[self.object.id])
    
    def get_prev_redirect_url(self):
        """Determine where to redirect when user cancels."""
        # object = self.get_object()
        # Check for prev parameter in request
        prev_url = self.request.GET.get('prev')
        if prev_url:
            return prev_url
        # Default redirect
        return reverse('production:production-order-list')


class ProductionOrderDetailView(PermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = ProductionOrder
    permission_required = 'production.view_productionorder'
    template_name = 'production/orders/production-order-detail.html'
    context_object_name = 'production_order'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumb_items'] = [
            {'name': 'Dashboard', 'url': 'dashboard'},
            {'name': 'Production', 'url': reverse('production:dashboard')},
            {'name': 'Production Order', 'url': None}
        ]

        # --- BOM Material Stock Sufficiency ---
        from production.models.production_order_bom import ProductionOrderBOM
        from inventory.models.stock import Stock
        from inventory.models.material_reservation import MaterialReservation
        from django.db.models import Sum

        production_order = self.object
        warehouse = getattr(production_order, 'warehouse', None)
        bom_items = ProductionOrderBOM.objects.filter(production_order=production_order).select_related('item_sku')
        material_stock_status = []
        if warehouse:
            for bom in bom_items:
                total_stock = Stock.get_total_stock(bom.item_sku, warehouse)
                material_stock_status.append({
                    'item_sku': bom.item_sku,
                    'planned_quantity': bom.planned_quantity,
                    'available_stock': total_stock,
                    'is_sufficient': total_stock >= bom.planned_quantity if total_stock is not None else False
                })
        context['material_stock_status'] = material_stock_status

        # --- Over Reserved Reservations ---
        over_reserved_reservations = []
        reservations = MaterialReservation.objects.filter(
            reference_type=MaterialReservation.ReferenceType.PRODUCTION,
            reference_id=production_order.id
        ).select_related('item_sku', 'warehouse')
        for r in reservations:
            available = r.item_sku.stocks.filter(warehouse=r.warehouse).aggregate(total=Sum('available_quantity'))['total'] or 0
            if r.reserved_quantity > available:
                over_reserved_reservations.append({
                    'id': r.id,
                    'item_sku': r.item_sku,
                    'warehouse': r.warehouse,
                    'reserved_quantity': r.reserved_quantity,
                    'available_quantity': available,
                    'status': r.status,
                    'reference_type': r.reference_type,
                    'reference_id': r.reference_id,
                    'created_at': r.created_at,
                    'get_status_display': r.get_status_display(),
                })
        context['over_reserved_reservations'] = over_reserved_reservations

        # --- Stock Movements ---
        from inventory.models.stock_movement import StockMovement
        from inventory.models.stock_movement_item import StockMovementItem
        from django.db.models import Count

        # Get stock movements related to this production order
        stock_movements = StockMovement.objects.filter(
            reference_type=StockMovement.ReferenceType.PRODUCTION,
            reference_id=production_order.id
        ).annotate(
            items_count=Count('movement_items')
        ).prefetch_related(
            'movement_items__item_sku'
        ).order_by('-created_at')

        context['stock_movements'] = stock_movements

        # --- WIP Stock Movements ---
        from production.models.wip_stock_movement import WIPStockMovement
        
        wip_movements = WIPStockMovement.objects.filter(
            production_order=production_order
        ).select_related(
            'item_sku'
        ).order_by('-created_at')
        
        context['wip_movements'] = wip_movements

        # --- Production Processes ---
        from production.models.production_process import ProductionProcess
        
        production_processes = ProductionProcess.objects.filter(
            production_order=production_order
        ).order_by('-created_at')
        
        context['production_processes'] = production_processes

        return context




class ProductionOrderUpdateView(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = ProductionOrder
    permission_required = 'production.change_productionorder'
    form_class = ProductionOrderForm
    template_name = 'production/orders/production-order-form.html'
    context_object_name = 'production_order'
    
    def form_valid(self, form):
        try:
            order = form.save(commit=False)
            order.updated_by = self.request.user
            order.save()
            return super().form_valid(form)
        except Exception as e:
            # Handle the exception (e.g., log it, return an error response, etc.)
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumb_items'] = [
            {'name': 'Dashboard', 'url': 'dashboard'},
            {'name': 'Production', 'url': reverse('production:dashboard')},
            {'name': 'Production Order', 'url': reverse('production:production-order-detail', args=[self.object.id])},
            {'name': 'Edit', 'url': None}
        ]
        context['prev_url'] = self.get_prev_redirect_url()
        return context

    def get_success_url(self):
        return reverse('production:production-order-detail', args=[self.object.id])

    def get_prev_redirect_url(self):
        """Determine where to redirect when user cancels."""
        object = self.get_object()
        # Check for prev parameter in request
        prev_url = self.request.GET.get('prev')
        if prev_url:
            return prev_url
        # Default redirect
        return reverse('production:production-order-detail', kwargs={'pk': object.id})


class ProductionOrderListView(PermissionRequiredMixin, LoginRequiredMixin, ListView):
    model = ProductionOrder
    permission_required = 'production.view_productionorder'
    template_name = 'production/orders/production-order-list.html'
    context_object_name = 'production_orders'
    paginate_by = 5  # Show 20 orders per page

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumb_items'] = [
            {'name': 'Dashboard', 'url': 'dashboard'},
            {'name': 'Production', 'url': reverse('production:dashboard')},
            {'name': 'Production Orders', 'url': None}
        ]
        return context


class ProductionOrderDeleteView(PermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = ProductionOrder
    permission_required = 'production.delete_productionorder'
    template_name = 'production/orders/production-order-confirm-delete.html'
    context_object_name = 'production_order'
    # success_url = reverse('production:production-order-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumb_items'] = [
            {'name': 'Dashboard', 'url': 'dashboard'},
            {'name': 'Production', 'url': reverse('production:dashboard')},
            {'name': 'Production Order', 'url': reverse('production:production-order-detail', args=[self.object.id])},
            {'name': 'Delete', 'url': None}
        ]
        context['prev_url'] = self.get_prev_redirect_url()
        return context

    def get_success_url(self):
        return reverse('production:production-order-list')
    
    def get_prev_redirect_url(self):
        """Determine where to redirect when user cancels."""
        object = self.get_object()
        # Check for prev parameter in request
        prev_url = self.request.GET.get('prev')
        if prev_url:
            return prev_url
        # Default redirect
        return reverse('production:production-order-detail', kwargs={'pk': object.id})
    


from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect

class ProductionOrderCreatedStatusView(PermissionRequiredMixin, LoginRequiredMixin, RedirectView):
    permission_required = 'production.change_productionorder'

    def get_redirect_url(self, *args, **kwargs):
        pk = kwargs.get('pk')
        order = get_object_or_404(ProductionOrder, pk=pk)

        try:
            order.created_production_order(self.request.user)  # Use the new method to set status to CREATED
            messages.success(self.request, f"Production Order #{order.id} status changed to CREATED and materials reserved successfully.")
        except Exception as e:
            messages.error(self.request, f"Error occurred while changing Production Order #{order.id}: {str(e)}")
        
        return reverse('production:production-order-detail', args=[order.id])


class ProductionOrderDraftStatusView(PermissionRequiredMixin, LoginRequiredMixin, RedirectView):
    permission_required = 'production.change_productionorder'

    def get_redirect_url(self, *args, **kwargs):
        pk = kwargs.get('pk')
        order = get_object_or_404(ProductionOrder, pk=pk)

        try:
            order.draft_production_order(self.request.user)  # Use the new method to set status to DRAFT
            messages.success(self.request, f"Production Order #{order.id} status changed to DRAFT and material reservations cancelled successfully.")
        except Exception as e:
            messages.error(self.request, f"Error occurred while changing Production Order #{order.id}: {str(e)}")
        
        return reverse('production:production-order-detail', args=[order.id])
    