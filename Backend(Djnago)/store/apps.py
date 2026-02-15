from django.apps import AppConfig

class StoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'store'

    def ready(self):
        import store.signals  #  এই লাইন signals activate করে

# # store/apps.py
# from django.apps import AppConfig
# from django.db import connection

# class StoreConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'store'

#     def ready(self):
#         old_schema = connection.schema_name
#         connection.set_schema_to_public()
#         try:
#             import store.signals
#         finally:
#             connection.set_schema(old_schema)