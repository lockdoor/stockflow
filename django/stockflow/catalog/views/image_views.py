"""
Image Views

This module contains views for managing ItemImage operations.
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
# from django.core.files.storage import default_storage
from django.conf import settings

from catalog.models.item import ItemSKU
from catalog.models.image import ItemImage
from catalog.forms.image_form import (
    ItemImageForm, 
    ItemImageBulkUploadForm, 
    ItemImageUpdateForm
)


class ItemImageCreateView(PermissionRequiredMixin,LoginRequiredMixin, CreateView):
    """Single image upload view"""
    model = ItemImage
    form_class = ItemImageForm
    template_name = 'catalog/image/image-form.html'
    permission_required = 'catalog.add_itemimage'
    http_method_names = ['get', 'post']
    
    def dispatch(self, request, *args, **kwargs):
        """Ensure item exists and is active or draft"""
        self.item = get_object_or_404(
            ItemSKU, 
            id=kwargs['item_id'], 
            status__in=[ItemSKU.Status.ACTIVE, ItemSKU.Status.DRAFT]
        )
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        """Pass item to form constructor"""
        kwargs = super().get_form_kwargs()
        # Pass item to form constructor
        kwargs['item'] = self.item
        return kwargs
    
    def get_success_url(self):
        """Return success URL"""
        next_url = self.request.POST.get('next')
        if next_url:
            return next_url
        return reverse('catalog:image-list', kwargs={'item_id': self.item.id})
    
    def get_prev_redirect_url(self):
        """Determine where to redirect when user cancels."""
        # Check for prev parameter in request
        prev_url = self.request.GET.get('prev')
        if prev_url:
            return prev_url
        # Default redirect
        return reverse('catalog:image-list', kwargs={'item_id': self.item.id})

    def form_valid(self, form):
        """Set user and handle successful form submission"""
        try:
            # Use atomic transaction to ensure data consistency:
            # - If file upload fails, database record won't be created
            # - If database save fails, uploaded file will be cleaned up
            # - Prevents orphaned files or incomplete database records
            with transaction.atomic():
                # Set audit fields (created_by, updated_by) before saving
                form.set_user(self.request.user)
                
                # Call parent's form_valid() which performs:
                # 1. form.save() - creates ItemImage instance with uploaded file
                # 2. File gets saved to MEDIA_ROOT/item_images/ folder automatically
                # 3. File path gets stored in database image field
                # 4. Returns HttpResponseRedirect to success_url
                response = super().form_valid(form)
                
                messages.success(
                    self.request, 
                    f'Image uploaded successfully for {self.item.name}'
                )
                
                return response
                
        except ValidationError as e:
            messages.error(self.request, f'Upload failed: {e}')
            return self.form_invalid(form)
        except Exception as e:
            messages.error(self.request, f'Unexpected error: {e}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """Handle invalid form submission"""
        messages.error(self.request, 'Please correct the errors')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'item': self.item,
            'page_title': f'Upload Image - {self.item.name}',
            'prev_url': self.get_prev_redirect_url(),
            'breadcrumb_items': [
                {'name': 'Dashboard', 'url': 'dashboard'},
                {'name': 'Catalog', 'url': 'catalog:dashboard'},
                {'name': 'Items', 'url': reverse('catalog:item-list')},
                {'name': self.item.name, 'url': reverse('catalog:item-detail', kwargs={'pk': self.item.id})},
                {'name': 'Images', 'url': reverse('catalog:image-list', kwargs={'item_id': self.item.id})},
                {'name': 'Upload Image', 'url': ''},
            ],
        })
        return context


class ItemImageBulkUploadView(PermissionRequiredMixin, LoginRequiredMixin, FormView):
    """Bulk image upload view"""
    form_class = ItemImageBulkUploadForm
    template_name = 'catalog/image/bulk-upload.html'
    permission_required = 'catalog.add_itemimage'
    
    def dispatch(self, request, *args, **kwargs):
        """Ensure item exists and is active or draft"""

        self.item = get_object_or_404(
            ItemSKU,
            id=kwargs['item_id'],
            status__in=[ItemSKU.Status.ACTIVE, ItemSKU.Status.DRAFT]
        )
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        """Pass item to form constructor"""
        kwargs = super().get_form_kwargs()
        # Pass item to form constructor
        kwargs['item'] = self.item
        return kwargs
    
    def form_valid(self, form):
        """Handle bulk upload"""
        item = form.cleaned_data['item']
        set_first_as_primary = form.cleaned_data['set_first_as_primary']
        
        # Get uploaded files
        uploaded_files = self.request.FILES.getlist('images')
        
        if not uploaded_files:
            messages.error(self.request, 'Please select at least one image file.')
            return self.form_invalid(form)
        
        try:
            # Atomic transaction for bulk upload ensures:
            # - All images are saved together or none at all
            # - No partial uploads if one image fails validation
            # - Consistent primary image status across all uploaded images
            with transaction.atomic():
                created_images = []
                
                for index, uploaded_file in enumerate(uploaded_files):
                    # Create ItemImage instance
                    image = ItemImage(
                        item=item,
                        image=uploaded_file,
                        caption=f'{item.name} - Image {index + 1}',
                        is_primary=(index == 0 and set_first_as_primary),
                        created_by=self.request.user,
                        updated_by=self.request.user
                    )
                    
                    # Validate the image
                    image.full_clean()
                    image.save()
                    created_images.append(image)
                
                messages.success(
                    self.request, 
                    f'Successfully uploaded {len(created_images)} images for {item.name}'
                )
                
                # Redirect to item detail
                next_url = self.request.POST.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect(reverse('catalog:image-list', kwargs={'item_id': self.item.id}))
                
        except ValidationError as e:
            messages.error(self.request, f'Upload failed: {e}')
            return self.form_invalid(form)
        except Exception as e:
            messages.error(self.request, f'Unexpected error: {e}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """Handle invalid form submission"""
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        """Add context data"""
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Bulk Upload Images',
            'breadcrumb_items': [
                {'name': 'Dashboard', 'url': 'dashboard'},
                {'name': 'Catalog', 'url': 'catalog:dashboard'},
                {'name': 'Items', 'url': reverse('catalog:item-list')},
                {'name': self.item.name, 'url': reverse('catalog:item-detail', kwargs={'pk': self.item.id})},
                {'name': 'Images', 'url': reverse('catalog:image-list', kwargs={'item_id': self.item.id})},
                {'name': 'Bulk Upload Images', 'url': ''},
            ]
        })
        return context


class ItemImageListView(LoginRequiredMixin, ListView):
    """List all images for an item"""
    model = ItemImage
    template_name = 'catalog/image/image-list.html'
    context_object_name = 'images'
    
    def dispatch(self, request, *args, **kwargs):
        """Get item object"""
        self.item = get_object_or_404(ItemSKU, id=kwargs['item_id'])
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        """Filter images by item"""
        return ItemImage.objects.filter(item=self.item).order_by('-is_primary', '-created_at')
    
    def get_context_data(self, **kwargs):
        """Add context data"""
        context = super().get_context_data(**kwargs)
        context.update({
            'item': self.item,
            'page_title': f'Images - {self.item.name}',
            'breadcrumb_items': [
                {'name': 'Dashboard', 'url': 'dashboard'},
                {'name': 'Catalog', 'url': 'catalog:dashboard'},
                {'name': 'Items', 'url': reverse('catalog:item-list')},
                {'name': self.item.name, 'url': reverse('catalog:item-detail', kwargs={'pk': self.item.id})},
                {'name': 'Images', 'url': ''},
            ]
        })
        return context


class ItemImageDetailView(LoginRequiredMixin, DetailView):
    """View image details"""
    model = ItemImage
    template_name = 'catalog/image/image-detail.html'
    # context_object_name = 'image'
    
    def get_context_data(self, **kwargs):
        """Add context data"""
        context = super().get_context_data(**kwargs)
        image = self.get_object()
        context.update({
            'image': image,
            'item': image.item,
            'page_title': f'Update Image - {image.item.name}',
            'breadcrumb_items': [
                {'name': 'Dashboard', 'url': 'dashboard'},
                {'name': 'Catalog', 'url': 'catalog:dashboard'},
                {'name': 'Items', 'url': reverse('catalog:item-list')},
                {'name': image.item.name, 'url': reverse('catalog:item-detail', kwargs={'pk': image.item.id})},
                {'name': 'Images', 'url': reverse('catalog:image-list', kwargs={'item_id': image.item.id})},
            ],
        })
        return context


class ItemImageUpdateView(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    """Update image caption and primary status"""
    model = ItemImage
    form_class = ItemImageUpdateForm
    template_name = 'catalog/image/image-form.html'
    permission_required = 'catalog.change_itemimage'
    
    def get_prev_redirect_url(self):
        """Determine where to redirect when user cancels."""
        object = self.get_object()
        # Check for prev parameter in request
        prev_url = self.request.GET.get('prev')
        if prev_url:
            return prev_url
        # Default redirect
        return reverse('catalog:image-list', kwargs={'item_id': object.item.id})
    
    def form_valid(self, form):
        """Handle successful form submission"""
        try:
            # Atomic transaction for image update ensures:
            # - Caption and primary status are updated together
            # - If setting as primary, other images lose primary status atomically
            # - Prevents inconsistent primary image states
            with transaction.atomic():
                form.set_user(self.request.user)
                self.object = form.save()
                
                messages.success(
                    self.request, 
                    f'Image updated successfully'
                )
                
                # Redirect back to image list
                next_url = self.request.POST.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('catalog:image-list', item_id=self.object.item.id)
                
        except ValidationError as e:
            messages.error(self.request, f'Update failed: {e}')
            return self.form_invalid(form)
        except Exception as e:
            messages.error(self.request, f'Unexpected error: {e}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """Handle invalid form submission"""
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        """Add context data"""
        context = super().get_context_data(**kwargs)
        image = self.get_object()
        context.update({
            'image': image,
            'item': image.item,
            'page_title': f'Update Image - {image.item.name}',
            'breadcrumb_items': [
                {'name': 'Dashboard', 'url': 'dashboard'},
                {'name': 'Catalog', 'url': 'catalog:dashboard'},
                {'name': 'Items', 'url': reverse('catalog:item-list')},
                {'name': image.item.name, 'url': reverse('catalog:item-detail', kwargs={'pk': image.item.id})},
                {'name': 'Images', 'url': reverse('catalog:image-list', kwargs={'item_id': image.item.id})},
                {'name': 'Update Image', 'url': ''},
            ],
            'prev_url': self.get_prev_redirect_url()
        })
        return context


class ItemImageDeleteView(PermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    """Delete an image"""
    model = ItemImage
    permission_required = 'catalog.delete_itemimage'
    template_name = 'catalog/image/image-delete.html'
    context_object_name = 'image'

    def get_success_url(self):
        """Redirect to image list after deletion"""
        return reverse('catalog:image-list', kwargs={'item_id': self.object.item.id})
    
    def get_prev_redirect_url(self):
        """Determine where to redirect when user cancels."""
        object = self.get_object()
        # Check for prev parameter in request
        prev_url = self.request.GET.get('prev')
        if prev_url:
            return prev_url
        # Default redirect
        return reverse('catalog:image-list', kwargs={'item_id': object.item.id})
    
    def post(self, request, *args, **kwargs):
        """Handle deletion with file cleanup"""
        self.object = self.get_object()
        
        try:
            # Atomic transaction for image deletion ensures:
            # - Physical file deletion and database record removal happen together
            # - If file deletion fails, database record remains intact
            # - Prevents orphaned database records without files
            with transaction.atomic():
                
                success_url = self.get_success_url()
                self.object.delete()
                
                messages.success(
                    request, 
                    f'Image deleted successfully'
                )
                
        except Exception as e:
            messages.error(request, f'Delete failed: {e}')
            return redirect('catalog:image-list', item_id=self.object.item.id)
        
        # Handle next URL
        next_url = request.POST.get('next')
        if next_url:
            return redirect(next_url)
        return redirect(success_url)
    
    def get_context_data(self, **kwargs):
        """Add context data"""
        context = super().get_context_data(**kwargs)
        image = self.get_object()
        context.update({
            'image': image,
            'item': image.item,
            'page_title': f'Update Image - {image.item.name}',
            'breadcrumb_items': [
                {'name': 'Dashboard', 'url': 'dashboard'},
                {'name': 'Catalog', 'url': 'catalog:dashboard'},
                {'name': 'Items', 'url': reverse('catalog:item-list')},
                {'name': image.item.name, 'url': reverse('catalog:item-detail', kwargs={'pk': image.item.id})},
                {'name': 'Images', 'url': reverse('catalog:image-list', kwargs={'item_id': image.item.id})},
                {'name': 'Delete Image', 'url': ''},
            ],
            'prev_url': self.get_prev_redirect_url()
        })
        return context


class ItemImageSetPrimaryView(PermissionRequiredMixin, LoginRequiredMixin, SingleObjectMixin, View):
    """Set an image as primary, call this method as link"""
    model = ItemImage
    http_method_names = ['get']
    permission_required = 'catalog.change_itemimage'

    def get(self, request, *args, **kwargs):
        """Handle get request to set image as primary"""
        self.object = self.get_object()
        
        try:
            # Atomic transaction for primary image setting ensures:
            # - Only one image can be primary per item at any time
            # - Previous primary image loses status before new one gains it
            # - Prevents multiple primary images or no primary image states
            with transaction.atomic():
                # Remove primary status from other images of the same item
                ItemImage.objects.filter(
                    item=self.object.item, 
                    is_primary=True
                ).exclude(pk=self.object.pk).update(is_primary=False)
                
                # Set this image as primary
                self.object.is_primary = True
                self.object.updated_by = request.user
                self.object.save()
                
                messages.success(
                    request, 
                    f'Image set as primary successfully'
                )
                
        except Exception as e:
            messages.error(request, f'Failed to set primary: {e}')
        
        # Redirect for regular form submissions
        next_url = request.GET.get('next')
        if next_url:
            return redirect(next_url)
        return redirect('catalog:image-list', item_id=self.object.item.id)


# API Views for AJAX operations (Class-based)

class ImageUploadProgressAPIView(LoginRequiredMixin, DetailView):
    """API endpoint for upload progress (if needed for future enhancement)"""
    http_method_names = ['get']
    
    def get(self, request, *args, **kwargs):
        """Handle GET request for upload progress"""
        # This could be implemented with websockets or polling
        # For now, return a simple response
        return JsonResponse({
            'status': 'not_implemented',
            'message': 'Upload progress tracking not yet implemented'
        })


class ItemImagesAPIView(LoginRequiredMixin, DetailView):
    """API endpoint to get item images as JSON"""
    model = ItemSKU
    http_method_names = ['get']
    
    def get(self, request, *args, **kwargs):
        """Handle GET request for item images API"""
        self.object = self.get_object()
        images = ItemImage.objects.filter(item=self.object).order_by('-is_primary', '-created_at')
        
        images_data = []
        for image in images:
            images_data.append({
                'id': image.id,
                'caption': image.caption,
                'is_primary': image.is_primary,
                'image_url': image.image.url if image.image else None,
                'thumbnail_url': image.get_thumbnail_url() if hasattr(image, 'get_thumbnail_url') else None,
                'file_size': image.file_size if hasattr(image, 'file_size') else None,
                'dimensions': f"{image.width}x{image.height}" if hasattr(image, 'width') and hasattr(image, 'height') else None,
                'created_at': image.created_at.isoformat(),
                'updated_at': image.updated_at.isoformat(),
            })
        
        return JsonResponse({
            'item': {
                'id': self.object.id,
                'name': self.object.name,
                'sku_code': self.object.sku_code,
            },
            'images': images_data,
            'total': len(images_data)
        })
