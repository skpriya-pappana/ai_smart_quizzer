from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib import messages
from django.db import IntegrityError
from .models import Topic, Subtopic, Profile, MCQQuestion, Result, UserAnswer
from django.db.models import Avg
from .utils import extract_mcqs_from_pdf
import random
import uuid
from django.utils import timezone
from django.http import JsonResponse
import json
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from datetime import datetime, timedelta
from django.db.models import Count, Avg

def home(request):
    return render(request,'home.html')
# --- Registration View ---
def register(request):
    if request.method == "POST":
        firstname = request.POST.get("first_name")
        lastname = request.POST.get("last_name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        retype_password = request.POST.get("retype_password")
        contact = request.POST.get("contact")
        gender = request.POST.get("gender")

        if password != retype_password:
            return render(request, 'register.html', {
                'error': 'Passwords do not match.',
                'values': request.POST
            })

        if User.objects.filter(username=email).exists():
            return render(request, 'register.html', {
                'error': 'Email already registered.',
                'values': request.POST
            })

        if User.objects.filter(username=email).exists():
            return render(request, 'register.html', {
                'error': 'Email already registered.',
                'values': request.POST
            })

        try:
            # ✅ Create user
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=firstname,
                last_name=lastname
            )

            # ✅ Create Profile
            Profile.objects.create(
                user=user,
                contact_no=contact,
                gender=gender
            )

            messages.success(request, "Registration successful! Please login.")
            return redirect('login')   

        except IntegrityError:
            messages.error(request, "Email or Contact number already exists.")
            return redirect('register')

    return render(request, "register.html")
# --- Login View ---
def login_view(request):
    if request.method == "POST":
        email = request.POST.get("username")  # form field is "username", really email
        password = request.POST.get("password")

        # Find user by email
        user_obj = User.objects.filter(email=email).first()
        if not user_obj:
            messages.error(request, 'No account found with this email.')
            return render(request, 'login.html', {'email': email})

        # Authenticate
        user = authenticate(request, username=user_obj.username, password=password)

        if user:
            auth_login(request, user)
            if user.is_superuser:
                return redirect('admin_dashboard')
            return redirect('user_dashboard')

        messages.error(request, 'Invalid email or password.')

    return render(request, 'login.html')
# ------------------ USER DASHBOARD ------------------
@login_required
def user_dashboard(request):
    if request.user.is_superuser:
        return redirect('admin_dashboard')
    topics = Topic.objects.all()
    return render(request, 'user_dashboard.html', {'topics': topics})

def get_suggestion(user):
    suggestion = None

    # Easy → Medium
    easy_results = Result.objects.filter(user=user, difficulty="easy")
    if easy_results.count() >= 5:
        avg_easy = sum(r.score for r in easy_results) / easy_results.count()
        if avg_easy >= 80:
            suggestion = "You are doing great in Easy level! Try Medium level quizzes."

    # Medium → Hard
    medium_results = Result.objects.filter(user=user, difficulty="medium")
    if medium_results.count() >= 5:
        avg_medium = sum(r.score for r in medium_results) / medium_results.count()
        if avg_medium >= 80:
            suggestion = "You are doing great in Medium level! Try Hard level quizzes."

    return suggestion

def get_subtopics_view(request):
    topic_id = request.GET.get('topic_id')
    subtopics = list(Subtopic.objects.filter(topic_id=topic_id).values('id', 'name')) if topic_id else []
    return JsonResponse(subtopics, safe=False)
