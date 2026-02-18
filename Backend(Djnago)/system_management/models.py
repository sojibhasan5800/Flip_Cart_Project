from django.db import models
from django.utils.dateparse import parse_datetime


# Create your models here.

class DashboardGlobalSettings(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.JSONField(default=dict)  # flexible

    class Meta:
        verbose_name_plural = "Global Settings"

    @classmethod
    def get_dashboard_scheduler_settings(cls):
        obj, _ = cls.objects.get_or_create(key="dashboard_scheduler")
        return obj

    @classmethod
    def is_enabled(cls):
        settings = cls.get_dashboard_scheduler_settings()
        return settings.value.get("enabled", True)

    @classmethod
    def get_interval_minutes(cls):
        settings = cls.get_dashboard_scheduler_settings()
        return settings.value.get("interval_minutes", 1)

    @classmethod
    def get_resume_at(cls):
        settings = cls.get_dashboard_scheduler_settings()
        resume_str = settings.value.get("resume_at")

        if resume_str:
            return parse_datetime(resume_str)

        return None

