from django.views.generic.base import TemplateView
from django.db.models import Sum
from inventory.models.material_reservation import MaterialReservation

class MaterialOverReservationListView(TemplateView):
    template_name = 'inventory/reservation/reservation-list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = MaterialReservation.objects.select_related('item_sku', 'warehouse').order_by('-created_at')
        over_reserved = []
        for r in qs:
            available = r.item_sku.stocks.filter(warehouse=r.warehouse).aggregate(total=Sum('available_quantity'))['total'] or 0
            if r.reserved_quantity > available:
                over_reserved.append({
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
        context['reservations'] = over_reserved
        context['breadcrumb_items'] = [
            {'name': 'Dashboard', 'url': 'dashboard'},
            {'name': 'Inventory', 'url': 'inventory:dashboard'},
            {'name': 'Over Reserved', 'url': None, 'active': True},
        ]
        return context
