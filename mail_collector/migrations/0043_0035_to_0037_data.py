
from django.conf import settings
from django.contrib.auth.models import User
from django.db import migrations
from django.utils import dateparse


def add_exchange_config(apps, schema_editor):

    user = User.objects.filter(username=settings.CITRUS_BORG_SERVICE_USER)
    if user.exists():
        user = user.get()
    else:
        user = User.objects.create_user(settings.CITRUS_BORG_SERVICE_USER)

    exchange_acounts = [
        'z-spexcm001-db01001@phsa.ca', 'z-spexcm001-db01002@phsa.ca',
        'z-spexcm001-db01003@phsa.ca', 'z-spexcm001-db01004@phsa.ca',
        'z-spexcm001-db01005@phsa.ca', 'z-spexcm001-db01006@phsa.ca',
        'z-spexcm001-db01007@phsa.ca', 'z-spexcm002-db02001@phsa.ca',
        'z-spexcm002-db02002@phsa.ca', 'z-spexcm002-db02003@phsa.ca',
        'z-spexcm002-db02004@phsa.ca', 'z-spexcm002-db02005@phsa.ca',
        'z-spexcm002-db02006@phsa.ca', 'z-spexcm002-db02007@phsa.ca',
        'z-spexcm003-db03001@phsa.ca', 'z-spexcm003-db03002@phsa.ca',
        'z-spexcm003-db03003@phsa.ca', 'z-spexcm003-db03004@phsa.ca',
        'z-spexcm003-db03005@phsa.ca', 'z-spexcm003-db03006@phsa.ca',
        'z-spexcm003-db03007@phsa.ca', 'z-spexcm004-db04001@phsa.ca',
        'z-spexcm004-db04002@phsa.ca', 'z-spexcm004-db04003@phsa.ca',
        'z-spexcm004-db04004@phsa.ca', 'z-spexcm004-db04005@phsa.ca',
        'z-spexcm004-db04006@phsa.ca', 'z-spexcm004-db04007@phsa.ca',
        'z-spexcm005-db05001@phsa.ca', 'z-spexcm005-db05002@phsa.ca',
        'z-spexcm005-db05003@phsa.ca', 'z-spexcm005-db05004@phsa.ca',
        'z-spexcm005-db05005@phsa.ca', 'z-spexcm005-db05006@phsa.ca',
        'z-spexcm005-db05007@phsa.ca', 'z-spexcm006-db06001@phsa.ca',
        'z-spexcm006-db06002@phsa.ca', 'z-spexcm006-db06003@phsa.ca',
        'z-spexcm006-db06004@phsa.ca', 'z-spexcm006-db06005@phsa.ca',
        'z-spexcm006-db06006@phsa.ca', 'z-spexcm006-db06007@phsa.ca',
        'z-spexcm007-db07001@phsa.ca', 'z-spexcm007-db07002@phsa.ca',
        'z-spexcm007-db07003@phsa.ca', 'z-spexcm007-db07004@phsa.ca',
        'z-spexcm007-db07005@phsa.ca', 'z-spexcm007-db07006@phsa.ca',
        'z-spexcm007-db07007@phsa.ca', 'z-spexcm008-db08001@phsa.ca',
        'z-spexcm008-db08002@phsa.ca', 'z-spexcm008-db08003@phsa.ca',
        'z-spexcm008-db08004@phsa.ca', 'z-spexcm008-db08005@phsa.ca',
        'z-spexcm008-db08006@phsa.ca', 'z-spexcm008-db08007@phsa.ca',
        'z-spexcm101-db01001@phsa.ca', 'z-spexcm101-db01002@phsa.ca',
        'z-spexcm101-db01003@phsa.ca', 'z-spexcm102-db02001@phsa.ca',
        'z-spexcm102-db02002@phsa.ca', 'z-spexcm102-db02003@phsa.ca',
        'z-spexcm103-db03001@phsa.ca', 'z-spexcm103-db03002@phsa.ca',
        'z-spexcm103-db03003@phsa.ca', 'z-spexcm104-db04001@phsa.ca',
        'z-spexcm104-db04002@phsa.ca', 'z-spexcm104-db04003@phsa.ca',
        'z-spexcm105-db05001@phsa.ca', 'z-spexcm105-db05002@phsa.ca',
        'z-spexcm105-db05003@phsa.ca', 'z-spexcm106-db06001@phsa.ca',
        'z-spexcm106-db06002@phsa.ca', 'z-spexcm106-db06003@phsa.ca',
        'z-spexcm107-db07001@phsa.ca', 'z-spexcm107-db07002@phsa.ca',
        'z-spexcm107-db07003@phsa.ca', 'z-spexcm108-db08001@phsa.ca',
        'z-spexcm108-db08002@phsa.ca', 'z-spexcm108-db08003@phsa.ca',
        'z-spexcm109-db09001@phsa.ca', 'z-spexcm109-db09002@phsa.ca',
        'z-spexcm109-db09003@phsa.ca', 'z-spexcm110-db10001@phsa.ca',
        'z-spexcm110-db10002@phsa.ca', 'z-spexcm110-db10003@phsa.ca',
        'z-spexcm111-db11001@phsa.ca', 'z-spexcm111-db11002@phsa.ca',
        'z-spexcm111-db11003@phsa.ca', 'z-spexcm112-db12001@phsa.ca',
        'z-spexcm112-db12002@phsa.ca', 'z-spexcm112-db12003@phsa.ca',
        'z-spexcm113-db13001@phsa.ca', 'z-spexcm113-db13002@phsa.ca',
        'z-spexcm113-db13003@phsa.ca', 'z-spexcm114-db14001@phsa.ca',
        'z-spexcm114-db14002@phsa.ca', 'z-spexcm114-db14003@phsa.ca']

    witness_emails = ['serban.teodorescu@phsa.ca', 'james.reilly@phsa.ca', ]

    DomainAccount = apps.get_model('mail_collector.DomainAccount')

    domain_account = DomainAccount(domain='PHSABC',
                                   username='svc_SOCmailbox',
                                   password='goodluckwiththat',
                                   is_default=True,
                                   created_by_id=user.id,
                                   updated_by_id=user.id)
    domain_account.save()

    ExchangeAccount = apps.get_model('mail_collector.ExchangeAccount')

    for exchange_account in exchange_acounts:
        _ = ExchangeAccount(smtp_address=exchange_account,
                            domain_account=domain_account,
                            created_by_id=user.id,
                            updated_by_id=user.id)
        _.save()

    WitnessEmail = apps.get_model('mail_collector.WitnessEmail')

    for witness_email in witness_emails:
        _ = WitnessEmail(smtp_address=witness_email, created_by_id=user.id,
                         updated_by_id=user.id)
        _.save()

    ExchangeConfiguration = apps.get_model(
        'mail_collector.ExchangeConfiguration')

    exchange_configuration = ExchangeConfiguration(
        config_name='default configuration',
        is_default=True,
        created_by_id=user.id,
        updated_by_id=user.id)

    exchange_configuration.save()
    for exchange_account in ExchangeAccount.objects.all():
        exchange_configuration.exchange_accounts.add(exchange_account)


