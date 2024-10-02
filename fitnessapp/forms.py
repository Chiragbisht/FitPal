from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render




def login_view(request):
    form = AuthenticationForm(request, data=request.POST or None)
    if form.is_valid():
        # Authenticate the user and log them in
        # Redirect after login
        pass

    return render(request, 'fitnessapp/login.html', {'form': form})
