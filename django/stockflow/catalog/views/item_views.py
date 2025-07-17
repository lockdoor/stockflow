from django.views.generic import ListView, CreateView, UpdateView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from django.urls import reverse_lazy

# from catalog.forms.category_form import CategoryForm
from catalog.models.category import Category
from catalog.models.item import ItemSKU, ItemSKUType
# froms
from catalog.forms.item_form import ItemForm
from catalog.forms.bom_form import BOMForm

class ItemListView(LoginRequiredMixin, ListView):
    model = ItemSKU
    template_name = 'catalog/item/item.html'
    context_object_name = 'items'
    ordering = ['-created_at']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ItemForm()
        return context
    
class ItemCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = ItemSKU
    form_class = ItemForm
    template_name = 'catalog/item/partials/item-form.html'
    permission_required = 'catalog.add_itemsku'

    def form_valid(self, form):
        item = form.save(commit=False)
        item.created_by = self.request.user
        item.updated_by = self.request.user
        item.save()
        context = {'item': item}
        response = render(self.request, 'catalog/item/partials/item-row.html', context)
        response['HX-Trigger'] = 'success'
        return response

    def form_invalid(self, form):
        response = render(self.request, self.template_name, {'form': form})
        response['HX-Retarget'] = '#item-form-container'
        response['HX-Reswap'] = 'innerHTML'
        return response
    
class ItemUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = ItemSKU
    form_class = ItemForm
    template_name = 'catalog/item/partials/item-form.html'
    permission_required = 'catalog.change_itemsku'
    pk_url_kwarg = 'pk'

    def form_valid(self, form):
        item = form.save(commit=False)
        item.updated_by = self.request.user
        item.save()
        context = {'item': item}
        response = render(self.request, 'catalog/item/partials/item-row.html', context)
        response['HX-Trigger'] = 'success'
        return response
    
    def form_invalid(self, form):
        response = render(self.request, self.template_name, {'form': form})
        response['HX-Retarget'] = '#item-form-container'
        response['HX-Reswap'] = 'innerHTML'
        return response

class ItemDetailView(LoginRequiredMixin, DetailView):
    model = ItemSKU
    template_name = 'catalog/item/item-detail.html'
    context_object_name = 'item'