# ------------------ ADMIN DASHBOARD ------------------
@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('user_dashboard')

    if request.method == "POST":
        topic_name = request.POST.get("topic_name")
        subtopic_name = request.POST.get("subtopic_name")
        difficulty = request.POST.get("difficulty")
        pdf_file = request.FILES.get("file-upload")

        if not pdf_file:
            messages.error(request, "Please upload a PDF file.")
            return redirect('admin_dashboard')

        topic_obj, _ = Topic.objects.get_or_create(name=topic_name)
        subtopic_obj, _ = Subtopic.objects.get_or_create(name=subtopic_name, topic=topic_obj)

        try:
            mcqs = extract_mcqs_from_pdf(pdf_file)
            new_questions_count = 0
            duplicate_questions_count = 0

            for mcq in mcqs:
                # Use get_or_create to prevent duplicates
                obj, created = MCQQuestion.objects.get_or_create(
                    topic=topic_obj,
                    subtopic=subtopic_obj,
                    question=mcq["question"].strip(),
                    # 'defaults' are only used if a new object is created
                    defaults={
                        'difficulty': difficulty,
                        'question_no': mcq["question_no"],
                        'option1': mcq["option1"], 
                        'option2': mcq["option2"],
                        'option3': mcq["option3"], 
                        'option4': mcq["option4"],
                        'correct_answer': mcq["correct_answer"],
                    }
                )
                if created:
                    new_questions_count += 1
                else:
                    duplicate_questions_count += 1
            
            # Provide a helpful summary message to the admin
            success_message = f"Upload complete! Created {new_questions_count} new questions."
            if duplicate_questions_count > 0:
                success_message += f" Found and skipped {duplicate_questions_count} duplicates."
            messages.success(request, success_message)

        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
        
        return redirect('admin_dashboard')
        
    return render(request, 'admin_dashboard.html')

# ------------------ ADMIN LOGIN ------------------
def admin_login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        # Look for admin (superuser only)
        user_obj = User.objects.filter(email=email, is_superuser=True).first()
        if not user_obj:
            # ✅ CORRECTED TEMPLATE PATH
            return render(request, "admin_login.html", {
                "error": "No admin account found with this email",
                "email": email
            })

        # Authenticate
        user = authenticate(request, username=user_obj.username, password=password)

        if user and user.is_superuser:
            auth_login(request, user)
            return redirect('admin_dashboard')

        # ✅ CORRECTED TEMPLATE PATH
        return render(request, "admin_login.html", {
            "error": "Invalid admin credentials",
            "email": email
        })

    # ✅ CORRECTED TEMPLATE PATH
    return render(request, "admin_login.html")

@login_required
def admin_manage(request):
    if not request.user.is_superuser:
        return redirect('user_dashboard')
    
    # Handle quiz deletion
    if request.method == "POST" and 'delete_quizzes' in request.POST:
        topic_id = request.POST.get('delete_topic')
        subtopic_id = request.POST.get('delete_subtopic')
        difficulty = request.POST.get('delete_difficulty')
        
        # Build filter conditions
        filters = {}
        if topic_id:
            filters['topic_id'] = topic_id
        if subtopic_id:
            filters['subtopic_id'] = subtopic_id
        if difficulty:
            filters['difficulty'] = difficulty
            
        if filters:
            deleted_count = MCQQuestion.objects.filter(**filters).count()
            MCQQuestion.objects.filter(**filters).delete()
            messages.success(request, f"Successfully deleted {deleted_count} quiz questions.")
        else:
            messages.error(request, "Please select at least one filter criteria.")
        
        return redirect('admin_manage')
    
    # Get statistics
    total_quizzes = MCQQuestion.objects.count()
    total_topics = Topic.objects.count()
    total_users = User.objects.filter(is_superuser=False).count()
    
    # Get all users with their profiles (exclude superusers)
    # Handle users without profiles gracefully
    users_with_profiles = []
    for user in User.objects.filter(is_superuser=False):
        try:
            profile = user.profile
            users_with_profiles.append(user)
        except Profile.DoesNotExist:
        # CORRECTED: Create profile with contact_no=None
            Profile.objects.create(user=user, contact_no=None, gender='M')
            users_with_profiles.append(user)

    
    # Get topics and subtopics for delete functionality
    topics = Topic.objects.all()
    subtopics = Subtopic.objects.all()
    
    # Get recent quiz results for overview
    recent_results = Result.objects.select_related('user').order_by('-date_attempted')[:10]
    
    context = {
        'total_quizzes': total_quizzes,
        'total_topics': total_topics,
        'total_users': total_users,
        'users_with_profiles': users_with_profiles,
        'topics': topics,
        'subtopics': subtopics,
        'recent_results': recent_results,
    }
    
    return render(request, 'admin_manage.html', context)

