# catalog/views/category_views.py

from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from django.urls import reverse_lazy
from catalog.models.category import Category
from catalog.forms.category_form import CategoryForm

class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = 'catalog/category/category.html'
    context_object_name = 'categories'
    ordering = ['-created_at']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CategoryForm()
        return context


class CategoryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'catalog/category/partials/category-form.html'
    permission_required = 'catalog.add_category'

    def form_valid(self, form):
        category = form.save(commit=False)
        category.created_by = self.request.user
        category.updated_by = self.request.user
        category.save()
        context = {'category': category}
        response = render(self.request, 'catalog/category/partials/category-row.html', context)
        response['HX-Trigger'] = 'success'
        return response

    def form_invalid(self, form):
        response = render(self.request, self.template_name, {'form': form})
        response['HX-Retarget'] = '#category-form-container'
        response['HX-Reswap'] = 'innerHTML'
        return response

class CategoryUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'catalog/category/partials/category-form.html'
    permission_required = 'catalog.change_category'
    pk_url_kwarg = 'pk'

    def form_valid(self, form):
        category = form.save(commit=False)
        category.updated_by = self.request.user
        category.save()
        context = {'category': category}
        response = render(self.request, 'catalog/category/partials/category-row.html', context)
        response['HX-Trigger'] = 'success'
        return response

    def form_invalid(self, form):
        response = render(self.request, self.template_name, {'form': form})
        response['HX-Retarget'] = '#category-form-container'
        response['HX-Reswap'] = 'innerHTML'
        return response


class CategoryDetailView(LoginRequiredMixin, DetailView):
    model = Category
    template_name = 'catalog/category/category-detail.html'
    context_object_name = 'category'
    # pk_url_kwarg = 'pk'
    # def get_object(self):
    #     return get_object_or_404(Category, pk=self.kwargs.get('pk'))
