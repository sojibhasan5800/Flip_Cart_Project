from django.apps import AppConfig


class OrdersWorkerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'orders_worker'
    def ready(self):
        import orders_worker.consumer  # Point: worker consumer auto-load
