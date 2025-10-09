"""
URL configuration for sample project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from space import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("",views.home,name="home"),
    path("login/",views.login_view,name="login"),
    path("register/",views.register,name="register"),
    path("user_dashboard/",views.user_dashboard,name="user_dashboard"),
    path("admin_dashboard/",views.admin_dashboard,name="admin_dashboard"),
    path("admin_login/",views.admin_login,name="admin_login"),
    path("logout/", views.logout_view, name="logout"),
    path('results/', views.results_display, name='results_display'),
    path('my_stats/', views.my_stats, name='my_stats'),
    path('history/', views.history, name='history'),
    path('help_support/', views.help_support, name='help_support'),
    path('settings/', views.settings_view, name='settings'),

    path('ajax/get-subtopics/', views.get_subtopics_view, name='get_subtopics'),
    
    # --- EDITED QUIZ URLS ---
    # This URL now just sets up the quiz and redirects
    path("start_quiz/", views.start_quiz, name="start_quiz"),
    
    # This new URL displays a specific question (e.g., /quiz/question/1/)
    path('quiz/question/<int:question_number>/', views.take_quiz_view, name='take_quiz'),

    # This URL is now only for final submission and scoring
    path("submit_quiz/", views.submit_quiz, name="submit_quiz"),
    path('admin_dashboard/manage/', views.admin_manage, name='admin_manage'),
    path('admin_dashboard/users/', views.admin_users_view, name='admin_users'),

    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/', views.reset_password, name='reset_password'),
]
