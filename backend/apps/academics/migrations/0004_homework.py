from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("academics", "0003_remove_feedback_author_mentor_test_duration_minutes_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Homework",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True)),
                ("due_date", models.DateField()),
                ("material_type", models.CharField(choices=[("text", "Text"), ("image", "Image"), ("pdf", "PDF"), ("text_file", "Text file"), ("link", "Link")], default="text", max_length=20)),
                ("material_text", models.TextField(blank=True)),
                ("material_file", models.FileField(blank=True, null=True, upload_to="homework_materials/")),
                ("material_url", models.URLField(blank=True)),
                ("status", models.CharField(choices=[("assigned", "Assigned"), ("submitted", "Submitted")], default="assigned", max_length=20)),
                ("submission_text", models.TextField(blank=True)),
                ("submission_file", models.FileField(blank=True, null=True, upload_to="homework_submissions/")),
                ("submitted_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="homework", to="accounts.studentprofile")),
                ("teacher", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="homework_assigned", to="accounts.teacherprofile")),
            ],
            options={
                "ordering": ["due_date", "-created_at"],
                "unique_together": {("teacher", "student", "title", "due_date")},
            },
        ),
        migrations.AddIndex(
            model_name="homework",
            index=models.Index(fields=["student", "status"], name="academics_h_student_8767d4_idx"),
        ),
    ]
