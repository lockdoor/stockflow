from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from inventory.models.warehouse import Warehouse
from inventory.forms.warehouse_form import WarehouseForm
from django.shortcuts import render


class WarehouseIndexView(LoginRequiredMixin, TemplateView):
    template_name = 'inventory/warehouse/warehouse-index.html'

class WarehouseListView(LoginRequiredMixin, ListView):
    model = Warehouse
    template_name = 'inventory/warehouse/partials/warehouse-list.html'
    context_object_name = 'warehouses'
    paginate_by = 20
    ordering = 'name'

class WarehouseDetailView(LoginRequiredMixin, DetailView):
    model = Warehouse
    template_name = 'inventory/warehouse/warehouse-detail.html'
    context_object_name = 'warehouse'
    
class WarehouseCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    
    model = Warehouse
    form_class = WarehouseForm
    template_name = 'inventory/warehouse/partials/warehouse-form.html'
    permission_required = 'inventory.add_warehouse'
    
    def form_valid(self, form):
        warehouse = form.save(commit=False)
        warehouse.created_by = self.request.user
        warehouse.updated_by = self.request.user
        warehouse.save()
        context = {'warehouse': warehouse}
        response = render(self.request, 'inventory/warehouse/partials/warehouse-row.html', context)
        response['HX-Trigger'] = 'success'
        return response
    
    def form_invalid(self, form):
        response = render(self.request, self.template_name, {'form': form})
        response['HX-Retarget'] = '#warehouse-form'
        response['HX-Reswap'] = 'outerHTML'
        return response

class WarehouseUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Warehouse
    form_class = WarehouseForm
    template_name = 'inventory/warehouse/partials/warehouse-form.html'
    permission_required = 'inventory.change_warehouse'
    pk_url_kwarg = 'pk'

    def form_valid(self, form):
        warehouse = form.save(commit=False)
        warehouse.updated_by = self.request.user
        warehouse.save()
        context = {'warehouse': warehouse}
        response = render(self.request, 'inventory/warehouse/partials/warehouse-row.html', context)
        response['HX-Trigger'] = 'success'
        return response

    def form_invalid(self, form):
        response = render(self.request, self.template_name, {'form': form})
        response['HX-Retarget'] = '#warehouse-form'
        response['HX-Reswap'] = 'outerHTML'
        return response
