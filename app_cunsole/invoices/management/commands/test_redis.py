# myapp/management/commands/test_redis.py
from django.core.management.base import BaseCommand
from django.conf import settings
import redis

class Command(BaseCommand):
    help = 'Test Redis connection'

    def handle(self, *args, **kwargs):
        try:
            redis_client = redis.StrictRedis.from_url(settings.CACHES['default']['LOCATION'])
            redis_client.set('test_key', 'Hello, Redis!')
            value = redis_client.get('test_key')
            self.stdout.write(self.style.SUCCESS(f'Redis is working! Value: {value.decode()}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error connecting to Redis: {e}'))
