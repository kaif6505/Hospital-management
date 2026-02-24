# --- Admin Appointment Slot Management ---
from doctor.models import AppointmentSlot, Review
from django import forms
from django.shortcuts import render, HttpResponseRedirect, redirect
from django.contrib.auth.forms import UserCreationForm

from django.contrib.auth import authenticate,login,logout
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required

from doctor.models import Doctor, AppointmentSlot, Booking
User = get_user_model()

from User.models import CustomUser
from django.db.models import Sum

from doctor.forms import SpecialityForm
from doctor.custom_forms import CustomDoctorForm
from doctor.forms import DoctorForm
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404

class AppointmentSlotForm(forms.ModelForm):
    class Meta:
        model = AppointmentSlot
        fields = ['doctor', 'date', 'time', 'is_booked']

@staff_member_required
def admin_slot_list(request):
    slots = AppointmentSlot.objects.select_related('doctor').all().order_by('-date', '-time')
    return render(request, 'admin_slot_list.html', {'slots': slots})

@staff_member_required
def admin_add_slot(request):
    if request.method == 'POST':
        form = AppointmentSlotForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_slot_list')
    else:
        form = AppointmentSlotForm()
    return render(request, 'admin_add_slot.html', {'form': form})

@staff_member_required
def admin_edit_slot(request, slot_id):
    slot = get_object_or_404(AppointmentSlot, id=slot_id)
    if request.method == 'POST':
        form = AppointmentSlotForm(request.POST, instance=slot)
        if form.is_valid():
            form.save()
            return redirect('admin_slot_list')
    else:
        form = AppointmentSlotForm(instance=slot)
    return render(request, 'admin_edit_slot.html', {'form': form})

@staff_member_required
def admin_delete_slot(request, slot_id):
    slot = get_object_or_404(AppointmentSlot, id=slot_id)
    if request.method == 'POST':
        slot.delete()
        return redirect('admin_slot_list')
    return render(request, 'admin_delete_slot.html', {'slot': slot})

# --- Admin Doctor Review Management ---
@staff_member_required
def admin_review_list(request):
    reviews = Review.objects.select_related('doctor', 'patient').all().order_by('-created_at')
    return render(request, 'admin_review_list.html', {'reviews': reviews})

@staff_member_required
def admin_delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    if request.method == 'POST':
        review.delete()
        return redirect('admin_review_list')
    return render(request, 'admin_delete_review.html', {'review': review})

def home(request):
    return render(request,'index.html')      

def doctor(request):
    return render(request , 'doctor.html')

def patient(request):
    return render (request , 'patient.html')

def contact(request):
    return render (request , 'contact.html')

def signin(request):
    return render (request, 'signin.html')

def health_plans(request):
    return render (request , 'health_plans.html')

def about(request):
    return render(request, 'about.html')

@csrf_exempt
def payment_success(request):
    data = request.session.get('booking_data')
    if not data:
        return redirect('doctors')  # or show error

    doctor = Doctor.objects.get(id=data['doctor_id'])
    slot = AppointmentSlot.objects.get(id=data['slot_id'])

    # Mark slot as booked
    slot.is_booked = True
    slot.save()

    # Create Booking
    Booking.objects.create(
        doctor=doctor,
        user=request.user,
        slot=slot
    )

    del request.session['booking_data']  # clean session
    return render(request, 'payment_success.html')



def register(request):
    if request.method == "GET":
        print("asdfghjk")
        return render(request, "signin.html")

    elif request.method == "POST":
        username = request.POST.get("username")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        passwordconfirmation = request.POST.get("confirm_password")

        if password != passwordconfirmation:
            message = "Passwords do not match"
            return render(request, "signin.html", {"message": message})

        if User.objects.filter(username=username).exists():
            return render(request, "signin.html", {"message": "Username already taken."})
        if User.objects.filter(email=email).exists():
            return render(request, "signin.html", {"message": "Email already registered."})

        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
            is_active=True
        )

        message = "Registration Successful. Please sign in."
        return redirect("login")

def user_login(request):
    if request.method == "GET":
        return render(request,"login.html")
    elif request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        print("Username:", username)
        print("Password:", password)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        print("User exists:", User.objects.filter(username=username).exists())
        user = authenticate(request, username=username, password=password)
        message = None
        if user is not None:
            login(request, user)
            return HttpResponseRedirect("/")
        message = "Login Failed"
        return render(request, "login.html", {"message": message})

