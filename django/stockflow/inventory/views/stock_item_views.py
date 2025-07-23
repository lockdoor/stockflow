from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from inventory.models.stock_movement_item import StockMovementItem
from inventory.models.stock_movement import StockMovement
from django.http import Http404, HttpResponse

class StockItemMovementListView(LoginRequiredMixin, ListView):
    model = StockMovementItem
    template_name = 'inventory/item-movement/partials/item-movement-list.html'
    context_object_name = 'movement_items'
    paginate_by = 20

    def get_queryset(self):
        stock_movement_id = self.kwargs.get('stock_movement_id')
        if not stock_movement_id:
            raise Http404
        stock_movememt = StockMovement.objects.filter(id=stock_movement_id).first()
        if not stock_movememt:
            raise Http404("Stock movement not found")
        return StockMovementItem.objects.filter(stock_movement_id=stock_movement_id).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stock_movement_id'] = self.kwargs.get('stock_movement_id')
        return context
