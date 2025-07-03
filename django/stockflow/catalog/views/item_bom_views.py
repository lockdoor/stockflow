from django.views.generic import ListView
from catalog.models.item import ItemSKU
from django.contrib.auth.mixins import LoginRequiredMixin

class ItemAutocompleteView(LoginRequiredMixin, ListView):
    model = ItemSKU
    template_name = "catalog/bom/partials/bom-autocomplete-list.html"
    context_object_name = "items"
    
    def get_queryset(self):
        # print("Autocomplete query:", self.request.GET)
        query = self.request.GET.get("q", "")
        category_id = self.request.GET.get("category")

        qs = ItemSKU.objects.filter(name__icontains=query)

        if category_id and category_id != "0":
            try:
                qs = qs.filter(category__id=int(category_id))
            except ValueError:
                pass  # กันกรณี category_id ไม่ใช่ตัวเลข

        return qs[:5]