def user_logout(request):
    logout(request)
    return HttpResponseRedirect("/login")


# Admin Dashboard View
from django.contrib.admin.views.decorators import staff_member_required
@staff_member_required
def admin_dashboard(request):
    total_doctors = Doctor.objects.count()
    total_patients = CustomUser.objects.filter(is_staff=False, is_superuser=False).count()
    total_appointments = Booking.objects.count()
    total_revenue = Booking.objects.aggregate(total=Sum('amount'))['total'] or 0

    recent_appointments = Booking.objects.select_related('user', 'doctor', 'slot').order_by('-booked_at')[:10]
    recent_appointments_data = []
    for appt in recent_appointments:
        recent_appointments_data.append({
            'patient': appt.user.get_full_name() or appt.user.username,
            'doctor': appt.doctor.name,
            'date': appt.slot.date,
            'status': appt.payment_status,
        })

    context = {
        'total_doctors': total_doctors,
        'total_patients': total_patients,
        'total_appointments': total_appointments,
        'total_revenue': total_revenue,
        'recent_appointments': recent_appointments_data,
    }
    return render(request, 'admin_dashboard.html', context)


# --- Admin Doctor Management ---
@staff_member_required
def admin_doctor_list(request):
    doctors = Doctor.objects.all()
    return render(request, 'admin_doctor_list.html', {'doctors': doctors})

@staff_member_required
def admin_add_doctor(request):
    if request.method == 'POST':
        form = CustomDoctorForm(request.POST, request.FILES)
        if form.is_valid():
            doctor = form.save(commit=False)
            # Save extra fields to model (if you add them to Doctor model)
            doctor.save()
            # Save specializations, summary, experience_details as needed
            # (You may want to add these fields to the Doctor model)
            return redirect('admin_doctor_list')
    else:
        form = CustomDoctorForm()
    return render(request, 'admin_add_doctor.html', {'form': form})

@staff_member_required
def admin_edit_doctor(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    if request.method == 'POST':
        form = CustomDoctorForm(request.POST, request.FILES, instance=doctor)
        if form.is_valid():
            form.save()
            return redirect('admin_doctor_list')
    else:
        form = CustomDoctorForm(instance=doctor)
    return render(request, 'admin_edit_doctor.html', {'form': form})

@staff_member_required
def admin_delete_doctor(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    if request.method == 'POST':
        doctor.delete()
        return redirect('admin_doctor_list')
    return render(request, 'admin_delete_doctor.html', {'doctor': doctor})

# --- Admin Speciality Management ---
@staff_member_required
def admin_speciality_list(request):
    from doctor.models import Speciality
    specialities = Speciality.objects.all()
    return render(request, 'admin_speciality_list.html', {'specialities': specialities})

@staff_member_required
def admin_add_speciality(request):
    if request.method == 'POST':
        form = SpecialityForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_speciality_list')
    else:
        form = SpecialityForm()
    return render(request, 'admin_add_speciality.html', {'form': form})

@staff_member_required
def admin_edit_speciality(request, speciality_id):
    from doctor.models import Speciality
    speciality = get_object_or_404(Speciality, id=speciality_id)
    if request.method == 'POST':
        form = SpecialityForm(request.POST, instance=speciality)
        if form.is_valid():
            form.save()
            return redirect('admin_speciality_list')
    else:
        form = SpecialityForm(instance=speciality)
    return render(request, 'admin_edit_speciality.html', {'form': form})

@staff_member_required
def admin_delete_speciality(request, speciality_id):
    from doctor.models import Speciality
    speciality = get_object_or_404(Speciality, id=speciality_id)
    if request.method == 'POST':
        speciality.delete()
        return redirect('admin_speciality_list')
    return render(request, 'admin_delete_speciality.html', {'speciality': speciality})

# --- Admin Booking Management ---
@staff_member_required
def admin_booking_list(request):
    bookings = Booking.objects.select_related('user', 'doctor', 'slot').all()
    return render(request, 'admin_booking_list.html', {'bookings': bookings})

@staff_member_required
def admin_delete_booking(request, booking_uuid):
    booking = get_object_or_404(Booking, booking_uuid=booking_uuid)
    if request.method == 'POST':
        booking.delete()
        return redirect('admin_booking_list')
    return render(request, 'admin_delete_booking.html', {'booking': booking})