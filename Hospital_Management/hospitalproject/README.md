# Hospital Online Booking System

A Django-based web application for online hospital appointment booking, doctor management, and patient services.

## Features

- Doctor registration, editing, and management (admin CRUD)
- Patient appointment booking with dynamic slot selection
- Online consultation scheduling
- Consultation fee management for doctors
- Platform fee and price breakdown in booking
- Payment integration with Razorpay
- User authentication and profiles
- Admin dashboard with sidepanel navigation
- Appointment slot management with calendar and time picker
- Email notifications
- Improved booking validation (slot required, total required)
- Responsive and modern UI

## Installation

1. Clone the repository:

   ```
   git clone <repository-url>
   cd hospitalproject
   ```

2. Create a virtual environment:

   ```
   python -m venv venv
   venv\Scripts\activate  # On Windows
   ```

3. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

4. Set up the database:
   - Ensure MySQL is installed and running
   - Update database settings in `hospitalproject/settings.py` if needed
   - Run migrations:
     ```
     python manage.py migrate
     ```

5. Create a superuser:

   ```
   python manage.py createsuperuser
   ```

6. Run the development server:

   ```
   python manage.py runserver
   ```

7. Access the application at `http://127.0.0.1:8000/`

## Configuration

- Update `RAZORPAY_ID` and `RAZORPAY_SECRET` in `settings.py` for payment functionality
- Configure email settings in `settings.py` for notifications
- Set `DEBUG = False` and configure `ALLOWED_HOSTS` for production

## Usage

- Register as a patient or doctor
- Browse available doctors and specialities
- Book appointments online
- Make payments through Razorpay
- View booking history in user dashboard
- Admin can manage doctors, appointments, and users

## Technologies Used

- Django
- MySQL
- Razorpay (payments)
- HTML/CSS/JavaScript
- Bootstrap (for styling)


