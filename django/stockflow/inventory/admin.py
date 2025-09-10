from django.contrib import admin
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import Warehouse, Stock, StockMovement, MaterialReservation


class WarehouseUserInline(admin.TabularInline):
    """Inline for managing warehouse user assignments"""
    model = User.groups.through
    extra = 0
    verbose_name = "Warehouse User"
    verbose_name_plural = "Assigned Users"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if hasattr(self, 'parent_obj') and self.parent_obj:
            group = self.parent_obj.get_warehouse_group()
            if group:
                return qs.filter(group=group)
        return qs.none()


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'is_active', 'assigned_users_count', 'created_at', 'warehouse_permissions_link']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by', 'version']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'code', 'is_active')
        }),
        ('Details', {
            'fields': ('address', 'note')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by', 'version'),
            'classes': ('collapse',)
        }),
    )
    
    # inlines = [WarehouseUserInline]
    
    def assigned_users_count(self, obj):
        """Display count of assigned users"""
        group = obj.get_warehouse_group()
        if group:
            count = group.user_set.count()
            if count > 0:
                return format_html(
                    '<a href="{}?groups__id__exact={}">{} users</a>',
                    reverse('admin:auth_user_changelist'),
                    group.id,
                    count
                )
            return "0 users"
        return "No group"
    assigned_users_count.short_description = "Assigned Users"
    
    def warehouse_permissions_link(self, obj):
        """Display link to manage warehouse permissions"""
        group = obj.get_warehouse_group()
        if group:
            return format_html(
                '<a href="{}">Manage Permissions</a>',
                reverse('admin:auth_group_change', args=[group.id])
            )
        return "No permissions"
    warehouse_permissions_link.short_description = "Permissions"
    
    def save_model(self, request, obj, form, change):
        """Set audit fields and create permissions for new warehouses"""
        if not change:  # New warehouse
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def response_add(self, request, obj, post_url_override=None):
        """Show success message with permission info after creating warehouse"""
        response = super().response_add(request, obj, post_url_override)
        self.message_user(
            request,
            f'Warehouse "{obj}" created successfully with warehouse-specific permissions.',
        )
        return response
    
    actions = ['create_permissions', 'assign_selected_users']
    
    def create_permissions(self, request, queryset):
        """Action to recreate permissions for selected warehouses"""
        count = 0
        for warehouse in queryset:
            warehouse._create_warehouse_permissions()
            count += 1
        
        self.message_user(
            request,
            f'Successfully created/updated permissions for {count} warehouse(s).',
        )
    create_permissions.short_description = "Create/update warehouse permissions"


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['item_sku', 'warehouse', 'lot_number', 'expiry_date', 'available_quantity']
    list_filter = ['warehouse', 'expiry_date']
    search_fields = ['item_sku__name', 'item_sku__sku_code', 'lot_number']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['id', 'warehouse', 'reference_type', 'status', 'created_at']
    list_filter = ['warehouse', 'reference_type', 'status', 'created_at']
    search_fields = ['reference_id', 'note']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


@admin.register(MaterialReservation)
class MaterialReservationAdmin(admin.ModelAdmin):
    list_display = ['item_sku', 'warehouse', 'reserved_quantity', 'reference_type', 'created_at']
    list_filter = ['warehouse', 'reference_type', 'created_at']
    search_fields = ['item_sku__name', 'item_sku__sku_code']
    readonly_fields = ['created_at', 'updated_at']
