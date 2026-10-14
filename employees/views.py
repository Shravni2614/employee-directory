
from django.shortcuts import render, redirect, get_object_or_404
from .models import Employee
from .forms import EmployeeForm
from django.core.paginator import Paginator
import csv
from django.http import HttpResponse

def employee_list(request):
    employees = Employee.objects.all()

    search_query = request.GET.get('search', '')
    department = request.GET.get('department', '')

    if search_query:
        employees = employees.filter(name__icontains=search_query)

    if department:
        employees = employees.filter(department=department)

    # Sorting logic
    sort_by = request.GET.get('sort', 'name')
    order = request.GET.get('order', 'asc')

    allowed_fields = ['employee_id', 'name', 'department', 'salary']

    if sort_by not in allowed_fields:
        sort_by = 'name'

    if order == 'desc':
        sort_by = '-' + sort_by

    employees = employees.order_by(sort_by)

    # Count employees after search and department filtering
    total_employees = employees.count()

    departments = Employee.objects.values_list(
        'department', flat=True
    ).distinct()

    # Pagination logic
    paginator = Paginator(employees, 7)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'index.html', {
        'employees': page_obj,
        'page_obj': page_obj,
        'departments': departments,
        'search_query': search_query,
        'selected_department': department,
        'sort': request.GET.get('sort', 'name'),
        'order': order,
        'total_employees': total_employees,
    })


def safe_csv_value(value):
    value = str(value)

    # Prevent spreadsheet formula injection
    if value.lstrip().startswith(('=', '+', '-', '@', '\t', '\r')):
        return "'" + value

    return value


def export_employees_csv(request):
    employees = Employee.objects.all()

    search_query = request.GET.get('search', '')
    department = request.GET.get('department', '')

    if search_query:
        employees = employees.filter(name__icontains=search_query)

    if department:
        employees = employees.filter(department=department)

    response = HttpResponse(
        content_type='text/csv',
    )
    response['Content-Disposition'] = (
        'attachment; filename="employees.csv"'
    )

    writer = csv.writer(response)
    writer.writerow([
        'Employee ID',
        'Name',
        'Department',
        'Email',
        'Salary',
    ])

    for employee in employees:
        writer.writerow([
            safe_csv_value(employee.employee_id),
            safe_csv_value(employee.name),
            safe_csv_value(employee.department),
            safe_csv_value(employee.email),
            employee.salary,
        ])

    return response


def add_employee(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('employee_list')
    else:
        form = EmployeeForm()

    return render(request, 'add_employee.html', {'form': form})

def edit_employee(request, id):
    employee = get_object_or_404(Employee, id=id)

    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)

        if form.is_valid():
            form.save()
            return redirect('employee_list')
    else:
        form = EmployeeForm(instance=employee)

    return render(request, 'edit_employee.html', {
        'form': form,
        'employee': employee
    })


from django.shortcuts import render, redirect, get_object_or_404
from .models import Employee


def delete_employee(request, id):
    employee = get_object_or_404(Employee, id=id)

    if request.method == 'POST':
        employee.delete()
        return redirect('employee_list')

    return render(request, 'delete_employee.html', {
        'employee': employee
    })
