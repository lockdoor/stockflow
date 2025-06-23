from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def dashboard_view(request):
    user = request.user
    # ตรวจสอบกลุ่มผู้ใช้
    # if user.groups.filter(name='Warehouse').exists():
    #     return render(request, 'dashboard/warehouse.html')
    # elif user.groups.filter(name='Production').exists():
    #     return render(request, 'dashboard/production.html')
    # elif user.is_superuser:
    #     return render(request, 'dashboard/admin.html')
    # else:
    #     return render(request, 'dashboard/general.html')


    if user.is_superuser:
        return render(request, 'dashboard/admin.html')
    else:
        return render(request, 'dashboard/general.html')
