from hypothesis.extra.django import TestCase

from p_soc_auto_base.utils import get_or_create_user


class UserTestCase(TestCase):
    """
    Class that provides set-up for test cases that require users
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user = get_or_create_user()
        cls.USER_ARGS = {'created_by': user, 'updated_by': user}
