"""
Stock Movement Image Views

This module contains views for managing StockMovementImage operations.
Handles image upload, display, update, and deletion functionality.

Author: StockFlow Team
Created: 2025
"""

import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import JsonResponse, Http404
from django.urls import reverse, reverse_lazy
from django.core.exceptions import ValidationError
from django.db import transaction
from django import forms
from django.views.generic import (
    CreateView, UpdateView, DeleteView, DetailView, ListView, FormView, View
)
from django.views.generic.detail import SingleObjectMixin
from django.conf import settings

from inventory.models.stock_movement import StockMovement
from inventory.models.stock_movement_image import StockMovementImage
from inventory.forms.stock_movement_image_form import (
    StockMovementImageForm, 
    StockMovementImageBulkUploadForm, 
    StockMovementImageUpdateForm
)


class StockMovementImageCreateView(PermissionRequiredMixin, LoginRequiredMixin, CreateView):
    """Single image upload view for stock movement"""
    model = StockMovementImage
    form_class = StockMovementImageForm
    template_name = 'inventory/stock_movement_image/image-form.html'
    permission_required = 'inventory.add_stockmovementimage'
    http_method_names = ['get', 'post']
    
    def dispatch(self, request, *args, **kwargs):
        """Ensure stock movement exists and is not failed"""
        self.stock_movement = get_object_or_404(
            StockMovement, 
            id=kwargs['stock_movement_id']
        )
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        """Pass stock_movement to form constructor"""
        kwargs = super().get_form_kwargs()
        kwargs['stock_movement'] = self.stock_movement
        return kwargs
    
    def get_success_url(self):
        """Return success URL"""
        next_url = self.request.POST.get('next')
        if next_url:
            return next_url
        return reverse('inventory:stock-movement-image-list', kwargs={'stock_movement_id': self.stock_movement.id})
    
    def get_prev_redirect_url(self):
        """Determine where to redirect when user cancels."""
        prev_url = self.request.GET.get('prev')
        if prev_url:
            return prev_url
        return reverse('inventory:stock-movement-detail', kwargs={'pk': self.stock_movement.id})

    def form_valid(self, form):
        """Set user and handle successful form submission"""
        try:
            with transaction.atomic():
                form.set_user(self.request.user)
                response = super().form_valid(form)
                
                messages.success(
                    self.request,
                    f'Image uploaded successfully for Stock Movement #{self.stock_movement.id}.'
                )
                return response
                
        except ValidationError as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)
        except Exception as e:
            messages.error(
                self.request,
                f'Error uploading image: {str(e)}'
            )
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        """Add additional context"""
        context = super().get_context_data(**kwargs)
        context['stock_movement'] = self.stock_movement
        context['prev_url'] = self.get_prev_redirect_url()
        return context


class StockMovementImageListView(PermissionRequiredMixin, LoginRequiredMixin, ListView):
    """List view for stock movement images"""
    model = StockMovementImage
    template_name = 'inventory/stock_movement_image/image-list.html'
    context_object_name = 'images'
    permission_required = 'inventory.view_stockmovementimage'
    paginate_by = 20
    ordering = ['-is_primary', '-created_at']
    
    def dispatch(self, request, *args, **kwargs):
        """Ensure stock movement exists"""
        self.stock_movement = get_object_or_404(
            StockMovement, 
            id=kwargs['stock_movement_id']
        )
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        """Filter images by stock movement"""
        return super().get_queryset().filter(
            stock_movement=self.stock_movement
        ).select_related('created_by', 'updated_by')
    
    def get_context_data(self, **kwargs):
        """Add additional context"""
        context = super().get_context_data(**kwargs)
        context['stock_movement'] = self.stock_movement
        return context


class StockMovementImageUpdateView(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    """Update view for stock movement image metadata"""
    model = StockMovementImage
    form_class = StockMovementImageUpdateForm
    template_name = 'inventory/stock_movement_image/image-form.html'
    permission_required = 'inventory.change_stockmovementimage'
    http_method_names = ['get', 'post']
    
    def get_success_url(self):
        """Return success URL"""
        next_url = self.request.POST.get('next')
        if next_url:
            return next_url
        return reverse('inventory:stock-movement-image-list', 
                      kwargs={'stock_movement_id': self.object.stock_movement.id})
    
    def get_prev_redirect_url(self):
        """Determine where to redirect when user cancels."""
        prev_url = self.request.GET.get('prev')
        if prev_url:
            return prev_url
        return reverse('inventory:stock-movement-image-list', 
                      kwargs={'stock_movement_id': self.object.stock_movement.id})

    def form_valid(self, form):
        """Set user and handle successful form submission"""
        try:
            with transaction.atomic():
                form.set_user(self.request.user)
                response = super().form_valid(form)
                
                messages.success(
                    self.request,
                    'Image updated successfully.'
                )
                return response
                
        except ValidationError as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)
        except Exception as e:
            messages.error(
                self.request,
                f'Error updating image: {str(e)}'
            )
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        """Add additional context"""
        context = super().get_context_data(**kwargs)
        context['stock_movement'] = self.object.stock_movement
        context['prev_url'] = self.get_prev_redirect_url()
        context['is_edit'] = True
        return context


