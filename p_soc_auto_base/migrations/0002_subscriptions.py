from django.db import migrations

from p_soc_auto_base.utils import get_or_create_user

from p_soc_auto_base.migrations import create_subscription


def populate_subscriptions(apps, schema_editor):
    # TODO do I need to add subjects to all the subscriptions that did have them
    citrix_subs = [
        {'name': 'Dead Citrix monitoring bots',
         'template_name': 'borg_hosts_dead',
         'headers': 'host_name,ip_address,site__site,last_seen', },
        {'name': 'Dead Citrix client sites',
         'template_name': 'borg_sites_dead',
         'headers': 'site,winlogbeathost__last_seen', },
        {'name': 'Missing Citrix farm hosts',
         'template_name': 'borg_servers_dead',
         'headers': 'broker_name,last_seen', },
        {'name': 'Citrix logon event summary',
         'template_name': 'borg_logins_by_host_report',
         'headers': 'host_name,site__site,hour,failed_events,successful_events',
         },
        {'name': 'citrix logon alert',
         'template_name': 'borg_failed_logins',
         'headers': 'host_name,site__site,hour,failed_events', },
        {'name': 'Citrix Failed Logins Report',
         'template_name': 'borg_failed_logins_report',
         'headers': 'created_on,source_host__site__site,source_host__host_name'
                    ',failure_reason,failure_details', },
        {'name': 'Citrix Failed Logins per Site Report',
         'template_name': 'borg_failed_logins_by_site_report',
         'headers': 'created_on,failure_reason,failure_details', },
        {'subscription': 'Citrix logon event and ux summary',
         'email_subject': 'Logon Events and Response Time Summary over the'
                          ' Last',
         'alternate_email_subject': 'Logon Events and Response Time Summary'
                                    ' by Hour',
         'headers': 'hour,failed_events,successful_events,'
                    'avg_storefront_connection_time,avg_receiver_startup_time,'
                    'avg_connection_achieved_time,avg_logon_time,'
                    'undetermined_events',
         'template_name': 'login_ux_site_borg', },
    ]
        # TODO did the format of subscriptions change?
    ldap_subs = [
        {'subscription': 'LDAP: Error alerts subscription',
         'template_name': 'ldap_error_alert',
         'email_subject': 'AD Controller Error',
         'alternate_email_subject': '',
         'headers': 'uuid,ad_orion_node,ad_node,created_on,errors', },
        {'subscription': 'LDAP: Performance alerts subscription',
         'template_name': 'ldap_perf_error',
         'email_subject': 'AD Service Performance Degradation',
         'alternate_email_subject': '',
         'headers': 'elapsed_initialize,elapsed_bind,elapsed_search_ext,'
                    'elapsed_anon_bind,elapsed_read_root', },
        {'subscription': 'LDAP: summary report, anonymous bind, non orion',
         'template_name': 'ldap_summary_report',
         'email_subject': 'AD Services Monitoring Summary Report',
         'alternate_email_subject': '',
         # TODO is successful really misspelled?
         'headers': 'node_dns,number_of_failed_probes,'
                    'number_of_successfull_probes,average_initialize_duration,'
                    'minimum_bind_duration,average_bind_duration,'
                    'maximum_bind_duration,minimum_read_root_dse_duration,'
                    'average_read_root_dse_duration,'
                    'maximum_read_root_dse_duration,orion_url,probes_url', },
        {'subscription': 'LDAP: summary report, anonymous bind, orion',
         'template_name': 'ldap_summary_report',
         'email_subject': 'AD Services Monitoring Summary Report',
         'alternate_email_subject': '',
         'headers': 'node__node_caption,orion_anchor,number_of_failed_probes,'
                    'number_of_successfull_probes,average_initialize_duration,'
                    'minimum_bind_duration,average_bind_duration,'
                    'maximum_bind_duration,minimum_read_root_dse_duration,'
                    'average_read_root_dse_duration,'
                    'maximum_read_root_dse_duration,orion_url,probes_url', },
        {'subscription': 'LDAP: summary report, full bind, non orion',
         'template_name': 'ldap_summary_report',
         'email_subject': 'AD Services Monitoring Summary Report',
         'alternate_email_subject': '',
         'headers': 'node_dns,number_of_failed_probes,'
                    'number_of_successfull_probes,average_initialize_duration,'
                    'minimum_bind_duration,average_bind_duration,'
                    'maximum_bind_duration,minimum_extended_search_duration,'
                    'average_extended_search_duration,'
                    'maximum_extended_search_duration,orion_url,probes_url', },
        {'subscription': 'LDAP: summary report, full bind, orion',
         'template_name': 'ldap_summary_report',
         'email_subject': 'AD Services Monitoring Summary Report',
         'alternate_email_subject': '',
         'headers': 'node__node_caption,orion_anchor,number_of_failed_probes,'
                    'number_of_successfull_probes,average_initialize_duration,'
                    'minimum_bind_duration,average_bind_duration,'
                    'maximum_bind_duration,minimum_extended_search_duration,'
                    'average_extended_search_duration,'
                    'maximum_extended_search_duration,orion_url,probes_url', },
        {'subscription': 'LDAP: error report',
         'template_name': 'ldap_error_report',
         'email_subject': 'AD Services Monitoring Errors',
         'alternate_email_subject': '',
         'headers': 'uuid,domain_controller_fqdn,created_on,errors,probe_url',
         },
        {'subscription': 'LDAP: non Orion AD nodes',
         'template_name': 'ldap_nono_nodes_report',
         'email_subject': 'Network Nodes Providing AD Services That Are Not'
                          ' Defined on the Orion Server',
         'alternate_email_subject': '',
         'headers': 'node_dns,created_on,updated_on', },
        {'subscription': 'LDAP: Orion FQDN AD nodes',
         'template_name': 'ldap_nono_nodes_report',
         'email_subject': 'Network Nodes Providing AD Services Improperly'
                          ' Defined on the Orion Server',
         'alternate_email_subject': '',
         'headers': 'node__node_caption,node__ip_address,orion_url', },
        {'subscription': 'LDAP: Duplicate Orion AD nodes',
         'template_name': 'ldap_nono_nodes_report',
         'email_subject': 'Network Nodes Providing AD Services With Duplicate'
                          ' Definitions on the Orion Server',
         'alternate_email_subject': '',
         'headers': 'node__node_caption,node__ip_address,orion_url', },
        {'subscription': 'LDAP: summary report, full bind, perf, orion,'
                         ' degrade',
         'template_name': 'ldap_perf_report',
         'email_subject': 'AD Services Monitoring Performance Degradation'
                          ' Report for Nodes Located in',
         'alternate_email_subject': '',
         'headers': 'node__node_caption,orion_anchor,average_bind_duration,'
                    'average_extended_search_duration,orion_url,probes_url', },
        {'subscription': 'LDAP: summary report, anonymous bind, perf, orion,'
                         ' degrade',
         'template_name': 'ldap_perf_report',
         'email_subject': 'AD Services Monitoring Performance Degradation '
                          'Report for Nodes Located in',
         'alternate_email_subject': '',
         'headers': 'node__node_caption,orion_anchor,average_bind_duration,'
                    'average_read_root_dse_duration,orion_url,probes_url', },
        {'subscription': 'LDAP: summary report, anonymous bind, perf, '
                         'non orion,degrade',
         'template_name': 'ldap_perf_report',
         'email_subject': 'AD Services Monitoring Performance Degradation '
                          'Report for Nodes Located in',
         'alternate_email_subject': '',
         'headers': 'node_dns,average_bind_duration,'
                    ' average_read_root_dse_duration,orion_url,probes_url', },
        {'subscription': 'LDAP: summary report, full bind, perf, non orion,'
                         'degrade',
         'template_name': 'ldap_perf_report',
         'email_subject': 'AD Services Monitoring Performance Degradation '
                          'Report for Nodes Located in',
         'alternate_email_subject': '',
         'headers': 'node_dns,average_bind_duration,'
                    'average_extended_search_duration,orion_url,probes_url', },
        {'subscription': 'LDAP: summary report, full bind, perf, orion,degrade,'
                         'err',
         'template_name': 'ldap_perf_report',
         'email_subject': 'AD Services Monitoring Performance Degradation '
                          'Report for Nodes Located in',
         'alternate_email_subject': '',
         'headers': 'node__node_caption,orion_anchor,maximum_bind_duration,'
                    'maximum_extended_search_duration,orion_url,probes_url', },
        {'subscription': 'LDAP: summary report, anonymous bind, perf, orion,'
                         'degrade,err',
         'template_name': 'ldap_perf_report',
         'email_subject': 'AD Services Monitoring Performance Degradation '
                          'Report for Nodes Located in',
         'alternate_email_subject': '',
         'headers': 'node__node_caption,orion_anchor,maximum_bind_duration,'
                    'maximum_read_root_dse_duration,orion_url,probes_url', },
        {'subscription': 'LDAP: summary report, anonymous bind, perf,'
                         ' non orion,degrade,err',
         'template_name': 'ldap_perf_report',
         'email_subject': 'AD Services Monitoring Performance Degradation'
                          ' Report for Nodes Located in',
         'alternate_email_subject': '',
         'headers': 'node_dns,maximum_bind_duration,'
                    'maximum_read_root_dse_duration,orion_url,probes_url', },
        {'subscription': 'LDAP: summary report, full bind, perf, non orion,'
                         'degrade,err',
         'template_name': 'ldap_perf_report',
         'email_subject': 'AD Services Monitoring Performance Degradation'
                          ' Report for Nodes Located in',
         'alternate_email_subject': '',
         'headers': 'node_dns,maximum_bind_duration,'
                    'maximum_extended_search_duration,orion_url,probes_url', },
    ]

    mail_subs = [
        {'subscription': 'Exchange Servers Not Seen',
         'template_name': 'exc_serv_alert_all',
         'email_subject': 'Exchange servers that have not serviced any '
                          'requests over the last',
         'alternate_email_subject': 'All Exchange Servers have serviced all '
                                    'requests over the last',
         'headers': 'exchange_server,last_updated', },
        {'subscription': 'Exchange Servers No Connection',
         'template_name': 'exc_serv_alert_all',
         'email_subject': 'Exchange servers that have not serviced any '
                          'connection requests over the last',
         'alternate_email_subject': 'All Exchange Servers have serviced all '
                                    'connection requests over the last',
         'headers': 'exchange_server,last_connected', },
        {'subscription': 'Exchange Servers No Send',
         'template_name': 'exc_serv_alert_all',
         'email_subject': 'Exchange servers that have not serviced any send '
                          'requests over the last',
         'alternate_email_subject': 'All Exchange Servers have serviced all '
                                    'send requests over the last',
         'headers': 'exchange_server,last_send', },
        {'subscription': 'Exchange Servers No Receive',
         'template_name': 'exc_serv_alert_all',
         'email_subject': 'Exchange servers that have not serviced any inbox '
                          'access requests over the last',
         'alternate_email_subject': 'All Exchange Servers have serviced all '
                                    'inbox access requests over the last',
         'headers': 'exchange_server,last_send', },
        {'subscription': 'Exchange Databases Not Seen',
         'template_name': 'exc_serv_alert_all',
         'email_subject': 'Exchange Databases that have not serviced any inbox '
                          'access requests over the last',
         'alternate_email_subject': 'All Exchange Databases have serviced all '
                                    'inbox access requests over the last',
         'headers': 'exchange_server,last_send', },
        {'subscription': 'Mail Unchecked On Site',
         'template_name': 'exc_serv_alert_all',
         'email_subject': 'Sites where email services have not been tested over'
                          ' the last',
         'alternate_email_subject': 'Email services have been tested at least'
                                    ' once on each site over the last',
         'headers': 'from_domain,to_domain,site,status,last_verified', },
        {'subscription': 'Mail Verification Failed',
         'template_name': 'mail_verify_fail',
         'email_subject': 'Site where email services verification failed',
         'alternate_email_subject': 'Email services are working on all sites',
         'headers': 'from_domain,to_domain,site,status,last_verified', },
        {'subscription': 'Exchange Client Site',
         'template_name': 'exc_serv_alert_all',
         'email_subject': 'Exchange client sites not been tested over the last',
         'alternate_email_subject': 'All Exchange client sites are up',
         'headers': 'site,winlogbeathost__excgh_last_seen', },
        {'subscription': 'Exchange Client Bot',
         'template_name': 'exc_serv_alert_all',
         'email_subject': 'Site where email services verification failed',
         'alternate_email_subject': 'Email services are working on all sites',
         'headers': 'host_name,site__site,excgh_last_seen', },
        {'subscription': 'Exchange Client Bots Not Seen',
         'template_name': 'exc_serv_alert_all',
         'email_subject': 'Exchange client bots that have not made any mail'
                          ' requests over the last',
         'alternate_email_subject': 'All Exchange client bots have been'
                                    ' functioning properly over the last',
         'headers': 'host_name,site__site,excgh_last_seen', },
        {'subscription': 'Exchange Client Bot Sites Not Seen',
         'template_name': 'exc_serv_alert_all',
         'email_subject': 'Exchange client bot sites that have not made any'
                          ' mail requests over the last',
         'alternate_email_subject': 'At least one Exchange client bot has been'
                                    ' functioning properly on each site over'
                                    ' the last',
         'headers': 'site__site.most_recent', },
        {'subscription': 'Exchange Send Receive By Site',
         'template_name': 'mail_events_by_site',
         'email_subject': 'Exchange send receive events for site',
         'alternate_email_subject': 'ERROR: No data for site ',
         'headers': 'mail_message_identifier,sent_from,sent_to,received_from,'
                    'received_by,event__source_host__host_name,'
                    'event__event_type,event__event_status,'
                    'event__event_registered_on', },
        {'subscription': 'Exchange Send Receive By Bot',
         'template_name': 'mail_events_by_bot',
         'email_subject': 'Exchange send receive events for bot',
         'alternate_email_subject': 'ERROR: No data for bot ',
         'headers': 'mail_message_identifier,sent_from,sent_to,received_from,'
                    'received_by,event__event_type,event__event_status,'
                    'event__event_registered_on', },
        {'subscription': 'Exchange Failed Send Receive By Bot',
         'template_name': 'mail_failed_events_by_bot',
         'email_subject': 'Exchange failed send receive events for bot',
         'alternate_email_subject': 'No Exchange failed send receive events for'
                                    ' bot ',
         'headers': 'mail_message_identifier,sent_from,sent_to,received_from,'
                    'received_by,event__event_type,event__event_status,'
                    'event__event_registered_on', },
        {'subscription': 'Exchange Failed Send Receive By Site',
         'template_name': 'mail_failed_events_by_site',
         'email_subject': 'Exchange failed send receive events for site',
         'alternate_email_subject': 'No Exchange failed send receive events for'
                                    ' site ',
         'headers': 'mail_message_identifier,sent_from,sent_to,received_from,'
                    'received_by,event__source_host__host_name,'
                    'event__event_type,event__event_status,'
                    'event__event_registered_on', },
        {'subscription': 'Exchange Client Error',
         'template_name': 'event_error',
         'email_subject':'',
         'alternate_email_subject':'',
         'headers': 'uuid,event_message,event_exception,event_body,'
                    'event_registered_on', },
        {'subscription': 'Mail Verification Report',
         'template_name': 'mail_verify_fail',
         'email_subject': 'Email Verification Report',
         'alternate_email_subject': 'Email Verification Report: no data.'
                                    ' Please investigate immediately',
         'headers': 'from_domain,to_domain,site__site,status,last_verified', },
        {'subscription': 'Mail Verification Failures Report',
         'template_name': 'mail_verify_fail',
         'email_subject': 'Email Verification Failures Report',
         'alternate_email_subject': 'Email Verification Failures Report:'
                                    ' no failures',
         'headers': 'from_domain,to_domain,site__site,status,last_verified', },
        {'subscription': 'Exchange bot no site',
         'template_name': 'unconfigured_bots',
         'email_subject': '',
         'alternate_email_subject': '',
         'headers': 'url_annotate,host_name,site__site,excgh_last_verified', },
    ]

    ssl_subs = [
        {'subscription': 'SSL Report',
         'template_name': 'ssl_cert_email',
         'email_subject': '',
         'alternate_email_subject': '',
         'headers': 'common_name,issuer__is_trusted,issuer__common_name,'
                    'port__port,hostnames,expires_in_x_days,not_before,'
                    'not_after', },
        {'subscription': 'Expired SSL Report',
         'template_name': 'ssl_cert_email',
         'email_subject': '',
         'alternate_email_subject': '',
         'headers': 'common_name,issuer__is_trusted,issuer__common_name,'
                    'port__port,hostnames,has_expired_x_days_ago,'
                    'not_before,not_after', },
        {'subscription': 'Invalid SSL Report',
         'template_name': 'ssl_cert_email',
         'email_subject': '',
         'alternate_email_subject': '',
         'headers': 'common_name,issuer__is_trusted,issuer__common_name,'
                    'port__port,hostnames,will_become_valid_in_x_days,'
                    'not_before,not_after', },
    ]

    for subscription in citrix_subs + ldap_subs + mail_subs + ssl_subs:
        create_subscription(apps, subscription)


