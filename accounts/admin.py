# from rest_framework.authtoken.models import Token
# from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin
# from .models import Account, UserProfile
# from django.utils.html import format_html

# # Register your models here.

# class AccountAdmin(UserAdmin):
#     list_display = ('email','id',  'first_name', 'last_name', 'username', 'last_login', 'date_joined', 'is_active')
#     list_display_links = ('email','first_name', 'last_name')
#     readonly_fields = ('last_login', 'date_joined')
#     ordering = ('-date_joined',)

#     filter_horizontal = ()
#     list_filter = ()
#     fieldsets = ()

# class UserProfileAdmin(admin.ModelAdmin):
#     def thumbnail(self, object):
#         return format_html('<img src="{}" width="30" style="border-radius:50%;">'.format(object.profile_picture.url))
#     thumbnail.short_description = 'Profile Picture'
#     list_display = ('thumbnail', 'user_id', 'user', 'city', 'state', 'country')

# admin.site.register(Account, AccountAdmin)
# admin.site.register(UserProfile, UserProfileAdmin)



# class TokenAdmin(admin.ModelAdmin):
#     list_display = ('key', 'user_email', 'created')  # এখানে ইউজারের ইমেইল দেখাবো

#     def user_email(self, obj):
#         return obj.user.email  # ইউজারের ইমেইল ফিরিয়ে দিচ্ছে
#     user_email.short_description = 'User Email'  # অ্যাডমিন পেজে কলামের নাম


# # এখন কাস্টম TokenAdmin দিয়ে Token মডেল রেজিস্টার করো
# admin.site.register(Token, TokenAdmin)


from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Account, UserProfile
from django.utils.html import format_html

# Account Admin
class AccountAdmin(UserAdmin):
    list_display = ('email','id',  'first_name', 'last_name', 'username', 'last_login', 'date_joined', 'is_active')
    list_display_links = ('email','first_name', 'last_name')
    readonly_fields = ('last_login', 'date_joined')
    ordering = ('-date_joined',)
    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()

# UserProfile Admin
class UserProfileAdmin(admin.ModelAdmin):
    def thumbnail(self, object):
        return format_html('<img src="{}" width="30" style="border-radius:50%;">'.format(object.profile_picture.url))
    thumbnail.short_description = 'Profile Picture'
    list_display = ('thumbnail', 'user_id', 'user', 'city', 'state', 'country')

admin.site.register(Account, AccountAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