# ------------------ LOGOUT ------------------
def logout_view(request):
    logout(request)   # ✅ Logs out both user & admin
    return redirect('home')   # ✅ Redirects everyone to home page


# ---------------- Helper Function ----------------
def generate_suggestions(user):
    """
    Generate difficulty suggestions based on user's quiz history.
    Returns a list of suggestion strings.
    """
    results = Result.objects.filter(user=user)
    history = (
        results.values("topic", "subtopic", "difficulty")
        .annotate(
            quizzes_taken=Count("id"),
            avg_score=Avg("score")
        )
        .order_by("topic", "subtopic", "difficulty")
    )

    suggestions = []

    for h in history:
        if h['difficulty'] == 'easy' and h['quizzes_taken'] >= 5 and h['avg_score'] >= 80:
            suggestions.append(f"Try Medium in {h['topic']} → {h['subtopic']} as you are doing great in easy level")
        elif h['difficulty'] == 'medium' and h['quizzes_taken'] >= 5 and h['avg_score'] >= 75:
            suggestions.append(f"Try Hard in {h['topic']} → {h['subtopic']} as you are doing great in medium level")
        elif h['difficulty'] == 'hard' and h['quizzes_taken'] >= 3 and h['avg_score'] >= 80:
            suggestions.append(f"You can move to next topic, you have already performed well in hard levels of {h['topic']} → {h['subtopic']}")

    return suggestions

@login_required
def start_quiz(request):
    if request.method == "POST":
        topic_id = request.POST.get("topic")
        subtopic_id = request.POST.get("subtopic")
        difficulty = request.POST.get("difficulty")
        num_questions = int(request.POST.get("num_questions", 5))

        questions_qs = MCQQuestion.objects.filter(
            topic_id=topic_id, subtopic_id=subtopic_id, difficulty=difficulty
        )
        question_ids = list(questions_qs.values_list('id', flat=True))

        if not question_ids:
            messages.error(request, "No questions found for the selected criteria.")
            return redirect("user_dashboard")

        if len(question_ids) > num_questions:
            question_ids = random.sample(question_ids, num_questions)

        request.session['quiz_questions'] = question_ids
        request.session['quiz_answers'] = {}
        request.session['quiz_params'] = {
            'topic_id': topic_id,
            'subtopic_id': subtopic_id,
            'difficulty': difficulty,
        }
        if request.POST.get("proceed") == "true":
            return redirect("take_quiz", question_number=1)

        # ✅ Generate AI-based suggestions
        suggestions = generate_suggestions(request.user)
        topic_name = Topic.objects.get(id=topic_id).name 
        subtopic_name = Subtopic.objects.get(id=subtopic_id).name

        # ✅ Block only if:
        # (1) Suggestion applies to the SAME topic/subtopic
        # (2) Suggestion recommends a different difficulty
        if suggestions:
            for s in suggestions:
                if topic_name in s and subtopic_name in s:  # match topic/subtopic context
                    if "Medium" in s and difficulty.lower() == "easy":
                        return render(request, "suggestion_modal.html", {
                            "suggestion": s,
                            "topic_id": topic_id,
                            "subtopic_id": subtopic_id,
                            "difficulty": difficulty,
                            "num_questions": num_questions,
                        })
                    elif "Hard" in s and difficulty.lower() == "medium":
                        return render(request, "suggestion_modal.html", {
                            "suggestion": s,
                            "topic_id": topic_id,
                            "subtopic_id": subtopic_id,
                            "difficulty": difficulty,
                            "num_questions": num_questions,
                        })
                    elif "next topic" in s.lower() and difficulty.lower() == "hard":
                        return render(request, "suggestion_modal.html", {
                            "suggestion": s,
                            "topic_id": topic_id,
                            "subtopic_id": subtopic_id,
                            "difficulty": difficulty,
                            "num_questions": num_questions,
                        })

        # ✅ Proceed normally if no suggestion applies
        return redirect("take_quiz", question_number=1)

    return redirect("user_dashboard")


