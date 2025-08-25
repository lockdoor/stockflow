from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from production.models.production_order import ProductionOrder

class ProductionDashboardView(PermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = 'production/dashboard.html'
    permission_required = 'production.view_productionorder'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = ProductionOrder.objects.all()
        context['total_orders'] = qs.count()
        context['in_progress_count'] = qs.filter(status=ProductionOrder.Status.IN_PROGRESS).count()
        context['completed_count'] = qs.filter(status=ProductionOrder.Status.COMPLETED).count()
        context['cancelled_count'] = qs.filter(status=ProductionOrder.Status.CANCELLED).count()
        context['recent_orders'] = qs.select_related('warehouse').order_by('-created_at')[:10]
        context['breadcrumb_items'] = [
            {'name': 'Dashboard', 'url': 'dashboard'},
            {'name': 'Production', 'url': None}
        ]
        return context