class StockMovementImageDeleteView(PermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    """Delete view for stock movement image"""
    model = StockMovementImage
    template_name = 'inventory/stock_movement_image/image-delete.html'
    permission_required = 'inventory.delete_stockmovementimage'
    http_method_names = ['get', 'post']
    
    def get_success_url(self):
        """Return success URL after deletion"""
        return reverse('inventory:stock-movement-image-list', 
                      kwargs={'stock_movement_id': self.object.stock_movement.id})
    
    def delete(self, request, *args, **kwargs):
        """Handle deletion with file cleanup"""
        try:
            with transaction.atomic():
                response = super().delete(request, *args, **kwargs)
                messages.success(
                    self.request,
                    'Image deleted successfully.'
                )
                return response
        except Exception as e:
            messages.error(
                self.request,
                f'Error deleting image: {str(e)}'
            )
            return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        """Add additional context"""
        context = super().get_context_data(**kwargs)
        context['stock_movement'] = self.object.stock_movement
        return context


class StockMovementImageBulkUploadView(PermissionRequiredMixin, LoginRequiredMixin, FormView):
    """Bulk upload view for multiple stock movement images"""
    form_class = StockMovementImageBulkUploadForm
    template_name = 'inventory/stock_movement_image/bulk-upload.html'
    permission_required = 'inventory.add_stockmovementimage'
    http_method_names = ['get', 'post']
    
    def dispatch(self, request, *args, **kwargs):
        """Ensure stock movement exists"""
        self.stock_movement = get_object_or_404(
            StockMovement, 
            id=kwargs['stock_movement_id']
        )
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        """Pass stock_movement to form constructor"""
        kwargs = super().get_form_kwargs()
        kwargs['stock_movement'] = self.stock_movement
        return kwargs
    
    def get_success_url(self):
        """Return success URL"""
        return reverse('inventory:stock-movement-image-list', 
                      kwargs={'stock_movement_id': self.stock_movement.id})
    
    def form_valid(self, form):
        """Handle successful bulk upload"""
        try:
            with transaction.atomic():
                created_images = form.save(user=self.request.user)
                
                messages.success(
                    self.request,
                    f'{len(created_images)} image(s) uploaded successfully.'
                )
                return super().form_valid(form)
                
        except ValidationError as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)
        except Exception as e:
            messages.error(
                self.request,
                f'Error uploading images: {str(e)}'
            )
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        """Add additional context"""
        context = super().get_context_data(**kwargs)
        context['stock_movement'] = self.stock_movement
        return context


class StockMovementImageSetPrimaryView(PermissionRequiredMixin, LoginRequiredMixin, View):
    """Set image as primary for stock movement"""
    permission_required = 'inventory.change_stockmovementimage'
    http_method_names = ['post', 'get']
    
    def get_object(self):
        """Get the image object"""
        return get_object_or_404(StockMovementImage, pk=self.kwargs['pk'])
    
    def post(self, request, *args, **kwargs):
        """Handle POST request to set primary"""
        return self.set_primary(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        """Handle GET request to set primary (for convenience)"""
        return self.set_primary(request, *args, **kwargs)
    
    def set_primary(self, request, *args, **kwargs):
        """Set image as primary"""
        image = self.get_object()
        
        try:
            with transaction.atomic():
                # Set this image as primary
                image.is_primary = True
                image.updated_by = request.user
                image.save()
                
                messages.success(
                    request,
                    'Image set as primary successfully.'
                )
                
        except Exception as e:
            messages.error(
                request,
                f'Error setting image as primary: {str(e)}'
            )
        
        # Redirect back
        next_url = request.GET.get('next') or request.POST.get('next')
        if next_url:
            return redirect(next_url)
        
        return redirect('inventory:stock-movement-image-list', 
                       stock_movement_id=image.stock_movement.id)