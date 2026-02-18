from .models import DashboardGlobalSettings 
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from datetime import timedelta
from .permissions import IsPlatformSuperAdmin

class DashboardSchedulerControlAPIView(APIView):
    permission_classes = [IsPlatformSuperAdmin]
    def get(self, request):
        task = PeriodicTask.objects.filter(
            name='update-active-merchant-dashboards-every-minute'
        ).first()

        settings = DashboardGlobalSettings.get_dashboard_scheduler_settings()
        data = settings.value

        resume_at = DashboardGlobalSettings.get_resume_at()
        resume_in = None
        if resume_at and resume_at > timezone.now():
            resume_in = int((resume_at - timezone.now()).total_seconds() / 60)  # minutes

        return Response({
            "enabled": data.get("enabled", True),
            "interval_minutes": data.get("interval_minutes", 1),
            "resume_at": resume_at.isoformat() if resume_at else None,
            "resume_in_minutes": resume_in,
            "task_last_run": task.last_run_at.isoformat() if task and task.last_run_at else None,
            "task_total_runs": task.total_run_count if task else 0,
        })

    def post(self, request):
        action = request.data.get("action")
        interval_minutes = request.data.get("interval_minutes")
        off_duration_minutes = request.data.get("off_duration_minutes")  # নতুন
        print("action:", action, "interval_minutes:", interval_minutes, "off_duration_minutes:", off_duration_minutes)  # for debugging
        settings_obj = DashboardGlobalSettings.get_dashboard_scheduler_settings()
        current = settings_obj.value

        task = PeriodicTask.objects.filter(
            name='update-active-merchant-dashboards-every-minute'
        ).first()

        if not task:
            return Response({"error": "Scheduler task not found"}, status=404)

        updated = False

        if action == "toggle":
            enabled = not current.get("enabled", True)
            current["enabled"] = enabled

            if not enabled and off_duration_minutes:
                resume_at = timezone.now() + timedelta(minutes=off_duration_minutes)
                current["resume_at"] = resume_at.isoformat()
            elif enabled:
                current.pop("resume_at", None)

            updated = True

        if interval_minutes:
            try:
                interval_minutes = int(interval_minutes)

                if interval_minutes >= 1:
                    current["interval_minutes"] = interval_minutes

                    schedule, _ = IntervalSchedule.objects.get_or_create(
                        every=interval_minutes,
                        period=IntervalSchedule.MINUTES,
                    )

                    task.interval = schedule
                    task.save()

                    updated = True

            except (ValueError, TypeError):
                return Response({"error": "Invalid interval_minutes"}, status=400)

        if updated:
            settings_obj.value = current
            settings_obj.save()

            # WebSocket-এ broadcast করুন
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "global_merchant_dashboard",
                {
                    "type": "scheduler_settings_update",
                    "data": {
                        "enabled": current.get("enabled", True),
                        "interval_minutes": current.get("interval_minutes", 1),
                        "resume_at": current.get("resume_at"),
                    }
                }
            )

        return Response({
            "message": "Settings updated",
            "enabled": current.get("enabled", True),
            "interval_minutes": current.get("interval_minutes", 1),
            "resume_at": current.get("resume_at")
        })