import factory

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'auth.User'

    username = factory.Faker('user_name')
    email = factory.Faker('email')
    password = factory.PostGenerationMethodCall('set_password', 'password')
