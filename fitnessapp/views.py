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

from groq import Groq
from django.conf import settings

# Configure Groq client
groq_client = Groq(api_key=settings.GROQ_API_KEY)

import random
from django.http import JsonResponse
import json


from .models import ChatMessage

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

    

    Please provide a diet plan with 4 meals a day (breakfast, lunch, snack, and dinner) that meets the total daily calorie requirement of {maintenance_calories} calories. Include specific Indian dishes and portion sizes.

    Format the output as follows:
    Indian {diet_type} Diet Plan for a {age}-Year-Old {gender}
    Breakfast:
    • Item 1 (calories) with quantity in grams or ml
    • Item 2 (calories) with quantity in grams or ml
    Lunch:
    • Item 1 (calories) with quantity in grams or ml
    • Item 2 (calories) with quantity in grams or ml
    Snack:
    • Item 1 (calories) with quantity in grams or ml
    • Item 2 (calories) with quantity in grams or ml
    Dinner:
    • Item 1 (calories) with quantity in grams or ml
    • Item 2 (calories) with quantity in grams or ml
    
    IMP:

    • Point 1
    • Point 2
    • Point 3
    • Point 4
    • Point 5

    Use round bullet points (•) and make headings bold. """

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
    


import json


def generate_quiz_questions():
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a fitness expert creating a beginner-friendly quiz."},
                {"role": "user", "content": """Generate 10 easy, beginner-level fitness-related multiple-choice questions with 4 options each. 
                The questions should cover basic fitness concepts, simple exercises, and general health knowledge.
                Make sure the questions are straightforward and the answers are clear.
                Format the response as a JSON array with the following structure for each question:
                {
                    "question": "The question text",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "correct_answer": 0  // Index of the correct answer (0-3)
                }
                """}
            ],
            model="llama3-70b-8192",
            max_tokens=1000,
            temperature=0.7,
        )

        content = chat_completion.choices[0].message.content
        questions = json.loads(content)
        return questions

    except Exception as e:
        print(f"An error occurred: {e}")
        return []

def fitness_quiz(request):
    if request.method == 'POST':
        # Handle quiz submission
        answers = request.POST
        questions = request.session.get('quiz_questions', [])
        score = calculate_score(answers, questions)
        category = categorize_score(score)
        return render(request, 'fitnessapp/quiz_results.html', {'score': score, 'category': category})
    else:
        # Generate quiz questions
        questions = generate_quiz_questions()
        if not questions:
            return render(request, 'fitnessapp/quiz_error.html', {'error_message': 'Failed to generate quiz questions. Please try again later.'})
        
        # Store questions in session for later use
        request.session['quiz_questions'] = questions
        
        return render(request, 'fitnessapp/quiz.html', {'questions': questions})

def calculate_score(answers, questions):
    score = 0
    for i, question in enumerate(questions, start=1):
        user_answer = answers.get(f'q{i}')
        if user_answer and int(user_answer) - 1 == question['correct_answer']:
            score += 1
    return score




def categorize_score(score):
    if score <= 3:
        return 'Beginner'
    elif score <= 6:
        return 'Intermediate'
    elif score <= 8:
        return 'Pro'
    else:
        return 'Elite'
    



@login_required
def chat_room(request):
    messages = ChatMessage.objects.all()
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            ChatMessage.objects.create(user=request.user, content=content)
        return redirect('chat_room')
    return render(request, 'fitnessapp/chat_room.html', {'messages': messages})

@login_required
def delete_message(request, message_id):
    message = ChatMessage.objects.get(id=message_id)
    if request.user == message.user:
        message.delete()
    return redirect('chat_room')
