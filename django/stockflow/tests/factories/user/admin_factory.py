import factory

class AdminFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'auth.User'

    username = factory.Faker('user_name')
    email = factory.Faker('email')
    is_staff = True
    is_superuser = True
    password = factory.PostGenerationMethodCall('set_password', 'password')
