from django.apps import AppConfig


class MerchantUserConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'merchant_user'
    
    def ready(self):
        import merchant_user.signals

# # merchant_user/apps.py
# from django.apps import AppConfig
# from django.db import connection

# class MerchantUserConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'merchant_user'
    
#     def ready(self):
#         old_schema = connection.schema_name
#         connection.set_schema_to_public()   # ← জোর করে public-এ নিয়ে যাও
#         try:
#             import merchant_user.signals
#         finally:
#             connection.set_schema(old_schema)  # শেষে আগের schema-এ ফিরিয়ে দাও