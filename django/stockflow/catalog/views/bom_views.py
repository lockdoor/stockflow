from django.views.generic import ListView, CreateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
# forms
from catalog.forms.bom_form import BOMForm
# models
from catalog.models.bom import BOM
from catalog.models.category import Category
from catalog.models.item import ItemSKU

class BomListByParentIDView(LoginRequiredMixin, ListView):
    model = BOM
    template_name = 'catalog/bom/partials/bom-list.html'
    context_object_name = 'boms'
    
    def dispatch(self, request, *args, **kwargs):
        parent_id = self.kwargs.get('parent_id')
        if not parent_id:
            raise ValueError("Parent ID is required")
        self.parent_sku = get_object_or_404(ItemSKU, pk=parent_id)
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        return BOM.objects.filter(parent_sku=self.parent_sku).order_by('-id')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['parent_sku'] = self.parent_sku
        # เมื่อ return จาก HTMX request ต้องมี context boms เพื่อให้ template render table โดยตรง
        # ไม่ใช้ created_at เพราะไม่มี field นี้ใน BOM model
        return context
        # print(f"get_context_data for parent SKU: {self.parent_sku.sku_code}")
        return context

class BomCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = BOM
    form_class = BOMForm
    template_name = 'catalog/bom/partials/bom-form.html'
    permission_required = 'catalog.add_bom'
    
    def dispatch(self, request, *args, **kwargs):
        parent_id = self.kwargs.get('parent_id')
        if not parent_id:
            raise ValueError("Parent ID is required")
        self.parent_sku = get_object_or_404(ItemSKU, pk=parent_id)
        print(f"dispatch Creating BOM for parent SKU: {self.parent_sku.sku_code}")
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = Category.objects.all()
        context['parent_sku'] = self.parent_sku
        print(f"get_context_data Creating BOM for parent SKU: {self.parent_sku.sku_code}")
        return context

    def form_valid(self, form):
        try:
            bom = form.save(commit=False)
            bom.created_by = self.request.user
            bom.updated_by = self.request.user
            bom.parent_sku = self.parent_sku
            bom.save()
            context = {'bom': bom}
            response = render(self.request, 'catalog/bom/partials/bom-row.html', context)
            response['HX-Trigger'] = 'success'
            return response
        except ValueError as e:
            form.add_error(None, e)
            return self.form_invalid(form)

    def form_invalid(self, form):
        response = render(self.request, self.template_name, {'form': form, 'parent_sku': self.parent_sku})
        response['HX-Retarget'] = '#bom-form-container'
        response['HX-Reswap'] = 'innerHTML'
        return response
    
class BomDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'catalog.delete_bom'
    
    def delete(self, request, pk):
        try:
            bom = BOM.objects.get(pk=pk)
            bom.delete()
            return HttpResponse("")
        except BOM.DoesNotExist:
            return HttpResponse(status=404)