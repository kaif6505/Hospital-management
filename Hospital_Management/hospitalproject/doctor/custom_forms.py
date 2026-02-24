from django import forms
from .models import Doctor, Speciality

class CustomDoctorForm(forms.ModelForm):
    consultation_fee = forms.DecimalField(
        label="Consultation Fee (₹)",
        max_digits=6,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter consultation fee'}),
        required=True
    )
    summary = forms.CharField(
        label="About Doctor",
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Short summary about the doctor'}),
        help_text="A brief summary about the doctor."
    )
    experience_details = forms.CharField(
        label="Experience Details",
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Describe experience, years, hospitals, etc.'}),
        help_text="Detailed experience, years, hospitals, etc."
    )
    class Meta:
        model = Doctor
        fields = [
            'name', 'image', 'experience', 'consultation_fee', 'clinic_name', 'address', 'location', 'speciality',
            'other_specialization_1', 'other_specialization_2', 'other_specialization_3', 'other_specialization_4',
            'contact_number', 'email', 'education_1', 'education_2', 'education_3', 'education_4',
        ]
