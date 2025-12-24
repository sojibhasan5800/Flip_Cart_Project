from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from cloudinary.models import CloudinaryField
from merchant_user.models import Organization
from django_tenants.utils import get_tenant_model, tenant_context




# ----------------------- Previous ----------------------------

class MyAccountManager(BaseUserManager):

    # def get_queryset(self):
    # # Override default queryset to return only active users
    #     return super().get_queryset().filter(is_active=True)

    def create_user(self, first_name, last_name, username, email,phone_number=None, password=None,organization=None):
        if not email:
            raise ValueError('User must have an email address')

        if not username:
            raise ValueError('User must have an username')

        user = self.model(
            email = self.normalize_email(email),
            username = username,
            first_name = first_name,
            last_name = last_name,
            phone_number = phone_number,
            organization=organization,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, first_name, last_name, email, username, password, phone_number=None):
        user = self.create_user(
            email = self.normalize_email(email),
            username = username,
            password = password,
            first_name = first_name,
            last_name = last_name,
            phone_number=phone_number or '0000000000',
        )
        # tenant fields False
        user.is_tenant_owner = False
        user.is_tenant_staff = False
        user.is_admin = True
        user.is_active = True
        user.is_staff = True
        user.is_superadmin = True
        user.save(using=self._db)
        return user



class Account(AbstractBaseUser):
    first_name      = models.CharField(max_length=50)
    last_name       = models.CharField(max_length=50)
    username        = models.CharField(max_length=50, unique=True)
    email           = models.EmailField(max_length=100, unique=True)
    phone_number    = models.CharField(max_length=50)

    # Tenant relationship
    organization = models.ForeignKey('merchant_user.Organization', on_delete=models.CASCADE, null=True, blank=True,related_name='users')

    # Role-based fields
    is_tenant_owner = models.BooleanField(default=False)
    is_tenant_staff = models.BooleanField(default=False)
                              

    # required
    date_joined     = models.DateTimeField(auto_now_add=True)
    last_login      = models.DateTimeField(auto_now_add=True)
    is_admin        = models.BooleanField(default=False)
    is_staff        = models.BooleanField(default=False)
    is_active       = models.BooleanField(default=False)
    is_superadmin   = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    objects = MyAccountManager()

    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, add_label):
        return True
    
    def delete(self, using=None, keep_parents=False):
        TenantModel = get_tenant_model()
        tenants = TenantModel.objects.all()
        for tenant in tenants:
            try:
                with tenant_context(tenant):
                    # ReviewRating: NULL
                    from store.models import ReviewRating
                    ReviewRating.objects.filter(user=self).update(user=None)
                    # Carts: ডিলিট
                    from carts.models import Cart, CartItem
                    Cart.objects.filter(user=self).delete()
                    CartItem.objects.filter(user=self).delete()
                    # Orders: NULL
                    from orders.models import Order, OrderProduct
                    Order.objects.filter(user=self).update(user=None)
                    OrderProduct.objects.filter(user=self).update(user=None)
                    # অন্যান্য যদি থাকে, অ্যাড করুন
            except Exception as e:
                pass  # ডিলিটেড টেন্যান্ট স্কিপ
        super(Account, self).delete(using=using, keep_parents=keep_parents)

class UserProfile(models.Model):
    user = models.OneToOneField(Account, on_delete=models.CASCADE)
    address_line_1 = models.CharField(blank=True, max_length=100)
    address_line_2 = models.CharField(blank=True, max_length=100)
    profile_picture = CloudinaryField('image', blank=True,default='default_snzedf')
    city = models.CharField(blank=True, max_length=20)
    state = models.CharField(blank=True, max_length=20)
    country = models.CharField(blank=True, max_length=20)

    def __str__(self):
        return self.user.first_name

    def full_address(self):
        return f'{self.address_line_1} {self.address_line_2}'



