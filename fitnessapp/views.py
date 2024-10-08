from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.backends import ModelBackend


import requests
from django.conf import settings
import google.generativeai as genai






@login_required
def get_diet(request):
    form_data = request.session.get('diet_form_data', {})
    diet_plan = generate_diet_plan(
        form_data.get('diet_type'),
        calculate_maintenance_calories(
            int(form_data.get('age', 0)),
            form_data.get('gender', ''),
            float(form_data.get('weight', 0)),
            float(form_data.get('height', 0)),
            form_data.get('exercise_level', ''),
            form_data.get('goal', '')
        ),
        int(form_data.get('age', 0)),
        form_data.get('gender', ''),
        float(form_data.get('weight', 0)),
        float(form_data.get('height', 0)),
        calculate_bmi(float(form_data.get('weight', 0)), float(form_data.get('height', 0))),
        form_data.get('exercise_level', '')
    )
    context = {
        'show_results': True,
        'diet_plan': diet_plan,
        'bmi': calculate_bmi(float(form_data.get('weight', 0)), float(form_data.get('height', 0))),
        'maintenance_calories': calculate_maintenance_calories(
            int(form_data.get('age', 0)),
            form_data.get('gender', ''),
            float(form_data.get('weight', 0)),
            float(form_data.get('height', 0)),
            form_data.get('exercise_level', ''),
            form_data.get('goal', '')
        )
    }
    return render(request, 'fitnessapp/diet.html', context)


def payment_failed(request):
    return render(request, 'fitnessapp/payment_failed.html')



def login_or_register(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            # User exists, log them in
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, "Successfully logged in.")
            return redirect('dashboard')
        else:
            # User doesn't exist, try to create a new one
            if User.objects.filter(email=email).exists():
                # Email exists but password is wrong
                messages.error(request, "Invalid email or password.")
            else:
                # Create new user
                user = User.objects.create_user(username=email, email=email, password=password)
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, "Account created and logged in successfully.")
                return redirect('dashboard')
    
    return render(request, 'fitnessapp/login_or_register.html')

@login_required
def dashboard(request):
    return render(request, 'fitnessapp/dashboard.html')





def logout_view(request):
    logout(request)
    return redirect('home')


def home(request):
    return render(request, 'fitnessapp/login.html')

@login_required
def update_user(request):
    if request.method == 'POST':
        new_username = request.POST['username']
        if new_username != request.user.username:
            if User.objects.filter(username=new_username).exists():
                messages.error(request, 'This username is already taken.')
            else:
                request.user.username = new_username
                request.user.save()
                messages.success(request, 'Your username has been updated successfully.')
                return redirect('home')
    return render(request, 'fitnessapp/update_user.html')



def diet(request):
    return render(request, 'fitnessapp/diet.html')





def calculate_bmi(weight, height):
    height_in_meters = height / 100
    bmi = weight / (height_in_meters ** 2)
    return round(bmi, 2)

def calculate_maintenance_calories(age, gender, weight, height, exercise_level, goal):
    if gender == 'male':
        bmr = 66 + (6.2 * weight) + (12.7 * height) - (6.8 * age)
    else:
        bmr = 655 + (4.35 * weight) + (4.7 * height) - (4.7 * age)
    
    activity_multipliers = {
        'sedentary': 1.2,
        'lightly_active': 1.375,
        'moderately_active': 1.55,
        'very_active': 1.725,
        'extremely_active': 1.9
    }
    
    goal_adjustments = {
        'build_muscle': 1.1,
        'weight_loss': 0.9,
        'maintain': 1
    }
    
    maintenance_calories = bmr * activity_multipliers[exercise_level] * goal_adjustments[goal]
    return round(maintenance_calories, 2)



def generate_diet_plan(diet_type, maintenance_calories, age, gender, weight, height, bmi, exercise_level):
    genai.configure(api_key=settings.GEMINI_API_KEY)

    prompt = f"""Generate a personalized Indian {diet_type} diet plan for a {age}-year-old {gender} with the following details:
    - Weight: {weight} kg
    - Height: {height} cm
    - BMI: {bmi}
    - Activity level: {exercise_level}
    - Daily calorie intake: {maintenance_calories} calories

    dont use astrix(*) anywhere in the answer

    Please provide a diet plan with 4 meals a day (breakfast, lunch, snack, and dinner) that meets the total daily calorie requirement of {maintenance_calories} calories. Include specific Indian dishes and portion sizes.

    Format the output as follows:
    Indian {diet_type} Diet Plan for a {age}-Year-Old {gender}
    Breakfast:
    • Item 1 (calories)
    • Item 2 (calories)
    Lunch:
    • Item 1 (calories)
    • Item 2 (calories)
    Snack:
    • Item 1 (calories)
    • Item 2 (calories)
    Dinner:
    • Item 1 (calories)
    • Item 2 (calories)
    
    IMP:

    • Point 1
    • Point 2
    • Point 3
    • Point 4
    • Point 5

    Use round bullet points (•) and make headings bold..dont use astrix."""

    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt)
    
    if response.text:
        return response.text
    else:
        return "Failed to generate diet plan. Please try again later."





