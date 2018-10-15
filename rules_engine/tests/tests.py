'''
Created on Oct 15, 2018

@author: serban
'''
import pytest
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from testlib.fixtures import not_yet_valid_rule_and_demo_data
from notifications.models import Notification


@pytest.mark.django_db(transaction=True)
class TestExpirationRule:

    def test_not_yet_valid_rule_notification(
            self, not_yet_valid_rule_and_demo_data):
        """
        test that expiration rules will trigger "not yet valid"
        notifications
        """
        import ipdb
        ipdb.set_trace()
        pass
