from django.db import models
from django.contrib.auth.models import User

# --- NEW MODELS FOR TOPIC AND SUBTOPIC ---
# This creates a dedicated table for all unique topics.
class Topic(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


# This creates a dedicated table for subtopics and links each one to a topic.
class Subtopic(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE) # The relationship
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    

# --- UPDATED MCQQuestion MODEL ---
# Now it links to the Topic and Subtopic models instead of using text fields.
class MCQQuestion(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    subtopic = models.ForeignKey(Subtopic, on_delete=models.CASCADE)
    difficulty = models.CharField(
        max_length=20,
        choices=[("Easy", "Easy"), ("Medium", "Medium"), ("Hard", "Hard")]
    )
    question_no = models.IntegerField()
    question = models.TextField()
    option1 = models.CharField(max_length=500)
    option2 = models.CharField(max_length=500)
    option3 = models.CharField(max_length=500)
    option4 = models.CharField(max_length=500)
    correct_answer = models.CharField(max_length=500)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.topic.name} - {self.subtopic.name} Q{self.question_no}"
    
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # link to Django User
    contact_no = models.CharField(max_length=15, unique=True)   # no duplicates
    gender = models.CharField(
        max_length=10,
        choices=[("M", "Male"), ("F", "Female"), ("O", "Other")],
        blank=False,
        null=False
    )
    created_at = models.DateTimeField(auto_now_add=True)   # set when created
    updated_at = models.DateTimeField(auto_now=True)       # update on save

    def __str__(self):
        return self.user.username


class Result(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    topic = models.CharField(max_length=100)
    subtopic = models.CharField(max_length=100)
    difficulty = models.CharField(max_length=20)
    date_attempted = models.DateTimeField(auto_now_add=True)
    total_questions = models.IntegerField()
    correct = models.IntegerField()
    wrong = models.IntegerField()
    score = models.FloatField()
    quiz_code = models.CharField(max_length=20) 

    def __str__(self):
        return f"{self.user.username} - {self.topic} ({self.score})"
    
class UserAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(MCQQuestion, on_delete=models.CASCADE)
    selected_option = models.CharField(max_length=500)
    correct_answer = models.CharField(max_length=500)
    date_attempted = models.DateTimeField(auto_now_add=True)
    
    # NEW FIELD to identify quiz attempt
    quiz_code = models.CharField(max_length=100, blank=True, null=True)

    def is_correct(self):
        return self.selected_option.strip().upper() == self.correct_answer.strip().upper()

    def __str__(self):
        return f"{self.user.username} - Q{self.question.question_no}"
    



''' from django.db import models

# Create your models here.
from django.db import models
from django.core.validators import RegexValidator, MinLengthValidator

class Sample(models.Model):
    firstname = models.CharField(
        max_length=50,
        blank=False,
        null=False
    )
    lastname = models.CharField(
        max_length=50,
        blank=False,
        null=False
    )
    email = models.EmailField(
        max_length=100,
        unique=True,   
        blank=False,
        null=False
    )
    password = models.CharField(
        max_length=128,   
        validators=[
            RegexValidator(
                regex=r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@#$%^&+=!]{8,}$',
                message="Password must be at least 8 characters long, alphanumeric, and may include special characters."
            )
        ],
        blank=False,
        null=False
    )
    contact_no = models.CharField(
        max_length=15,
        validators=[
            RegexValidator(
                regex=r'^\+?\d{10,15}$',
                message="Enter a valid contact number (10–15 digits, optional + prefix)."
            )
        ],
        unique=True,  
        blank=False,
        null=False
    )
    gender = models.CharField(
        max_length=10,
        choices=[("M", "Male"), ("F", "Female"), ("O", "Other")],
        blank=False,
        null=False
    )
    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.firstname} {self.lastname} - {self.email}" '''

