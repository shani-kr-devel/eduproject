from django.contrib import admin

from .models import Feedback, Homework, StudentGroup, Test, TestAnswer, TestAttempt, TestQuestion, TestScore

admin.site.register(Homework)
admin.site.register(Test)
admin.site.register(TestQuestion)
admin.site.register(StudentGroup)
admin.site.register(TestAttempt)
admin.site.register(TestAnswer)
admin.site.register(TestScore)
admin.site.register(Feedback)
