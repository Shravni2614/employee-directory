
import csv
from io import StringIO

from django.test import TestCase
from django.urls import reverse

from .models import Employee


class EmployeeCSVExportTests(TestCase):

    def setUp(self):
        Employee.objects.create(
            employee_id='EMP001',
            name='Aarav Sharma',
            department='IT',
            email='aarav@example.com',
            salary='45000.00',
        )

        Employee.objects.create(
            employee_id='EMP002',
            name='Priya Patel',
            department='HR',
            email='priya@example.com',
            salary='50000.00',
        )

    def test_csv_download_response(self):
        response = self.client.get(
            reverse('export_employees_csv')
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'text/csv',
        )
        self.assertIn(
            'attachment;',
            response['Content-Disposition'],
        )

    def test_csv_contains_headers_and_employee_data(self):
        response = self.client.get(
            reverse('export_employees_csv')
        )

        content = response.content.decode('utf-8')
        rows = list(csv.reader(StringIO(content)))

        self.assertEqual(
            rows[0],
            ['Employee ID', 'Name', 'Department', 'Email', 'Salary'],
        )
        self.assertIn(
            ['EMP001', 'Aarav Sharma', 'IT',
             'aarav@example.com', '45000.00'],
            rows,
        )
        self.assertIn(
            ['EMP002', 'Priya Patel', 'HR',
             'priya@example.com', '50000.00'],
            rows,
        )

    def test_search_filter_is_applied(self):
        response = self.client.get(
            reverse('export_employees_csv'),
            {'search': 'Aarav'},
        )

        content = response.content.decode('utf-8')

        self.assertIn('Aarav Sharma', content)
        self.assertNotIn('Priya Patel', content)

    def test_department_filter_is_applied(self):
        response = self.client.get(
            reverse('export_employees_csv'),
            {'department': 'HR'},
        )

        content = response.content.decode('utf-8')

        self.assertIn('Priya Patel', content)
        self.assertNotIn('Aarav Sharma', content)

    
    def test_formula_injection_is_mitigated(self):
        Employee.objects.create(
            employee_id='EMP003',
            name='=1+1',
            department='IT',
            email='formula@example.com',
            salary='30000.00',
        )

        response = self.client.get(
            reverse('export_employees_csv')
        )

        rows = list(
            csv.reader(
                StringIO(response.content.decode('utf-8'))
            )
        )

        exported_names = [row[1] for row in rows[1:]]

        self.assertIn("'=1+1", exported_names)
        self.assertNotIn('=1+1', exported_names)