# ---------------- My Stats View ----------------
@login_required
def my_stats(request):
    # All quiz results for the user
    results = Result.objects.filter(user=request.user).order_by('-date_attempted')

    # Summary stats
    total_quizzes = results.count()
    average_score = results.aggregate(Avg('score'))['score__avg'] or 0
    average_score = round(average_score, 2)
    passed_quizzes = results.filter(score__gte=50).count()
    failed_quizzes = results.filter(score__lt=50).count()

    # Suggestions (from history data)
    history = (
        results.values("topic", "subtopic", "difficulty")
        .annotate(
            quizzes_taken=Count("id"),
            avg_score=Avg("score")
        )
        .order_by("topic", "subtopic", "difficulty")
    )

    suggestion = None
    for h in history:
        # Easy → Medium
        if (
            h["difficulty"] == "easy"
            and h["quizzes_taken"] >= 5
            and h["avg_score"] >= 80
            and not results.filter(topic=h["topic"], subtopic=h["subtopic"], difficulty="medium").exists()
        ):
            suggestion = f"You’ve mastered Easy in {h['topic']} → {h['subtopic']}. Try Medium next!"

        # Medium → Hard
        elif (
            h["difficulty"] == "medium"
            and h["quizzes_taken"] >= 5
            and h["avg_score"] >= 75
            and not results.filter(topic=h["topic"], subtopic=h["subtopic"], difficulty="hard").exists()
        ):
            suggestion = f"Nice work! You’re ready for Hard in {h['topic']} → {h['subtopic']}."

        # Hard → Next topic
        elif (
            h["difficulty"] == "hard"
            and h["quizzes_taken"] >= 3
            and h["avg_score"] >= 80
        ):
            suggestion = f"Awesome! You’re strong in {h['topic']} → {h['subtopic']}. Move to the next topic."

    # If request is AJAX (fetching review for a quiz attempt)
    quiz_code = request.GET.get("quiz_code")
    if quiz_code:
        user_answers = list(
            UserAnswer.objects.filter(user=request.user, quiz_code=quiz_code).values(
                'question__question', 'selected_option', 'correct_answer',
                'question__option1', 'question__option2',
                'question__option3', 'question__option4',
            )
        )
        return JsonResponse(user_answers, safe=False)

    context = {
        "results": results,
        "total_quizzes": total_quizzes,
        "average_score": average_score,
        "passed_quizzes": passed_quizzes,
        "failed_quizzes": failed_quizzes,
        "suggestion": suggestion,   # <-- Only shows if next difficulty not yet tried
    }
    return render(request, "my_stats.html", context)

@login_required
def take_quiz_view(request, question_number):
    question_ids = request.session.get('quiz_questions')
    if not question_ids:
        messages.error(request, "Quiz session not found. Please start a new quiz.")
        return redirect('user_dashboard')

    total_questions = len(question_ids)
    
    if request.method == "POST":
        current_question_id = question_ids[question_number - 1]
        answer = request.POST.get(f"q{current_question_id}")
        answers = request.session.get('quiz_answers', {})
        if answer:
            answers[str(current_question_id)] = answer
            request.session['quiz_answers'] = answers
        
        if 'next' in request.POST:
            next_page = question_number + 1
            if next_page > total_questions:
                return redirect('submit_quiz')
            return redirect('take_quiz', question_number=next_page)
        
        elif 'previous' in request.POST:
            prev_page = question_number - 1
            if prev_page > 0:
                return redirect('take_quiz', question_number=prev_page)

    if not (1 <= question_number <= total_questions):
        return redirect('take_quiz', question_number=1)

    question_id = question_ids[question_number - 1]
    question = get_object_or_404(MCQQuestion, id=question_id)

    context = {
        'question': question,
        'question_number': question_number,
        'total_questions': total_questions,
        'previous_answer': request.session.get('quiz_answers', {}).get(str(question_id))
    }
    return render(request, "take_quiz.html", context)


