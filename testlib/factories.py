'''
Created on Oct 5, 2018

@author: serban
'''
import factory

from django.contrib.auth import get_user_model


class UserFactory(factory.DjangoModelFactory):
    """
    factory for the User model
    """
    class Meta:
        model = get_user_model()

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_superuser = False
    is_active = True
    is_staff = True

    @factory.lazy_attribute
    def username(self):
        """
        build username from firt and last name
        """
        return '{}{}'.format(
            str(self.first_name)[0].lower(), str(self.last_name).lower())

    @factory.lazy_attribute
    def email(self):
        """
        build email from username
        """
        return '{}@phsa.ca'.format(self.username)
