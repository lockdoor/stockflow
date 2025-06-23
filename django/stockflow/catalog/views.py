from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ValidationError
# models
from catalog.models.item import ItemSKU
from catalog.models.category import Category
# forms
from catalog.forms.create_raw_item_form import CreateRawItemForm
from catalog.forms.create_category_form import CreateCategoryForm

# Create your views here.
# create item if finished redirect to before page
@login_required
@permission_required('catalog.add_itemsku', raise_exception=True)
def create_raw_item_view(request):
    next_url = request.GET.get('next') or reverse('catalog:items')
    if request.method == 'POST':
        form = CreateRawItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.created_by = request.user
            item.updated_by = request.user
            item.save()
            return redirect(next_url)
    else:
        form = CreateRawItemForm()
    return render(request, 'catalog/create_raw_item.html', {'form': form, 'next_url': next_url})

# create category if finished redirect to before page
@login_required
@permission_required('catalog.add_category', raise_exception=True)
def create_category_view(request):
    next_url = request.GET.get('next') or reverse('catalog:categories')
    if request.method == 'POST':
        form = CreateCategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.created_by = request.user
            category.updated_by = request.user
            category.save()
            return redirect(next_url)
    else:
        form = CreateCategoryForm()
    return render(request, 'catalog/create_category.html', {'form': form, 'next_url': next_url})

@login_required
def categories_view(request):
    categories = Category.objects.all()
    return render(request, 'catalog/categories.html', {'categories': categories})

@login_required
def items_view(request):
    items = ItemSKU.objects.all()
    return render(request, 'catalog/items.html', {'items': items})

