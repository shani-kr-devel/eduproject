import datetime

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import ParentProfile, Role, StudentProfile, TeacherProfile, User
from apps.academics.models import Feedback, Test, TestScore
from apps.courses.models import Course, Enrollment, Order, Payment


class Command(BaseCommand):
    help = "Seed the database with demo users (one per role) and sample data."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Seeding demo data...")

        admin, _ = User.objects.get_or_create(
            email="admin@edumanage.test",
            defaults=dict(first_name="Ada", last_name="Admin", role=Role.ADMIN, is_staff=True, is_superuser=True),
        )
        admin.set_password("Admin@12345")
        admin.save()

        teacher_user, _ = User.objects.get_or_create(
            email="teacher@edumanage.test",
            defaults=dict(first_name="Tara", last_name="Teacher", role=Role.TEACHER),
        )
        teacher_user.set_password("Teacher@12345")
        teacher_user.save()
        teacher_profile, _ = TeacherProfile.objects.get_or_create(
            user=teacher_user, defaults={"subject_specialization": "Mathematics"}
        )

        student_user, _ = User.objects.get_or_create(
            email="student@edumanage.test",
            defaults=dict(first_name="Sam", last_name="Student", role=Role.STUDENT),
        )
        student_user.set_password("Student@12345")
        student_user.save()
        student_profile, _ = StudentProfile.objects.get_or_create(
            user=student_user,
            defaults={
                "grade_level": "Grade 8",
                # Pre-authorizes the parent seeded below to link to this
                # student by email, the way an admin would when enrolling a
                # student whose parent hasn't created an account yet.
                "guardian_email": "parent@edumanage.test",
            },
        )
        student_profile.guardian_email = "parent@edumanage.test"
        student_profile.save()
        student_profile.teachers.add(teacher_profile)

        parent_user, _ = User.objects.get_or_create(
            email="parent@edumanage.test",
            defaults=dict(first_name="Priya", last_name="Parent", role=Role.PARENT),
        )
        parent_user.set_password("Parent@12345")
        parent_user.save()
        parent_profile, _ = ParentProfile.objects.get_or_create(user=parent_user)
        parent_profile.children.add(student_profile)
        # Also demonstrates the direct-account authorization path (as
        # opposed to guardian_email) for admins who create the parent
        # account first.
        student_profile.authorized_parent = parent_profile
        student_profile.save(update_fields=["authorized_parent"])

        # A second student, deliberately NOT authorized for any parent yet,
        # to demonstrate the rejection path: searching by Student ID works,
        # but POSTing to /parent/link-child/ for this one will correctly
        # fail with "not authorized" until an admin sets guardian_email or
        # authorized_parent via /accounts/students/<id>/set_guardian/.
        unlinked_user, _ = User.objects.get_or_create(
            email="unlinked.student@edumanage.test",
            defaults=dict(first_name="Uma", last_name="Unlinked", role=Role.STUDENT),
        )
        unlinked_user.set_password("Student@12345")
        unlinked_user.save()
        unlinked_student, _ = StudentProfile.objects.get_or_create(
            user=unlinked_user, defaults={"grade_level": "Grade 6"}
        )

        test, _ = Test.objects.get_or_create(
            teacher=teacher_profile,
            title="Unit 1 Test",
            subject="Mathematics",
            defaults={"date": datetime.date.today(), "max_score": 100},
        )
        TestScore.objects.get_or_create(test=test, student=student_profile, defaults={"score": 82})

        Feedback.objects.get_or_create(
            student=student_profile,
            author_teacher=teacher_profile,
            message="Sam is making great progress with fractions this term.",
        )

        course, _ = Course.objects.get_or_create(
            title="Foundations of Algebra",
            defaults={
                "description": "A friendly introduction to algebraic thinking for middle schoolers.",
                "category": Course.Category.MATH,
                "price": 999.00,
                "is_published": True,
                "created_by": admin,
            },
        )

        self.stdout.write(self.style.SUCCESS("Seed complete. Demo logins (password shown):"))
        self.stdout.write("  Admin   : admin@edumanage.test   / Admin@12345")
        self.stdout.write("  Teacher : teacher@edumanage.test / Teacher@12345")
        self.stdout.write(f"  Student : student@edumanage.test / Student@12345  (Student ID: {student_profile.student_id})")
        self.stdout.write("  Parent  : parent@edumanage.test  / Parent@12345  (already linked to Sam Student)")
        self.stdout.write(
            f"  Unauthorized student for testing the rejection path: "
            f"unlinked.student@edumanage.test (Student ID: {unlinked_student.student_id}) - "
            f"searchable by the demo parent, but linking will be rejected until "
            f"an admin authorizes it."
        )
