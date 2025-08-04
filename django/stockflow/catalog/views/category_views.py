# catalog/views/category_views.py

from django.views.generic import ListView, CreateView, UpdateView, DetailView, TemplateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from catalog.models.category import Category
from catalog.forms.category_form import CategoryForm

class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = 'catalog/category/category-list.html'
    context_object_name = 'categories'
    ordering = ['-created_at']

class CategoryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'catalog/category/category-form.html'
    permission_required = 'catalog.add_category'
    http_method_names = ['get', 'post']

    def form_valid(self, form):
        category = form.save(commit=False)
        category.created_by = self.request.user
        category.updated_by = self.request.user
        category.save()
        
        messages.success(self.request, f'Category "{category.name}" was created successfully.')
        
        # Redirect to next URL if provided, otherwise default to category list
        next_url = self.request.GET.get('next') or self.request.POST.get('next')
        if next_url:
            return redirect(next_url)
        return redirect('catalog:category-list')

    def form_invalid(self, form):
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass next URL to template for hidden form field
        context['next_url'] = self.request.GET.get('next', '')
        return context

class CategoryUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'catalog/category/category-form.html'
    permission_required = 'catalog.change_category'
    pk_url_kwarg = 'pk'
    http_method_names = ['get', 'post']

    def form_valid(self, form):
        category = form.save(commit=False)
        category.updated_by = self.request.user
        category.save()
        
        messages.success(self.request, f'Category "{category.name}" was updated successfully.')
        
        # Redirect to next URL if provided, otherwise default to category detail or list
        next_url = self.request.GET.get('next') or self.request.POST.get('next')
        if next_url:
            return redirect(next_url)
        # Default to category detail page for update
        return redirect('catalog:category-detail', pk=category.pk)

    def form_invalid(self, form):
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass next URL to template for hidden form field
        context['next_url'] = self.request.GET.get('next', '')
        return context

class CategoryDetailView(LoginRequiredMixin, DetailView):
    model = Category
    template_name = 'catalog/category/category-detail.html'
    context_object_name = 'category'

class CategoryDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Category
    permission_required = 'catalog.delete_category'
    http_method_names = ['delete']
    
    def delete(self, request, *args, **kwargs):
        category: Category = self.get_object()
        category_name = category.name

        if category.has_items:
            messages.error(request, f'Cannot delete category "{category_name}" because it contains items.')
            return redirect('catalog:category-list')
        
        # Safe to delete
        category.delete()
        messages.success(request, f'Category "{category_name}" was deleted successfully.')
        return redirect('catalog:category-list')
