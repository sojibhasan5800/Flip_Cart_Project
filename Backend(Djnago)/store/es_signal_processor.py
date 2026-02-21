# store/es_signal_processor.py
from django.conf import settings
from django_elasticsearch_dsl.signals import RealTimeSignalProcessor

class ConditionalSignalProcessor(RealTimeSignalProcessor):
    def handle_save(self, sender, instance, **kwargs):
        if getattr(settings, "ELASTICSEARCH_OFFLINE", False):
            return
        try:
            super().handle_save(sender, instance, **kwargs)
        except Exception:
            pass

    def handle_delete(self, sender, instance, **kwargs):
        if getattr(settings, "ELASTICSEARCH_OFFLINE", False):
            return
        try:
            super().handle_delete(sender, instance, **kwargs)
        except Exception:
            pass
