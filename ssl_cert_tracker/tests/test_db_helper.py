"""
.. _models:

django models for the ssl_certificates app

:module:    test_db_helper.py

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

"""
import pytest
from django.utils import timezone
from ssl_cert_tracker.models import NmapCertsData, NmapHistory

@pytest.mark.django_db
def test_insert_into_certs_data():
    """test_insert_into_certs_data inserts data into model then
    do a sanity check"""
    NmapCertsData.created_by = NmapCertsData.get_or_create_user(username=
                                                                'PHSA_User')
    cert = NmapCertsData(xml_data="sample data",
                         addresses="10.10.10.10",
                         orion_id="12345",
                         not_before=timezone.now(),
                         not_after=timezone.now(),
                         md5="57adc7886d93a03d934ae691178748b7",
                         sha1="ae699d5ebddce6ed574111262f19bb18efbe73b0",
                         created_by_id=NmapCertsData.created_by.id,
                         updated_by_id=NmapCertsData.created_by.id,
                         updated_on=timezone.now())
    cert.save()
    assert cert.sha1 is not "57adc7886d93a03d934ae691178748b7"
    assert cert.md5 is "57adc7886d93a03d934ae691178748b7"
    assert (NmapHistory.objects.filter(md5="57adc7886d93a03d934ae691178748b7")
            .count() is 1)