class EmployeeDeletionTests(TestCase):

    def setUp(self):
        self.employee = Employee.objects.create(
            employee_id='DEL001',
            name='Test Employee',
            department='IT',
            email='testemployee@example.com',
            salary='40000.00',
        )

    def test_get_request_does_not_delete_employee(self):
        response = self.client.get(
            reverse('delete_employee', args=[self.employee.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Employee.objects.filter(id=self.employee.id).exists()
        )

    def test_post_request_deletes_employee(self):
        response = self.client.post(
            reverse('delete_employee', args=[self.employee.id])
        )

        self.assertRedirects(
            response,
            reverse('employee_list'),
        )
        self.assertFalse(
            Employee.objects.filter(id=self.employee.id).exists()
        )

    def test_nonexistent_employee_returns_404(self):
        response = self.client.get(
            reverse('delete_employee', args=[99999])
        )

        self.assertEqual(response.status_code, 404)


class EmployeeEditingTests(TestCase):

    def setUp(self):
        self.employee = Employee.objects.create(
            employee_id='EDIT001',
            name='Original Employee',
            department='IT',
            email='original@example.com',
            salary='40000.00',
        )

    def test_edit_page_loads(self):
        response = self.client.get(
            reverse('edit_employee', args=[self.employee.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Original Employee')

    def test_post_updates_employee(self):
        response = self.client.post(
            reverse('edit_employee', args=[self.employee.id]),
            {
                'employee_id': 'EDIT001',
                'name': 'Updated Employee',
                'department': 'HR',
                'email': 'updated@example.com',
                'salary': '50000.00',
            },
        )

        self.assertRedirects(
            response,
            reverse('employee_list'),
        )

        self.employee.refresh_from_db()
        self.assertEqual(self.employee.name, 'Updated Employee')
        self.assertEqual(self.employee.department, 'HR')
        self.assertEqual(str(self.employee.salary), '50000.00')

    def test_nonexistent_employee_returns_404(self):
        response = self.client.get(
            reverse('edit_employee', args=[99999])
        )

        self.assertEqual(response.status_code, 404)

    
    def test_invalid_post_does_not_update_employee(self):
        response = self.client.post(
            reverse('edit_employee', args=[self.employee.id]),
            {
                'employee_id': 'EDIT001',
                'name': 'Updated Employee',
                'department': 'HR',
                'email': 'not-a-valid-email',
                'salary': '50000.00',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)

        self.employee.refresh_from_db()
        self.assertEqual(
            self.employee.name,
            'Original Employee',
        )
        self.assertEqual(
            self.employee.email,
            'original@example.com',
        )


class EmployeeCreationTests(TestCase):

    def test_add_employee_page_loads(self):
        response = self.client.get(reverse('add_employee'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Add Employee')

    def test_valid_post_creates_employee(self):
        response = self.client.post(
            reverse('add_employee'),
            {
                'employee_id': 'NEW001',
                'name': 'New Employee',
                'department': 'IT',
                'email': 'newemployee@example.com',
                'salary': '35000.00',
            },
        )

        self.assertRedirects(
            response,
            reverse('employee_list'),
        )
        self.assertTrue(
            Employee.objects.filter(
                employee_id='NEW001',
                name='New Employee',
            ).exists()
        )

    def test_invalid_post_does_not_create_employee(self):
        response = self.client.post(
            reverse('add_employee'),
            {
                'employee_id': 'NEW002',
                'name': 'New Employee',
                'department': 'IT',
                'email': 'invalid-email',
                'salary': '35000.00',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        self.assertFalse(
            Employee.objects.filter(
                employee_id='NEW002',
            ).exists()
        )



class EmployeeDirectoryTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        for i in range(1, 8):
            Employee.objects.create(
                employee_id=f'DIR{i:03d}',
                name=f'Employee {i}',
                department='IT' if i <= 4 else 'HR',
                email=f'employee{i}@example.com',
                salary=f'{30000 + i * 1000}.00',
            )

    def test_directory_page_loads(self):
        response = self.client.get(reverse('employee_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Employee Directory')

    def test_search_filters_by_name(self):
        response = self.client.get(
            reverse('employee_list'),
            {'search': 'Employee 1'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Employee 1')
        self.assertNotContains(response, 'Employee 2')

    def test_department_filter(self):
        response = self.client.get(
            reverse('employee_list'),
            {'department': 'HR'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Employee 5')
        self.assertNotContains(response, 'Employee 1')

    def test_sorting_by_name_descending(self):
        response = self.client.get(
            reverse('employee_list'),
            {'sort': 'name', 'order': 'desc'},
        )

        self.assertEqual(response.status_code, 200)
        employees = list(response.context['employees'])
        self.assertEqual(employees[0].name, 'Employee 7')

    
    def test_pagination_shows_seven_employees_per_page(self):
        response = self.client.get(reverse('employee_list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['employees']), 7)
        self.assertEqual(response.context['page_obj'].paginator.count, 7)

    
    def test_out_of_range_page_returns_last_valid_page(self):
        response = self.client.get(
            reverse('employee_list'),
            {'page': 2},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['page_obj'].number, 1)
        self.assertEqual(len(response.context['employees']), 7)

    
    def test_pagination_splits_employees_across_pages(self):
        Employee.objects.create(
            employee_id='DIR008',
            name='Employee 8',
            department='HR',
            email='employee8@example.com',
            salary='38000.00',
        )

        first_page = self.client.get(
            reverse('employee_list')
        )
        second_page = self.client.get(
            reverse('employee_list'),
            {'page': 2},
        )

        self.assertEqual(len(first_page.context['employees']), 7)
        self.assertEqual(len(second_page.context['employees']), 1)
        self.assertEqual(first_page.context['page_obj'].number, 1)
        self.assertEqual(second_page.context['page_obj'].number, 2)

