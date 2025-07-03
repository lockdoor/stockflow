from django.views.generic import ListView, CreateView, View
from catalog.models.bom import BOM
from catalog.forms.bom_form import BOMForm
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import render
from django.http import HttpResponse
from django.core.exceptions import ValidationError

class BomListView(LoginRequiredMixin, ListView):
    model = BOM
    template_name = 'catalog/bom/bom-list.html'
    context_object_name = 'boms'
    ordering = ['-created_at']

class BomCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = BOM
    form_class = BOMForm
    template_name = 'catalog/bom/partials/bom-form.html'
    permission_required = 'catalog.add_bom'

    def form_valid(self, form):
        try:
            bom = form.save(commit=False)
            bom.created_by = self.request.user
            bom.updated_by = self.request.user
            bom.save()
            context = {'bom': bom}
            response = render(self.request, 'catalog/bom/partials/bom-row.html', context)
            response['HX-Trigger'] = 'success'
            return response
        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)

    def form_invalid(self, form):
        response = render(self.request, self.template_name, {'form': form})
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