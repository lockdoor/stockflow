from django.views.generic import CreateView, DetailView, UpdateView, DeleteView, ListView
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
    