def create_fake_site_bot(apps, schema_editor):

    user = User.objects.filter(username=settings.CITRUS_BORG_SERVICE_USER)
    if user.exists():
        user = user.get()
    else:
        user = User.objects.create_user(settings.CITRUS_BORG_SERVICE_USER)

    Site = apps.get_model('citrus_borg', 'BorgSite')
    Borg = apps.get_model('citrus_borg', 'WinlogbeatHost')
    ExchangeConfiguration = apps.get_model('mail_collector',
                                           'ExchangeConfiguration')

    sites_and_bots = [
        {'site': 'site.not.exist',
         'notes': (
             'fake site to be used when an exchange bot is first'
             ' seen by the system'),
         'enabled': False,
         'bots': [{'host_name': 'host.not.exist',
                   'notes': (
                       'fake host to be used when retrieving the exchange'
                       ' configuration for an exchange bot not known to the'
                       ' system'),
                   'exchange_client_config':
                   ExchangeConfiguration.objects.filter(is_default=True).get(),
                   'excgh_last_seen':
                   dateparse.parse_datetime('1970-01-01T00:00:00+00'),
                   'enabled': False}, ], },
    ]

    for _site in sites_and_bots:
        site = Site.objects.filter(site__iexact=_site['site'])
        if site.exists():
            site = site.get()
        else:
            site = Site(site=_site.get('site'), notes=_site.get('notes'),
                        created_by_id=user.id, updated_by_id=user.id,
                        enabled=_site.get('enabled'))
            site.save()
        for _bot in _site['bots']:
            bot = Borg.objects.filter(host_name__iexact=_bot['host_name'])
            if bot.exists():
                bot = bot.get()
            else:
                bot = Borg(
                    host_name=_bot['host_name'],
                    excgh_last_seen=_bot.get('excgh_last_seen'),
                    created_by_id=user.id, updated_by_id=user.id)

            bot.site = site
            bot.notes = _bot.get('notes')
            bot.enabled = _bot.get('enabled')
            bot.exchange_client_config = _bot.get('exchange_client_config')

            bot.save()


class Migration(migrations.Migration):
    replaces = [
        ('mail_collector', '0035_add_exchange_config_default'),
        ('mail_collector', '0036_host_site_not_exist'),
        ('mail_collector', '0037_merge_20190819_1311')
    ]

    dependencies = [
        ('mail_collector', '0042_0001_to_0041_model'),
        ('citrus_borg', '0029_0001_to_0027_foreign_keys'),
        ('auth', '0011_update_proxy_permissions'),
    ]

    operations = [
        migrations.RunPython(add_exchange_config,
                             reverse_code=migrations.RunPython.noop),
        migrations.RunPython(create_fake_site_bot,
                             reverse_code=migrations.RunPython.noop),
    ]