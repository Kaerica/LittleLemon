from django.contrib.auth.models import User

username = 'admin'
password = 'AdminPass123'
email = 'admin@littlelemon.local'

if User.objects.filter(username=username).exists():
    print('Superuser exists')
else:
    User.objects.create_superuser(username=username, email=email, password=password)
    print('Superuser created')