@login_required
def submit_quiz(request):
    question_ids = request.session.get('quiz_questions')
    user_answers = request.session.get('quiz_answers')
    quiz_params = request.session.get('quiz_params')

    if not all([question_ids, user_answers, quiz_params]):
        messages.error(request, "Your quiz session has expired. Please start again.")
        return redirect("user_dashboard")

    # Generate one quiz_code for this attempt
    quiz_code = str(uuid.uuid4())[:8]

    questions = MCQQuestion.objects.filter(id__in=question_ids)
    correct = 0

    for q in questions:
        user_answer = user_answers.get(str(q.id))
        if user_answer and user_answer.strip().upper() == q.correct_answer.strip().upper():
            correct += 1

        # Save per-question answer
        UserAnswer.objects.create(
            user=request.user,
            question=q,
            selected_option=user_answer or "",
            correct_answer=q.correct_answer,
            quiz_code=quiz_code
        )

    total = len(question_ids)
    wrong = total - correct
    score = (correct / total) * 100 if total > 0 else 0

    topic = Topic.objects.get(id=quiz_params['topic_id'])
    subtopic = Subtopic.objects.get(id=quiz_params['subtopic_id'])

    Result.objects.create(
        user=request.user,
        quiz_code=quiz_code,
        topic=topic.name,
        subtopic=subtopic.name,
        difficulty=quiz_params['difficulty'],
        total_questions=total,
        correct=correct,
        wrong=wrong,
        score=score
    )

    # Clear session
    for key in ['quiz_questions', 'quiz_answers', 'quiz_params']:
        if key in request.session:
            del request.session[key]

    context = {
        "quiz_code": quiz_code,
        "topic": topic.name,
        "subtopic": subtopic.name,
        "difficulty": quiz_params['difficulty'],
        "total": total,
        "correct": correct,
        "wrong": wrong,
        "score": round(score, 2)
    }
    return render(request, "results_display.html", context)



def results_display(request):
    
    return render(request, "results_display.html")

def help_support(request):
    
    return render(request, "help_support.html")

@login_required
def settings_view(request):
    if request.method == "POST":
        user = request.user
        profile = user.profile  # OneToOne relation

        # Update User table fields
        user.first_name = request.POST.get("first_name", user.first_name)
        user.last_name = request.POST.get("last_name", user.last_name)
        user.email = request.POST.get("email", user.email)

        # Update Profile table fields
        profile.contact_no = request.POST.get("contact", profile.contact_no)
        profile.gender = request.POST.get("gender", profile.gender)

        # Save both
        user.save()
        profile.save()

        messages.success(request, "Your settings have been updated successfully!")
        return redirect("user_dashboard")

    return render(request, "settings.html")


@login_required
def history(request):
    results = Result.objects.filter(user=request.user)

    history = (
        results.values("topic", "subtopic", "difficulty")
        .annotate(
            quizzes_taken=Count("id"),
            avg_score=Avg("score")
        )
        .order_by("topic", "subtopic", "difficulty")
    )

    context = {
        "history": history,
    }
    return render(request, "history.html", context)

