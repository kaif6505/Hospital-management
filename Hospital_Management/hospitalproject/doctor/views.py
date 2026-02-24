from django.shortcuts import render, get_object_or_404,redirect
from .models import Doctor,Speciality
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.shortcuts import render, redirect
from datetime import datetime, timedelta, time ,date
from .models import Doctor,Booking,AppointmentSlot
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .forms import SlotBookingForm, BookingForm
import calendar
from collections import defaultdict
import razorpay
from django.conf import settings
from hospitalproject.settings import RAZORPAY_ID,RAZORPAY_SECRET
from django.core.mail import send_mail,EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseRedirect
from django.urls import reverse
from .forms import ReviewForm
from .models import  Review
from django.contrib import messages


# Create your views here.
def doctors(request):
    query = request.GET.get('q')  # Get the search term
    if query:
        doctors = Doctor.objects.filter(name__icontains=query)  # Case-insensitive match
    else:
        doctors = Doctor.objects.all()
    return render(request, 'doctors.html', {'doctors': doctors})



class DoctorDetailView(DetailView):
    model = Doctor
    template_name = 'doctor_detail.html'
    context_object_name = 'doctor'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doctor = self.object

        context['appointments'] = Booking.objects.filter(
            doctor=doctor
        ).order_by('slot__date', 'slot__time')

        context['availability_data'] = get_available_slots(doctor, days_ahead=5)

        reviews = doctor.reviews_received.all()
        context['reviews'] = reviews

        review_form = ReviewForm()
        context['review_form'] = review_form

        user_already_reviewed = False
        if self.request.user.is_authenticated:
            user_already_reviewed = Review.objects.filter(
                patient=self.request.user, doctor=doctor
            ).exists()
        context['user_already_reviewed'] = user_already_reviewed

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        doctor = self.object

        if not request.user.is_authenticated:
            messages.error(request, "You must be logged in to submit a review.")
            return redirect('login')

        user_already_reviewed = Review.objects.filter(
            patient=request.user, doctor=doctor
        ).exists()

        if user_already_reviewed:
            messages.warning(request, "You have already submitted a review for this doctor.")
            return redirect(self.get_success_url())

        review_form = ReviewForm(request.POST)
        if review_form.is_valid():
            review = review_form.save(commit=False)
            review.patient = request.user
            review.doctor = doctor
            review.save()
            messages.success(request, "Your review has been submitted successfully!")
            return redirect(self.get_success_url())
        else:
            messages.error(request, "There was an error with your review submission. Please check your input.")
            context = self.get_context_data(object=self.object)
            context['review_form'] = review_form
            return self.render_to_response(context)

    def get_success_url(self):
        return reverse('doctor_detail', kwargs={'slug': self.object.slug}) + '#reviews'





class SpecialityDetailView(DetailView):
    model=Speciality
    template_name="speciality.html"
    context_object_name="speciality"
    slug_field="slug"
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs) :
        context = super().get_context_data(**kwargs)
        context["doctors"]=Doctor.objects.all()
       
        return context
    
def doctors_by_speciality(request, speciality_slug):
    speciality = get_object_or_404(Speciality, slug__iexact=speciality_slug)
    doctors = Doctor.objects.filter(speciality=speciality)
    print(doctors,"***********************")
    return render(request, 'doctors_by_speciality.html', {
        'doctors': doctors,
        'speciality': speciality.name
    })

import uuid
from .models import AppointmentSlot
import razorpay
from .models import Payment

