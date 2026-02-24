from django.urls import path
from hospitalproject import views

urlpatterns = [
    path('doctors/', views.admin_doctor_list, name='admin_doctor_list'),
    path('doctors/add/', views.admin_add_doctor, name='admin_add_doctor'),
    path('doctors/edit/<int:doctor_id>/', views.admin_edit_doctor, name='admin_edit_doctor'),
    path('doctors/delete/<int:doctor_id>/', views.admin_delete_doctor, name='admin_delete_doctor'),

    path('specialities/', views.admin_speciality_list, name='admin_speciality_list'),
    path('specialities/add/', views.admin_add_speciality, name='admin_add_speciality'),
    path('specialities/edit/<int:speciality_id>/', views.admin_edit_speciality, name='admin_edit_speciality'),
    path('specialities/delete/<int:speciality_id>/', views.admin_delete_speciality, name='admin_delete_speciality'),

    path('bookings/', views.admin_booking_list, name='admin_booking_list'),
    path('bookings/delete/<uuid:booking_uuid>/', views.admin_delete_booking, name='admin_delete_booking'),

    # Appointment Slot Management
    path('slots/', views.admin_slot_list, name='admin_slot_list'),
    path('slots/add/', views.admin_add_slot, name='admin_add_slot'),
    path('slots/edit/<int:slot_id>/', views.admin_edit_slot, name='admin_edit_slot'),
    path('slots/delete/<int:slot_id>/', views.admin_delete_slot, name='admin_delete_slot'),

    # Doctor Review Management
    path('reviews/', views.admin_review_list, name='admin_review_list'),
    path('reviews/delete/<int:review_id>/', views.admin_delete_review, name='admin_delete_review'),
]