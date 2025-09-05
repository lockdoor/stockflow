from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404, reverse
from django.views.generic import ListView

from production.models.production_order import ProductionOrder


class WIPStockListView(PermissionRequiredMixin, LoginRequiredMixin, ListView):
    """View to show WIP stock movements for a specific production order"""
    permission_required = 'production.view_productionorder'
    template_name = 'production/orders/wip-stock-list.html'
    context_object_name = 'wip_movements'
    paginate_by = 50  # แสดง 50 รายการต่อหน้า

    def get_queryset(self):
        """Get WIP movements for the specified production order"""
        from production.models.wip_stock_movement import WIPStockMovement
        
        # Get production order from URL
        self.production_order = get_object_or_404(ProductionOrder, pk=self.kwargs['pk'])
        
        queryset = WIPStockMovement.objects.filter(
            production_order=self.production_order
        ).select_related(
            'item_sku',
            'source_stock_movement'
        ).order_by('-created_at')
        
        # Apply movement type filter if provided
        movement_type = self.request.GET.get('movement_type')
        if movement_type and movement_type in dict(WIPStockMovement.MovementType.choices):
            queryset = queryset.filter(movement_type=movement_type)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add production order to context
        context['production_order'] = self.production_order
        
        context['breadcrumb_items'] = [
            {'name': 'Dashboard', 'url': 'dashboard'},
            {'name': 'Production', 'url': reverse('production:dashboard')},
            {'name': 'Production Order', 'url': reverse('production:production-order-detail', args=[self.production_order.id])},
            {'name': 'WIP Stock', 'url': None}
        ]
        
        # Add filter information
        context['current_filter'] = self.request.GET.get('movement_type', '')
        
        # Calculate WIP Balance by item_sku
        from django.db.models import Sum, Q, Case, When, DecimalField, F
        from production.models.wip_stock_movement import WIPStockMovement
        
        wip_balance = WIPStockMovement.objects.filter(
            production_order=self.production_order
        ).values(
            'item_sku',
            'item_sku__name', 
            'item_sku__sku_code',
            'item_sku__unit'
        ).annotate(
            balance=Sum(
                Case(
                    When(movement_type='IN', then='quantity'),
                    When(movement_type='ADJUST', then='quantity'),
                    When(movement_type__in=['OUT', 'LOSS', 'RETURN'], then=-F('quantity')),
                    default=0,
                    output_field=DecimalField()
                )
            )
        ).filter(balance__gt=0).order_by('-balance')
        
        context['wip_balance'] = wip_balance
        
        return context