@login_required
def diet_tracker(request):
    if request.method == 'POST':
        # Store form data in session
        request.session['diet_form_data'] = request.POST.dict()
        # Redirect to payment
        return redirect('get_diet')
    return render(request, 'fitnessapp/diet.html')


@login_required
def get_diet(request):
    if request.method == 'POST':
        # Handle Razorpay payment verification
        payment_id = request.POST.get('razorpay_payment_id', '')
        order_id = request.POST.get('razorpay_order_id', '')
        signature = request.POST.get('razorpay_signature', '')
        params_dict = {
            'razorpay_payment_id': payment_id,
            'razorpay_order_id': order_id,
            'razorpay_signature': signature
        }
        try:
            client.utility.verify_payment_signature(params_dict)
            # Payment successful, generate diet plan
            form_data = request.session.get('diet_form_data', {})
            diet_plan = generate_diet_plan(
                form_data.get('diet_type'),
                calculate_maintenance_calories(
                    int(form_data.get('age', 0)),
                    form_data.get('gender', ''),
                    float(form_data.get('weight', 0)),
                    float(form_data.get('height', 0)),
                    form_data.get('exercise_level', ''),
                    form_data.get('goal', '')
                ),
                int(form_data.get('age', 0)),
                form_data.get('gender', ''),
                float(form_data.get('weight', 0)),
                float(form_data.get('height', 0)),
                calculate_bmi(float(form_data.get('weight', 0)), float(form_data.get('height', 0))),
                form_data.get('exercise_level', '')
            )
            context = {
                'show_results': True,
                'diet_plan': diet_plan,
                'bmi': calculate_bmi(float(form_data.get('weight', 0)), float(form_data.get('height', 0))),
                'maintenance_calories': calculate_maintenance_calories(
                    int(form_data.get('age', 0)),
                    form_data.get('gender', ''),
                    float(form_data.get('weight', 0)),
                    float(form_data.get('height', 0)),
                    form_data.get('exercise_level', ''),
                    form_data.get('goal', '')
                )
            }
            return render(request, 'fitnessapp/diet.html', context)
        except:
            # Payment failed, redirect to payment failed page
            return redirect('payment_failed')
    else:
        # Create Razorpay order
        amount = 1000  # Amount in paise (10 INR)
        order = client.order.create({'amount': amount, 'currency': 'INR', 'payment_capture': '1'})
        return render(request, 'fitnessapp/payment.html', {'order': order})




def aboutus(request):
    return render(request, 'fitnessapp/aboutus.html')

def contact(request):
    return render(request, 'fitnessapp/contact.html')

def pricing(request):
    return render(request, 'fitnessapp/pricing.html')

def privacy(request):
    return render(request, 'fitnessapp/privacy.html')

def termsandconditions(request):
    return render(request, 'fitnessapp/termsandconditions.html')

def cancelandrefund(request):
    return render(request, 'fitnessapp/cancelandrefund.html')


@login_required
def process_diet_request(request):
    if request.method == 'POST':
        # Process the diet request without Razorpay
        form_data = request.session.get('diet_form_data', {})
        diet_plan = generate_diet_plan(
            form_data.get('diet_type'),
            calculate_maintenance_calories(
                int(form_data.get('age', 0)),
                form_data.get('gender', ''),
                float(form_data.get('weight', 0)),
                float(form_data.get('height', 0)),
                form_data.get('exercise_level', ''),
                form_data.get('goal', '')
            ),
            int(form_data.get('age', 0)),
            form_data.get('gender', ''),
            float(form_data.get('weight', 0)),
            float(form_data.get('height', 0)),
            calculate_bmi(float(form_data.get('weight', 0)), float(form_data.get('height', 0))),
            form_data.get('exercise_level', '')
        )
        context = {
            'show_results': True,
            'diet_plan': diet_plan,
            'bmi': calculate_bmi(float(form_data.get('weight', 0)), float(form_data.get('height', 0))),
            'maintenance_calories': calculate_maintenance_calories(
                int(form_data.get('age', 0)),
                form_data.get('gender', ''),
                float(form_data.get('weight', 0)),
                float(form_data.get('height', 0)),
                form_data.get('exercise_level', ''),
                form_data.get('goal', '')
            )
        }
        return render(request, 'fitnessapp/diet.html', context)
    else:
        # If it's a GET request, just show the payment page without Razorpay
        return render(request, 'fitnessapp/payment.html')