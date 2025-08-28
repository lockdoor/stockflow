from django.views.generic import CreateView, UpdateView, DeleteView
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from inventory.views import get_object_or_404
from production.forms.production_order_bom_form import ProductionOrderBOMForm
from production.models.production_order import ProductionOrder
from production.models.production_order_bom import ProductionOrderBOM


class ProductionOrderBOMCreateView(PermissionRequiredMixin, LoginRequiredMixin, CreateView):
    form_class = ProductionOrderBOMForm
    template_name = 'production/bom/production-order-bom-form.html'
    permission_required = 'add_productionorderbom'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        production_order = get_object_or_404(ProductionOrder, id=self.kwargs.get('production_order_id'))
        kwargs['production_order'] = production_order
        return kwargs
    
    def form_valid(self, form):
        bom: ProductionOrderBOM = form.save(commit=False)
        bom.created_by = self.request.user
        bom.updated_by = self.request.user
        bom.save()
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_id = self.kwargs.get('production_order_id')
        order = ProductionOrder.objects.get(id=order_id)
        context['production_order'] = ProductionOrder.objects.get(id=order_id)
        context['bom_items'] = ProductionOrderBOM.objects.filter(production_order=order).select_related('item_sku').order_by('created_at')
        context['prev_url'] = self.get_prev_redirect_url()
        context['breadcrumb_items'] = [
            {'name': 'Dashboard', 'url': 'dashboard'},
            {'name': 'Production', 'url': reverse('production:dashboard')},
            {'name': f'Order #{order.id}', 'url': reverse('production:production-order-detail', args=[order.id])},
            {'name': 'BOM ADD', 'url': None}
        ]
        return context
    
    def get_prev_redirect_url(self):
        """Determine where to redirect when user cancels."""
        # object = self.get_object()
        # Check for prev parameter in request
        order_id = self.kwargs.get('production_order_id')
        prev_url = self.request.GET.get('prev')
        if prev_url:
            return prev_url
        # Default redirect
        return reverse('production:production-order-detail', kwargs={'pk': order_id})

    def get_success_url(self):
        return reverse('production:production-order-add-bom', kwargs={'production_order_id': self.object.production_order.id})


class ProductionOrderBOMUpdateView(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):

    model = ProductionOrderBOM
    form_class = ProductionOrderBOMForm
    template_name = 'production/bom/production-order-bom-form.html'
    permission_required = 'change_productionorderbom'
    
    def get_success_url(self):
        return reverse('production:production-order-add-bom', kwargs={'production_order_id': self.object.production_order.id})

    def form_valid(self, form):
        bom: ProductionOrderBOM = form.save(commit=False)
        bom.updated_by = self.request.user
        bom.save()
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_id = self.kwargs.get('production_order_id')
        order = ProductionOrder.objects.get(id=order_id)
        context['production_order'] = ProductionOrder.objects.get(id=order_id)
        context['bom_items'] = ProductionOrderBOM.objects.filter(production_order=order).select_related('item_sku').order_by('created_at')
        context['prev_url'] = self.get_prev_redirect_url()
        context['breadcrumb_items'] = [
            {'name': 'Dashboard', 'url': 'dashboard'},
            {'name': 'Production', 'url': reverse('production:dashboard')},
            {'name': f'Order #{order.id}', 'url': reverse('production:production-order-detail', args=[order.id])},
            {'name': 'BOM EDIT', 'url': None}
        ]
        return context
    
    def get_prev_redirect_url(self):
        """Determine where to redirect when user cancels."""
        # object = self.get_object()
        # Check for prev parameter in request
        order_id = self.kwargs.get('production_order_id')
        prev_url = self.request.GET.get('prev')
        if prev_url:
            return prev_url
        # Default redirect
        return reverse('production:production-order-add-bom', kwargs={'production_order_id': order_id})


class ProductionOrderBOMDeleteView(PermissionRequiredMixin, LoginRequiredMixin, DeleteView):

    model = ProductionOrderBOM
    template_name = 'production/bom/production-order-bom-confirm-delete.html'
    permission_required = 'delete_productionorderbom'

    def get_success_url(self):
        return reverse('production:production-order-add-bom', kwargs={'production_order_id': self.object.production_order.id})
