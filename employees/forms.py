
from django import forms
from .models import Employee


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            'employee_id',
            'name',
            'department',
            'email',
            'salary',
        ]

        widgets = {
            'employee_id': forms.TextInput(attrs={
                'placeholder': 'e.g. EMP001',
                'required': True,
            }),
            'name': forms.TextInput(attrs={
                'placeholder': 'Enter full name',
                'required': True,
                'autocomplete': 'name',
            }),
            'department': forms.TextInput(attrs={
                'placeholder': 'e.g. Information Technology',
                'required': True,
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'name@example.com',
                'required': True,
                'autocomplete': 'email',
            }),
            'salary': forms.NumberInput(attrs={
                'placeholder': 'Enter salary',
                'min': '0.01',
                'step': '0.01',
                'required': True,
            }),
        }

    def clean_employee_id(self):
        employee_id = self.cleaned_data['employee_id'].strip()

        if not employee_id:
            raise forms.ValidationError(
                'Employee ID cannot be empty.'
            )

        return employee_id

    def clean_name(self):
        name = self.cleaned_data['name'].strip()

        if not name:
            raise forms.ValidationError(
                'Employee name cannot be empty.'
            )

        if not any(character.isalpha() for character in name):
            raise forms.ValidationError(
                'Enter a valid employee name.'
            )

        return name

    def clean_department(self):
        department = self.cleaned_data['department'].strip()

        if not department:
            raise forms.ValidationError(
                'Department cannot be empty.'
            )

        return department

    def clean_salary(self):
        salary = self.cleaned_data['salary']

        if salary <= 0:
            raise forms.ValidationError(
                'Salary must be greater than zero.'
            )

        return salary
