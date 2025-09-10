"""
Production Process Detail View

View สำหรับแสดงรายละเอียดของ Production Process ที่ CONFIRMED แล้ว
"""

from django.views.generic import DetailView
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.contrib.auth.mixins import LoginRequiredMixin

from production.models.production_order import ProductionOrder
from production.models.production_process import ProductionProcess
from common.mixins.redirect import RedirectMixin
from inventory.utils.warehouse_permissions import WarehousePermissionMixin


class ProductionProcessDetailView(LoginRequiredMixin, RedirectMixin, WarehousePermissionMixin, DetailView):
    """
    View สำหรับแสดงรายละเอียดของ Production Process
    รองรับเฉพาะ process ที่มีสถานะ CONFIRMED แล้ว
    """
    model = ProductionProcess
    template_name = 'production/production-process/production-process-detail.html'
    context_object_name = 'process'
    pk_url_kwarg = 'process_id'
    required_warehouse_operation = 'view_production_process'

    def get_warehouse_from_request(self):
        """Get warehouse from production order"""
        production_order_id = self.kwargs.get('production_order_id')
        production_order = get_object_or_404(ProductionOrder, id=production_order_id)
        return production_order.warehouse

    def get_object(self, queryset=None):
        """Get production process object with security checks"""
        production_order_id = self.kwargs.get('production_order_id')
        process_id = self.kwargs.get('process_id')
        
        # ตรวจสอบว่า production order มีอยู่
        production_order = get_object_or_404(ProductionOrder, id=production_order_id)
        
        # ตรวจสอบว่า production process มีอยู่และเป็นของ production order นี้
        process = get_object_or_404(
            ProductionProcess,
            id=process_id,
            production_order=production_order
        )
        
        # อนุญาตให้ดู process ที่ CONFIRMED แล้วเท่านั้น
        if process.status != ProductionProcess.StatusChoices.CONFIRMED:
            raise Http404("Production process must be confirmed to view details")
        
        return process

    def get_context_data(self, **kwargs):
        """Add additional context data"""
        context = super().get_context_data(**kwargs)
        process = self.get_object()
        
        context.update({
            'production_order': process.production_order,
            'production_results': process.production_results.all().order_by('item_sku__name'),
            'production_losses': process.production_losses.all().order_by('item_sku__name'),
        })
        
        return context
