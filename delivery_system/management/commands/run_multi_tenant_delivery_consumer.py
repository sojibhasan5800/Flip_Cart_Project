# delivery_system/management/commands/run_multi_tenant_delivery_consumer.py
import time
import sys
from django.core.management.base import BaseCommand
from delivery_system.consumers import MultiTenantDeliveryConsumer


class Command(BaseCommand):
    help = 'Run Multi-tenant RabbitMQ Delivery Consumer'

    def handle(self, *args, **options):
        consumer = MultiTenantDeliveryConsumer()
        
        while True:
            try:
                consumer.connect()
                consumer.start_consuming()
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING('Multi-tenant delivery consumer stopped by user'))
                consumer.close()
                sys.exit(0)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Multi-tenant delivery consumer error: {e}'))
                self.stdout.write('Reconnecting in 5 seconds...')
                time.sleep(5)
                continue