@login_required
def book_slot(request, slug,slot_id):
    if request.method == "POST":
        if slot_id ==0:
            messages.error(request,"Pls Select Slot First")
            return redirect('doctor_detail',slug = slug) 
        doctor = get_object_or_404(Doctor, slug=slug)
        slot =  get_object_or_404(AppointmentSlot,id=slot_id)
        total = float(request.POST.get("total"))
        print(total)
        if slot.is_booked and not (request.POST.get('is_pending_payment')):
            return redirect(f'/doctor/{slug}/')
        else:
            # Allow booking if no booking exists with 'Completed' status
            # 1. Check if the slot is already booked with a Completed payment
            existing_completed_booking = Booking.objects.filter(
                slot=slot,
                payment_status='Completed'
            ).first()

            if existing_completed_booking:
                messages.error(request, "This slot has already been booked.")
                return redirect('some_page')  # Replace with actual view name

            # 2. Reuse or create booking where status is NOT 'Completed'
            book, created = Booking.objects.get_or_create(
                slot=slot,
                defaults={
                    'booking_uuid': uuid.uuid4(),
                    'doctor': doctor,
                    'amount': total,
                    'user' : request.user,
                    'payment_status': 'Processing'
                }
            )

            # Optional: update doctor or amount if reused
            if not created:
                book.doctor = doctor
                book.user = request.user
                book.amount = total
                book.payment_status = 'Processing'  # Reset to processing
                book.save()


            # slot.is_booked = True
            slot.save()
            client = razorpay.Client(auth=(settings.RAZORPAY_ID, settings.RAZORPAY_SECRET))

            data = { "amount": int(total)*100, "currency": "INR", "receipt": str(book.booking_uuid) }
            payment = client.order.create(data=data)
            context ={
                "data":data,
                "payment":payment,
                "book":book,
                "RAZORPAY_KEY_ID":settings.RAZORPAY_ID
            } 
            my_payment,create = Payment.objects.get_or_create(
                booking = book,
                defaults={
                    'user': request.user,
                    'razorpay_order_id': payment.get('id'),
                    'amount' : total,
                    'status':"PENDING",
                    'method': "RAZORPAY",
                }
            )
            my_payment.razorpay_order_id = payment.get('id')
            my_payment.amount =  total
            my_payment.user = request.user
            my_payment.save()
            book.save()

            return render(request,'book_slot.html',context)
            # return redirect('doctor')
    else:
        return redirect(f'/doctor/{slug}/')

from django.utils import timezone
@login_required
def my_bookings(request):
    user_bookings = Booking.objects.filter(user=request.user).order_by('slot__date', 'slot__time')

    upcoming_bookings = []
    previous_bookings = []

    current_datetime = timezone.now()

    for booking in user_bookings:
        # Assuming slot.date is a DateField and slot.time is a TimeField
        # Combine date and time to create a datetime object for comparison
        slot_datetime = timezone.make_aware(
            timezone.datetime.combine(booking.slot.date, booking.slot.time)
        )

        if slot_datetime >= current_datetime:
            upcoming_bookings.append(booking)
        else:
            previous_bookings.append(booking)

    context = {
        'upcoming_bookings': upcoming_bookings,
        'previous_bookings': previous_bookings,
    }
    
    return render(request, 'my_bookings.html', context)

@login_required
def cancel_booking(request, booking_uuid):
    booking = get_object_or_404(Booking, booking_uuid=booking_uuid, user=request.user)

    if booking.cancelled:
        return redirect('my-bookings')

    booking.cancelled = True
    booking.slot.is_booked = False
    booking.slot.save()
    booking.save()

    # Send cancellation email
    send_mail(
        subject='Your Appointment Has Been Cancelled',
        
        message=f'''
Hi {request.user.first_name},

Your appointment with Dr. {booking.doctor.name} on {booking.slot.date} at {booking.slot.time} has been successfully cancelled.
Your Refund will be processed soon

If this was a mistake, please log in to rebook another slot.

Thank you,
Curacare Team
''',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[request.user.email],
        fail_silently=False,
    )

    return redirect('my-bookings')

    

@csrf_exempt
def payment_success(request):
    if request.method == "POST":
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_signature = request.POST.get('razorpay_signature')

        try:
            payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
            payment.razorpay_payment_id = razorpay_payment_id
            payment.status = "SUCCESS"
            payment.save()

            booking = payment.booking
            booking.payment_status = "SUCCESS"
            booking.user = request.user
            booking.cancelled = False
            booking.save()
            slot = booking.slot
            slot.is_booked = True
            slot.save()
            
            subject = 'Appointment Confirmation - Curacare'
            

            html_message = render_to_string('email_confirmation.html', {
                'user': request.user,
                'doctor': booking.doctor,
                'slot': booking.slot,
                'booking': booking,
            })
            plain_message = strip_tags(html_message)
            print("Sending email to:", request.user.email)
            send_mail(
                subject,
                "Booking Done",
                settings.EMAIL_HOST_USER,
                [request.user.email],
                html_message=html_message,
                fail_silently=False,
            )
            email = EmailMultiAlternatives(
                subject,
                "Your appointment has been confirmed ",
                settings.EMAIL_HOST_USER,
                [request.user.email],
            )
            email.attach_alternative(html_message,'text/html')
            email.send()
            print("Bye")
            return render(request, 'payment_success.html', {'booking': booking})

        except Payment.DoesNotExist:
            return render(request, 'payment_failed.html', {
                'message': "Payment record not found."
            })

    return render(request, 'payment_failed.html', {
        'message': "Invalid request method."
    })


