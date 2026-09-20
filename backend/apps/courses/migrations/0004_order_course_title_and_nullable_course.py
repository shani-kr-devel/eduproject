from django.db import migrations, models
import django.db.models.deletion


def copy_course_titles(apps, schema_editor):
    Order = apps.get_model("courses", "Order")
    for order in Order.objects.select_related("course").all():
        if order.course_id and order.course:
            order.course_title = order.course.title
            order.save(update_fields=["course_title"])


class Migration(migrations.Migration):
    dependencies = [
        ("courses", "0003_coursecontentprogress"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="course_title",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
        migrations.RunPython(copy_course_titles, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="order",
            name="course",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="orders",
                to="courses.course",
            ),
        ),
    ]
