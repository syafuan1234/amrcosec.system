from django import forms
from .models import Director

class DirectorForm(forms.ModelForm):
    class Meta:
        model = Director
        fields = '__all__'
        widgets = {
            'appointment_date': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'},
                format='%d-%m-%Y'
            ),
            'resignation_date': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'},
                format='%d-%m-%Y'
            ),
        }
        input_formats = ['%d-%m-%Y']

import datetime

class DirectorForm(forms.ModelForm):
    appointment_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        input_formats=['%d-%m-%Y']
    )
    resignation_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        input_formats=['%d-%m-%Y']
    )

    class Meta:
        model = Director
        fields = '__all__'