def get_available_slots(doctor, days_ahead=5):
    """
    Returns grouped available slots for a doctor over the next `days_ahead` days.
    """
    today = date.today()
    end_date = today + timedelta(days=days_ahead)

    # Fetch unbooked slots
    slots = AppointmentSlot.objects.filter(
        doctor=doctor,
        date__range=(today, end_date),
        is_booked=False
    ).order_by('date', 'time')

    # Group by date
    grouped_slots = defaultdict(list)
    for slot in slots:
        grouped_slots[slot.date].append(slot)

    # Format for template
    availability_data = []
    for slot_date, slot_list in grouped_slots.items():
        availability_data.append({
            'date': slot_date,
            'day': calendar.day_name[slot_date.weekday()],
            'slots': slot_list,
            'slot_count': len(slot_list)
        })
    print(f""" 
    "slots" : {slots}

    "grouped_slots" :{grouped_slots}

    "availability_data" :{availability_data}

    """)
    return availability_data


  


def doctor_availability(request, slug):
    doctor = get_object_or_404(Doctor, slug=slug)
    today = date.today()
    days = [today + timedelta(days=i) for i in range(5)]  # Today to Friday

    date_slots = []
    for d in days:
        slots = DoctorAvailability.objects.filter(doctor=doctor, date=d, is_booked=False)
        date_slots.append({
        'date': d,
        'label': 'Today' if d == today else d.strftime('%A')[:3],  # Today, Mon, Tue...
        'slot_count': slots.count(),
        'slots': slots,
        })

    return render(request, 'doctor/availability.html', {
        'doctor': doctor,
        'date_slots': date_slots,
    })

from django.db.models import Q


def search_doctors(request):
    # pull the two parameters; default to empty string so we can strip safely
    speciality_query = request.GET.get('speciality', '').strip()
    location_query = request.GET.get('location', '').strip()

    # start with all doctors and narrow down
    doctors = Doctor.objects.all()

    if speciality_query:
        # allow users to type either the display name or the slug (cards use slug links)
        doctors = doctors.filter(
            Q(speciality__name__icontains=speciality_query) |
            Q(speciality__slug__icontains=speciality_query)
        )

    if location_query:
        doctors = doctors.filter(location__icontains=location_query)

    return render(request, 'search_results.html', {
        'doctors': doctors,
        'speciality_query': speciality_query,
        'location_query': location_query,
    })


def doctor_schedule_view(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    availability = DoctorAvailability.objects.filter(doctor=doctor)

    availability_data = {}
    for slot in availability:
        time_str = slot.time.strftime("%H:%M")
        availability_data.setdefault(slot.day, []).append(time_str)

    return render(request, 'doctor_schedule.html', {
        'doctor': doctor,
        'availability_data': availability_data,
    })

def get_slots_for_day(request):
    doctor_id = request.GET.get('doctor_id')
    day = request.GET.get('day')

    doctor = get_object_or_404(Doctor, id=doctor_id)
    slots = DoctorAvailability.objects.filter(doctor=doctor, day=day).order_by('time')
    slot_times = [slot.time.strftime("%H:%M") for slot in slots]

    return JsonResponse({'slots': slot_times})


@login_required
def book_appointment(request, slot_id):      #checkout page   create razorpay order here inside this view
    slot = get_object_or_404(AppointmentSlot, id=slot_id, is_booked=False)

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.doctor = slot.doctor
            booking.user = request.user
            booking.slot = slot
            print(book_slot)
            booking.save()
            slot.is_booked = True
            slot.save()
            return redirect('/')  # Make a success page
    else:
        form = BookingForm(initial={'slot': slot})

    return render(request, 'book_appointment.html', {
        'form': form,
        'slot': slot,
        'doctor': slot.doctor
    })



from django.shortcuts import render
from django.http import JsonResponse
from groq import Groq

# Replace with your Groq API key
client = Groq(api_key="myapi")


def chatbot_page(request):
    return render(request, "doctor/chatbot.html")

from django.views.decorators.csrf import csrf_exempt


@csrf_exempt

def chatbot_api(request):
    if request.method == "POST":
        user_message = request.POST.get("message")

        try:
            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )

            reply = completion.choices[0].message.content

        except Exception as e:
            reply = "Error: " + str(e)

        return JsonResponse({"reply": reply})