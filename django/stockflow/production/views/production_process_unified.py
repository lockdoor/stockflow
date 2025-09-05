"""
ProductionProcessUnifiedView

View แบบรวมสำหรับ Production Process ที่สามารถจัดการ:
- Production Process (การสร้าง/แก้ไข)
- Production Results (ผลผลิต)
- Production Losses (การสูญเสีย)

ทั้งหมดในหน้าเดียว
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.urls import reverse
from django.db import transaction
from django.forms import inlineformset_factory
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from decimal import Decimal

from production.models.production_order import ProductionOrder
from production.models.production_process import ProductionProcess
from production.models.production_result import ProductionResult
from production.models.production_loss import ProductionLoss
from production.forms.production_process_form import (
    ProductionProcessForm,
    ProductionResultForm,
    ProductionLossForm
)
from production.mixins.production_permissions import ProductionPermissionMixin


class ProductionProcessUnifiedView(ProductionPermissionMixin, View):
    """View แบบรวมสำหรับ Production Process Management"""
    
    required_permission = 'production_process.manage'
    permission_denied_message = "You don't have permission to manage production processes."
    
    def get_production_order(self, production_order_id):
        """ดึง ProductionOrder และตรวจสอบ permissions"""
        return get_object_or_404(ProductionOrder, pk=production_order_id)
    
    def get_production_process(self, process_id):
        """ดึง ProductionProcess (อาจเป็น None สำหรับการสร้างใหม่)"""
        if process_id:
            return get_object_or_404(ProductionProcess, pk=process_id)
        return None
    
    def get_formsets(self):
        """สร้าง Formset classes"""
        ResultFormSet = inlineformset_factory(
            ProductionProcess, 
            ProductionResult,
            form=ProductionResultForm,
            extra=1,
            can_delete=True
        )
        
        LossFormSet = inlineformset_factory(
            ProductionProcess, 
            ProductionLoss,
            form=ProductionLossForm,
            extra=1,
            can_delete=True
        )
        
        return ResultFormSet, LossFormSet
    
    def _validate_wip_balance(self, form, result_formset, loss_formset, production_order):
        """
        Validate WIP balance for production process
        Returns dict of validation errors or empty dict if valid
        """
        from production.models.wip_stock_movement import WIPStockMovement
        from catalog.models.bom import BOM
        from decimal import Decimal
        
        validation_errors = {}
        
        # เก็บ item usage ทั้งหมดจาก results และ losses
        item_usage = {}
        
        # รวม consumption จาก BOM (ถ้ามี)
        if hasattr(form, 'cleaned_data') and form.cleaned_data.get('bom'):
            bom = form.cleaned_data['bom']
            quantity = form.cleaned_data.get('quantity', Decimal('0'))
            
            for bom_item in bom.bom_items.all():
                required_qty = bom_item.quantity * quantity
                item_sku = bom_item.item.sku_code
                if item_sku in item_usage:
                    item_usage[item_sku] += required_qty
                else:
                    item_usage[item_sku] = required_qty
        
        # รวม consumption จาก BOM ของ results (สำหรับ production)
        if result_formset.is_valid():
            for result_form in result_formset.forms:
                if result_form.is_valid() and not result_form.cleaned_data.get('DELETE', False):
                    item = result_form.cleaned_data.get('item')
                    quantity = result_form.cleaned_data.get('quantity', Decimal('0'))
                    
                    if item and quantity > 0:
                        # ตรวจสอบว่า item นี้มี BOM หรือไม่
                        try:
                            bom_items = BOM.objects.filter(parent_sku=item)
                            for bom in bom_items:
                                required_qty = bom.quantity * quantity
                                component_item = bom.component_sku  # ใช้ object แทน string
                                if component_item in item_usage:
                                    item_usage[component_item] += required_qty
                                else:
                                    item_usage[component_item] = required_qty
                        except Exception:
                            # ถ้าไม่มี BOM ก็ข้าม
                            pass
        
        # รวม consumption จาก losses
        if loss_formset.is_valid():
            for loss_form in loss_formset.forms:
                if loss_form.is_valid() and not loss_form.cleaned_data.get('DELETE', False):
                    item = loss_form.cleaned_data.get('item')
                    quantity = loss_form.cleaned_data.get('quantity', Decimal('0'))
                    
                    if item and quantity > 0:
                        if item in item_usage:
                            item_usage[item] += quantity
                        else:
                            item_usage[item] = quantity
        
        # ตรวจสอบ balance สำหรับแต่ละ item
        for item_sku, usage_qty in item_usage.items():
            current_balance = WIPStockMovement.get_wip_balance(production_order, item_sku)
            
            if usage_qty > current_balance:
                error_msg = (
                    f'Insufficient WIP balance for {item_sku.sku_code}. '
                    f'Required: {usage_qty}, Available: {current_balance}'
                )
                validation_errors['__all__'] = validation_errors.get('__all__', []) + [error_msg]
        
        return validation_errors
    
    def _handle_confirm(self, request, production_process, production_order):
        """Handle confirm action for production process"""
        # ตรวจสอบว่า process เป็น DRAFT หรือไม่
        if production_process.status != ProductionProcess.StatusChoices.DRAFT:
            messages.error(request, 'Only draft processes can be confirmed.')
            return redirect('production:production-order-detail', production_order.id)
        
        try:
            # ใช้ model method สำหรับ confirm
            production_process.confirm_process(request.user)
            
            messages.success(
                request, 
                f'Production process "{production_process.process_name}" has been confirmed successfully.'
            )
            
        except ValidationError as e:
            messages.error(request, f'Cannot confirm production process: {e}')
        except Exception as e:
            messages.error(request, f'Error confirming production process: {e}')
            
        return redirect('production:production-order-detail', production_order.id)
    
    def get(self, request, production_order_id, process_id=None):
        """แสดง form สำหรับสร้าง/แก้ไข Production Process"""
        
        production_order = self.get_production_order(production_order_id)
        production_process = self.get_production_process(process_id) # None สำหรับ create
        
        # สำหรับการสร้าง process ใหม่ ต้องตรวจสอบว่ามี WIP items อยู่หรือไม่
        if not production_process:  # CREATE mode
            from production.models.wip_stock_movement import WIPStockMovement
            has_wip_items = WIPStockMovement.objects.filter(
                production_order=production_order,
                movement_type=WIPStockMovement.MovementType.IN
            ).exists()
            
            if not has_wip_items:
                messages.error(
                    request, 
                    'Cannot create production process: No WIP (Work in Progress) items available. '
                    'Please transfer materials to WIP first.'
                )
                prev_url = request.GET.get('prev') or reverse('production:production-order-detail', args=[production_order.id])
                return redirect(prev_url)
        
        # สร้าง forms และ formsets
        form = ProductionProcessForm(
            instance=production_process, # None สำหรับ create, instance สำหรับ update
            production_order=production_order,
            initial={'production_order': production_order} if not production_process else None
        )
        
        ResultFormSet, LossFormSet = self.get_formsets()
        
        result_formset = ResultFormSet(
            instance=production_process,
            prefix='results',
            form_kwargs={'production_order': production_order}
        )
        
        loss_formset = LossFormSet(
            instance=production_process,
            prefix='losses',
            form_kwargs={'production_order': production_order}
        )
        
        context = {
            'form': form,
            'result_formset': result_formset,
            'loss_formset': loss_formset,
            'production_order': production_order,
            'production_process': production_process,
            'is_edit': production_process is not None,
        }
        
        return render(request, 'production/production-process/production-process-unified-form.html', context)
    
    def post(self, request, production_order_id, process_id=None):
        """จัดการ form submission"""
        
        production_order = self.get_production_order(production_order_id)
        production_process = self.get_production_process(process_id)
        
        # ตรวจสอบ action parameter
        action = request.POST.get('action')
        
        # หาก action เป็น confirm
        if action == 'confirm' and production_process:
            return self._handle_confirmation(request, production_process, production_order)
        
        # สำหรับการสร้าง process ใหม่ ต้องตรวจสอบว่ามี WIP items อยู่หรือไม่
        if not production_process:  # CREATE mode
            from production.models.wip_stock_movement import WIPStockMovement
            has_wip_items = WIPStockMovement.objects.filter(
                production_order=production_order,
                movement_type=WIPStockMovement.MovementType.IN
            ).exists()
            
            if not has_wip_items:
                messages.error(
                    request, 
                    'Cannot create production process: No WIP (Work in Progress) items available. '
                    'Please transfer materials to WIP first.'
                )
                prev_url = request.GET.get('prev') or reverse('production:production-order-detail', args=[production_order.id])
                return redirect(prev_url)
        
        # สร้าง forms และ formsets
        form = ProductionProcessForm(
            request.POST,
            instance=production_process,
            production_order=production_order,
            initial={'production_order': production_order} if not production_process else None
        )
        
        ResultFormSet, LossFormSet = self.get_formsets()
        
        result_formset = ResultFormSet(
            request.POST,
            instance=production_process,
            prefix='results',
            form_kwargs={'production_order': production_order}
        )
        
        loss_formset = LossFormSet(
            request.POST,
            instance=production_process,
            prefix='losses',
            form_kwargs={'production_order': production_order}
        )
        
        # Validate ทุก forms
        if form.is_valid() and result_formset.is_valid() and loss_formset.is_valid():
            try:
                with transaction.atomic():
                    # บันทึก Production Process
                    if not production_process:
                        # สร้างใหม่ - เป็น DRAFT เสมอ
                        production_process = form.save(commit=False)
                        production_process.production_order = production_order
                        production_process.status = 'DRAFT'  # บังคับให้เป็น DRAFT
                        production_process.created_by = request.user
                        production_process.updated_by = request.user
                        production_process.save()
                    else:
                        # แก้ไข - เฉพาะ DRAFT เท่านั้น
                        if production_process.status != 'DRAFT':
                            messages.error(
                                request, 
                                'Cannot modify confirmed production process. Only process name can be updated.'
                            )
                            # อนุญาตให้แก้ไขเฉพาะ process_name
                            production_process.process_name = form.cleaned_data.get('process_name')
                            production_process.updated_by = request.user
                            production_process.save()
                            
                            # Redirect ทันทีโดยไม่ต้องบันทึก formsets
                            messages.success(request, f'Production process "{production_process.process_name}" updated successfully.')
                            next_url = request.GET.get('next')
                            if next_url:
                                return redirect(next_url)
                            else:
                                return redirect('production:production-order-detail', production_order.id)
                        else:
                            # แก้ไข DRAFT process
                            production_process = form.save(commit=False)
                            production_process.updated_by = request.user
                            production_process.save()
                    
                    # บันทึก Results และ Losses เฉพาะเมื่อ process เป็น DRAFT
                    if production_process.status == 'DRAFT':
                        # บันทึก Results
                        result_formset.instance = production_process
                        results = result_formset.save(commit=False)
                        
                        for result in results:
                            result.production_process = production_process
                            result.created_by = request.user
                            result.updated_by = request.user
                            result.save()
                        
                        # ลบ results ที่ถูกทำเครื่องหมายลบ
                        for result in result_formset.deleted_objects:
                            result.delete()
                        
                        # บันทึก Losses
                        loss_formset.instance = production_process
                        losses = loss_formset.save(commit=False)
                        
                        for loss in losses:
                            loss.production_process = production_process
                            loss.created_by = request.user
                            loss.updated_by = request.user
                            loss.save()
                        
                        # ลบ losses ที่ถูกทำเครื่องหมายลบ
                        for loss in loss_formset.deleted_objects:
                            loss.delete()
                    
                    # Success message และ redirect
                    if not process_id:  # สร้างใหม่
                        messages.success(request, f'Production process "{production_process.process_name}" created successfully.')
                    else:  # แก้ไข
                        messages.success(request, f'Production process "{production_process.process_name}" updated successfully.')
                    
                    # Redirect โดยใช้ next parameter ถ้ามี
                    next_url = request.GET.get('next')
                    if next_url:
                        return redirect(next_url)
                    else:
                        return redirect('production:production-order-detail', production_order.id)
                        
            except Exception as e:
                messages.error(request, f'Error saving production process: {str(e)}')
        else:
            # มี validation errors
            messages.error(request, 'Please correct the errors below.')
        
        # กรณี validation ไม่ผ่าน หรือเกิด error ให้แสดง form อีกครั้ง
        context = {
            'form': form,
            'result_formset': result_formset,
            'loss_formset': loss_formset,
            'production_order': production_order,
            'production_process': production_process,
            'is_edit': production_process is not None,
        }
        
        return render(request, 'production/production-process/production-process-unified-form.html', context)
    
    def _handle_confirmation(self, request, production_process, production_order):
        """Handle production process confirmation"""
        
        try:
            # ตรวจสอบว่า production process มี results และ losses หรือไม่
            if not production_process.production_results.exists():
                messages.error(
                    request, 
                    'Cannot confirm production process without results. Please add at least one result product.'
                )
                return redirect('production:production-process-unified-edit', 
                              production_order_id=production_order.id, 
                              process_id=production_process.id)
            
            # ตรวจสอบ WIP balance
            validation_errors = self._validate_wip_balance_for_confirmation(production_process)
            if validation_errors:
                for error in validation_errors:
                    messages.error(request, error)
                return redirect('production:production-process-unified-edit', 
                              production_order_id=production_order.id, 
                              process_id=production_process.id)
            
            # Confirm the process
            production_process.confirm_process(request.user)
            
            messages.success(
                request, 
                f'Production process "{production_process.process_name}" confirmed successfully.'
            )
            
            # Redirect กลับไปยัง production order detail
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            else:
                return redirect('production:production-order-detail', production_order.id)
                
        except Exception as e:
            messages.error(request, f'Error confirming production process: {str(e)}')
            return redirect('production:production-process-unified-edit', 
                          production_order_id=production_order.id, 
                          process_id=production_process.id)

    def _validate_wip_balance_for_confirmation(self, production_process):
        """Validate WIP balance for process confirmation"""
        errors = []
        
        # ตรวจสอบการใช้วัตถุดิบตาม BOM
        from production.models.wip_stock_movement import WIPStockMovement
        from catalog.models.bom import BOM
        
        # รวมปริมาณการใช้วัตถุดิบทั้งหมด
        material_usage = {}
        
        # จาก Results (ผลผลิต) -> ต้องใช้วัตถุดิบตาม BOM
        for result in production_process.production_results.all():
            # หา BOM ของ product นี้
            bom_items = BOM.objects.filter(parent_sku=result.item)
            for bom_item in bom_items:
                required_qty = bom_item.quantity * result.quantity
                material_sku = bom_item.component_sku
                
                if material_sku in material_usage:
                    material_usage[material_sku] += required_qty
                else:
                    material_usage[material_sku] = required_qty
        
        # จาก Losses (การสูญเสีย) -> วัตถุดิบที่สูญเสียไป
        for loss in production_process.production_losses.all():
            if loss.item in material_usage:
                material_usage[loss.item] += loss.quantity
            else:
                material_usage[loss.item] = loss.quantity
        
        # ตรวจสอบ balance
        for material_sku, required_qty in material_usage.items():
            current_balance = WIPStockMovement.get_wip_balance(
                production_process.production_order, 
                material_sku
            )
            
            if required_qty > current_balance:
                errors.append(
                    f'Insufficient WIP balance for {material_sku.sku_code}. '
                    f'Required: {required_qty}, Available: {current_balance}'
                )
        
        return errors