def get_subtopics_view(request):
    topic_id = request.GET.get('topic_id')
    if topic_id:
        subtopics = Subtopic.objects.filter(topic_id=topic_id).values('id', 'name')
        return JsonResponse(list(subtopics), safe=False)
    return JsonResponse([], safe=False)

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, 'No user found with that email address.')
            return redirect('forgot_password')

        # Generate OTP
        otp = get_random_string(length=6, allowed_chars='0123456789')
        
        # Store OTP and expiry in session
        request.session['reset_otp'] = otp
        request.session['reset_otp_user_id'] = user.id
        # Set OTP expiry to 5 minutes from now
        request.session['reset_otp_expiry'] = (datetime.now() + timedelta(minutes=5)).isoformat()
        
        # Send email with OTP
        send_mail(
            'Your Password Reset OTP',
            f'Your OTP to reset your password is: {otp}\nIt will expire in 5 minutes.',
            'from-email@yourdomain.com', # Should match EMAIL_HOST_USER in settings.py
            [email],
            fail_silently=False,
        )
        
        messages.success(request, 'An OTP has been sent to your email.')
        return redirect('reset_password')
        
    return render(request, 'forgot_password.html')


def reset_password(request):
    if request.method == 'POST':
        otp_entered = request.POST.get('otp')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        # Retrieve OTP data from session
        otp_saved = request.session.get('reset_otp')
        user_id = request.session.get('reset_otp_user_id')
        otp_expiry_str = request.session.get('reset_otp_expiry')

        if not all([otp_saved, user_id, otp_expiry_str]):
            messages.error(request, 'Your password reset session has expired. Please try again.')
            return redirect('forgot_password')
        
        # Check if OTP has expired
        if datetime.now() > datetime.fromisoformat(otp_expiry_str):
            messages.error(request, 'The OTP has expired. Please request a new one.')
            return redirect('forgot_password')

        if otp_entered != otp_saved:
            messages.error(request, 'Invalid OTP. Please try again.')
            return redirect('reset_password')

        if new_password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('reset_password')

        try:
            user = User.objects.get(id=user_id)
            user.set_password(new_password) # Correctly hashes the password
            user.save()
            
            # Clear session data
            del request.session['reset_otp']
            del request.session['reset_otp_user_id']
            del request.session['reset_otp_expiry']

            messages.success(request, 'Your password has been reset successfully. Please log in.')
            return redirect('login')
        except User.DoesNotExist:
            messages.error(request, 'An unexpected error occurred. Please try again.')
            return redirect('forgot_password')
            
    return render(request, 'reset_password.html')

# Add this new function to your views.py file

# In your views.py file
# Make sure you have this import at the top: import json

@login_required
def admin_users_view(request):
    if not request.user.is_superuser:
        return redirect('user_dashboard')

    users_list = User.objects.filter(is_superuser=False).select_related('profile').prefetch_related('result_set')
    
    # --- THIS IS THE CRITICAL PART THAT CALCULATES THE STATS ---
    # It loops through each user to calculate their stats before rendering the page.
    for user in users_list:
        user.total_quizzes = user.result_set.count()
        user.average_score = user.result_set.aggregate(avg_score=Avg('score'))['avg_score'] or 0
        
        # This part prepares the data for the pop-up modal
        results_data = list(user.result_set.all().order_by('-date_attempted')[:10].values(
            'topic', 'subtopic', 'score', 'date_attempted'
        ))
        for item in results_data:
            item['date_attempted'] = item['date_attempted'].strftime('%b %d, %Y')

        # This prepares all data for the modal's javascript
        user.json_data = {
            'fullname': f"{user.first_name} {user.last_name}",
            'email': user.email,
            'contact': user.profile.contact_no or 'N/A',
            'gender': user.profile.get_gender_display(),
            'joined': user.date_joined.strftime('%b %d, %Y'),
            'total_quizzes': user.total_quizzes,
            'average_score': user.average_score,
            'results': results_data
        }
    # --- END OF CRITICAL PART ---

    # We need to build the full JSON object for the template script
    users_data_for_js = {user.id: user.json_data for user in users_list}

    context = {
        'users_list': users_list,
        'users_data_json': json.dumps(users_data_for_js)
    }
    return render(request, 'admin_users.html', context)