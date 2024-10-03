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



def diet_tracker(request):
    context = {'show_results': False}
    if request.method == 'POST':
        # Extract form data
        age = int(request.POST.get('age', 0))
        gender = request.POST.get('gender', '')
        weight = float(request.POST.get('weight', 0))
        height = float(request.POST.get('height', 0))
        exercise_level = request.POST.get('exercise_level', '')
        goal = request.POST.get('goal', '')
        diet_type = request.POST.get('diet_type', '')
        
        # Perform calculations
        bmi = calculate_bmi(weight, height)
        maintenance_calories = calculate_maintenance_calories(age, gender, weight, height, exercise_level, goal)
        
        # Generate the diet plan
        diet_plan = generate_diet_plan(diet_type, maintenance_calories, age, gender, weight, height, bmi, exercise_level)
        
        context.update({
            'bmi': bmi,
            'maintenance_calories': maintenance_calories,
            'diet_plan': diet_plan,
            'show_results': True,
        })
    
    return render(request, 'fitnessapp/diet.html', context)

