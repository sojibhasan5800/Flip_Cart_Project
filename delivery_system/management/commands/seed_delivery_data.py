# delivery_system/management/commands/seed_delivery_data.py
from django.core.management.base import BaseCommand
from django_tenants.utils import tenant_context
from delivery_system.models import (
    DeliveryTenant, Division, District, DeliveryArea, DeliveryTimeSlot
)


class Command(BaseCommand):
    help = 'Seed delivery data for all tenants'

    def handle(self, *args, **options):
        self.stdout.write('Seeding delivery data for all tenants...')
        
        tenants = DeliveryTenant.objects.all()
        
        for tenant in tenants:
            with tenant_context(tenant):
                self.seed_tenant_data(tenant)
        
        self.stdout.write(self.style.SUCCESS('Successfully seeded delivery data for all tenants!'))
    
    def seed_tenant_data(self, tenant):
        """Seed delivery data for a specific tenant"""
        self.stdout.write(f'Seeding data for tenant: {tenant.name}')
        
        # Create Divisions
        divisions_data = [
            'Dhaka', 'Chittagong', 'Rajshahi', 'Khulna', 'Barishal', 
            'Sylhet', 'Rangpur', 'Mymensingh'
        ]
        
        divisions = {}
        for division_name in divisions_data:
            division, created = Division.objects.get_or_create(
                tenant=tenant,
                name=division_name
            )
            divisions[division_name] = division
            if created:
                self.stdout.write(f'  Created division: {division_name}')
        
        # Create Districts for Dhaka Division
        dhaka_districts = [
            'Dhaka', 'Gazipur', 'Narayanganj', 'Tangail', 'Kishoreganj',
            'Manikganj', 'Munshiganj', 'Narsingdi', 'Faridpur', 'Rajbari',
            'Gopalganj', 'Madaripur', 'Shariatpur'
        ]
        
        for district_name in dhaka_districts:
            district, created = District.objects.get_or_create(
                tenant=tenant,
                division=divisions['Dhaka'],
                name=district_name
            )
            if created:
                self.stdout.write(f'  Created district: {district_name}')
        
        # Create Delivery Areas for Dhaka District
        dhaka_areas = [
            ('Gulshan', 80.00, 1, 2),
            ('Banani', 70.00, 1, 2),
            ('Dhanmondi', 60.00, 1, 3),
            ('Mirpur', 50.00, 2, 4),
            ('Uttara', 90.00, 1, 3),
            ('Mohammadpur', 55.00, 2, 4),
            ('Motijheel', 65.00, 1, 2),
            ('Old Dhaka', 45.00, 2, 5),
        ]
        
        dhaka_district = District.objects.get(
            tenant=tenant,
            name='Dhaka', 
            division=divisions['Dhaka']
        )
        
        for area_name, charge, min_days, max_days in dhaka_areas:
            area, created = DeliveryArea.objects.get_or_create(
                tenant=tenant,
                district=dhaka_district,
                area_name=area_name,
                defaults={
                    'delivery_charge': charge,
                    'min_delivery_days': min_days,
                    'max_delivery_days': max_days
                }
            )
            if created:
                self.stdout.write(f'  Created delivery area: {area_name} - ৳{charge}')
        
        # Create Time Slots
        time_slots = [
            ('Morning Delivery', '09:00', '12:00', '09:00-12:00'),
            ('Noon Delivery', '12:00', '15:00', '12:00-15:00'),
            ('Afternoon Delivery', '15:00', '18:00', '15:00-18:00'),
            ('Evening Delivery', '18:00', '21:00', '18:00-21:00'),
        ]
        
        for slot_name, start_time, end_time, slot_code in time_slots:
            slot, created = DeliveryTimeSlot.objects.get_or_create(
                tenant=tenant,
                slot_code=slot_code,
                defaults={
                    'slot_name': slot_name,
                    'start_time': start_time,
                    'end_time': end_time,
                    'max_orders_per_slot': 100
                }
            )
            if created:
                self.stdout.write(f'  Created time slot: {slot_name}')