class Migration(migrations.Migration):
    replaces = [
        ('citrus_borg', '0008_populate_subscriptions'),
        ('citrus_borg', '0012_add_failed_logins_report_subscription'),
        ('citrus_borg', '0013_add_failed_login_site_report_subscription'),
        ('ldap_probe', '0002_populate_ldap_bind_creds'),
        ('ldap_probe', '0003_populate_ac_orion_node'),
        ('ldap_probe', '0004_populate_ac_node'),
        ('ldap_probe', '0020_add_error_alert_subscription'),
        ('ldap_probe', '0022_add_ldap_perf_alert_subscription'),
        ('ldap_probe', '0023_add_subscriptions_ldap_summary_reports'),
        ('ldap_probe', '0025_ldap_perf_reports_subs'),
        ('ldap_probe', '0027_err_reports_subs'),
        ('ldap_probe', '0029_nono_adnodes_rep_subs'),
        ('ldap_probe', '0031_orion_adnodes_rep_subs'),
        ('ldap_probe', '0036_subs_perf_reps'),
        ('ldap_probe', '0037_delete_old_perf_subs'),
        ('mail_collector', '0016_add_subscriptions'),
        ('mail_collector', '0017_add_mail_function_subscriptions'),
        ('mail_collector', '0019_subscriptions_mail_bots'),
        ('mail_collector', '0022_add_subs_bot_site'),
        ('mail_collector', '0024_subscription_exc_events_sr_site'),
        ('mail_collector', '0026_subscription_exc_evts_bot'),
        ('mail_collector', '0028_subscription_exc_fail_evts_bot'),
        ('mail_collector', '0029_subscription_exc_fail_evts_site'),
        ('mail_collector', '0030_subscription_failed_events'),
        ('mail_collector', '0039_add_subscription_mail_verification_report'),
        ('mail_collector', '0040_add_subscription_unconfig_bots'),
    ]

    dependencies = [('p_soc_auto_base', '0001_beats')]

    operations = [
        migrations.RunPython(populate_subscriptions)
    ]
