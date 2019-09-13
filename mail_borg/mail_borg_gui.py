"""
.. _mail_borg_gui:

GUI module for exchange monitoring borg bot software

:module:    mail_borg.mail_borg_gui

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    apr. 30, 2019

"""
import collections
from datetime import datetime, timedelta
from queue import Queue
import sys
import threading
import time

import PySimpleGUI as gui
from config import (
    load_config, load_base_configuration, WIN_EVT_CFG, HTTP_PROTO,
    save_base_configuration, reset_base_configuration, INI_DEFAULTS,
)
from mailer import WitnessMessages


gui.SetOptions(font='Any 10', button_color=('black', 'lightgrey'))


def get_window():
    """
    :returns: the main window for the program
    """
    config = load_config()
    base_config = load_base_configuration()

    window = gui.Window(WIN_EVT_CFG.get('app_name'),
                        auto_size_buttons=True, use_default_focus=False)

    control_frame = [
        [gui.Text('',  key='status', size=(133, 1),  justification='left'),
         gui.Button('Run Mail Check Now', key='mailcheck'),
            gui.Button('Start Auto-run', key='run'),
            gui.Button('Pause Auto-run', key='pause'), ],

    ]

    output_frame = [
        [gui.Multiline(size=(200, 10), key='output', disabled=True,
                       autoscroll=True, enable_events=True), ],
        [gui.Text('', size=(161, 1)),
         gui.Button('Clear execution data', key='clear'), ]
    ]

    conf_labels_col = [
        [gui.Checkbox(
            'Enable Auto-run on startup', key='autorun',  enable_events=True,
            default=config.get('exchange_client_config').get('autorun')), ],
        [
            gui.Checkbox(
                'Debug', default=config.get('exchange_client_config').get('debug'),
                key='debug', enable_events=True),
            gui.Checkbox(
                'Verify MX deliverability',
                default=config.get('exchange_client_config').get('check_mx'),
                key='check_mx', enable_events=True),
        ],
        [gui.Text('Verify MX Timeout:', justification='left'), ],
        [gui.Text('Minimum Wait for Check Receive:', justification='left'), ],
        [gui.Text('Multiply Factor for Check Receive:',
                  justification='left'), ],
        [gui.Text('Check Receive Timeout:', justification='left'), ],
        [gui.Text('Originating Site:', justification='left'), ],
        [gui.Text('Mail Subject:', size=(None, 1), justification='left'), ],
        [gui.Multiline(config.get(
            'exchange_client_config').get('email_subject'),
            key='email_subject', size=(32, 3), auto_size_text=True,
            do_not_clear=True,  enable_events=True), ],
    ]

    conf_values_col = [
        [gui.Text('Check Email Every', justification='left'),
         gui.Spin(
            [i for i in range(1, 60)], key='mail_check_period',
            initial_value=config.get(
                'exchange_client_config').get('mail_check_period'),
            size=(3, 1), enable_events=True),
         gui.Text('minutes'), ],
        [gui.Checkbox(
            'Force ASCII email',
            default=config.get('exchange_client_config').get('ascii_address'),
            key='ascii_address',  enable_events=True),
         gui.Checkbox(
             'UTF-8 addresses',
            default=config.get('exchange_client_config').get('utf8_email'),
            key='utf8_email', enable_events=True), ],
        [gui.Spin(
            [i for i in range(1, 20)], key='check_mx_timeout',
            initial_value=config.get(
                'exchange_client_config').get('check_mx_timeout'),
            size=(3, 1), enable_events=True),
         gui.Text('seconds'), ],
        [gui.Spin(
            [i for i in range(1, 120)], key='min_wait_receive',
            initial_value=config.get(
                'exchange_client_config').get('min_wait_receive'),
            size=(3, 1), enable_events=True),
         gui.Text('seconds'), ],
        [gui.Spin(
            [i for i in range(1, 10)], key='backoff_factor',
            initial_value=config.get(
                'exchange_client_config').get('backoff_factor'),
            size=(3, 1), enable_events=True), ],
        [gui.Spin(
            [i for i in range(1, 600)], key='max_wait_receive',
            initial_value=config.get(
                'exchange_client_config').get('max_wait_receive'),
            size=(3, 1),  enable_events=True),
         gui.Text('seconds'), ],
        [gui.InputText(config.get('site').get('site'), key='site', size=(32, 1),
                       disabled=True), ],
        [gui.Text('Additional Email Tags:',
                  size=(None, 1), justification='left'), ],
        [gui.Multiline(config.get(
            'exchange_client_config').get('tags'), key='tags', size=(32, 3),
            auto_size_text=True, do_not_clear=True,
            enable_events=True), ], ]

    conf_emails_col = [
        [gui.Text('Exchange Accounts:',  justification='left'), ],
        [gui.Table(
            [[None, None, None, None, None, None]],
            headings=['domain', 'username', 'password', 'smtp',
                      'autodiscover', 'autodiscover server'], key='exc_accs',
            auto_size_columns=True, display_row_numbers=True), ],
        [gui.Text('Witness Addresses:', justification='left'), ],
        [gui.Multiline(
            ', '.join(
                config.get('exchange_client_config').get('witness_addresses')),
            size=(96, 1), key='witness_addresses', disabled=True), ], ]

    config_frame = [
        [gui.Checkbox('Load Config from Server',
                      default=base_config.get('use_cfg_srv'),
                      key='use_cfg_srv', enable_events=True),
         gui.Text('Config Server Address', justification='left'),
         gui.InputText(base_config.get('cfg_srv_ip'), key='cfg_srv_ip',
                       size=(12, 1), do_not_clear=True, enable_events=True),
         gui.Text('Config Server Port', justification='left'),
         gui.InputText(base_config.get('cfg_srv_port'), key='cfg_srv_port',
                       size=(5, 1), do_not_clear=True, enable_events=True),
         gui.Text('Connection timeout'),
         gui.InputText(base_config.get('cfg_srv_conn_timeout'),
                       key='cfg_srv_conn_timeout', size=(3, 1),
                       do_not_clear=True, enable_events=True),
         gui.Text('Read timeout'),
         gui.InputText(base_config.get('cfg_srv_read_timeout'),
                       key='cfg_srv_read_timeout', size=(3, 1),
                       do_not_clear=True, enable_events=True),
         gui.Text('', size=(39, 1)),
         gui.Button('Save local config', key='save_config',
                    disabled=True),
         gui.Button('Reset local config', key='reset_config',
                    disabled=False), ],
        [gui.Text(config.get('load_status'))],
    ]

    mail_check_frame = [
        [
            gui.Text(
                ('Configuration changes are not preserved across startups.'
                 ' To persist changes, edit the configuration on the server at')),
            gui.InputText(
                '{}://{}:{}/admin/mail_collector/exchangeconfiguration/?q={}'.
                format(
                    HTTP_PROTO, base_config.get('cfg_srv_ip'),
                    base_config.get('cfg_srv_port'),
                    config.get('exchange_client_config').get('config_name')),
                disabled=True, size=(80, 1), key='bot_cfg_url'),
            gui.Button('Refresh config from server', key='reload_config',
                       disabled=False),
        ],
        [
            gui.Column(conf_labels_col),
            gui.Column(conf_values_col),
            gui.Column(conf_emails_col),
        ],
    ]

    layout = [
        [gui.Frame('Control',
                   control_frame, title_color='darkblue', font='Any 12'), ],
        [gui.Frame('Local configuration',
                   config_frame, title_color='darkblue', font='Any 12'), ],
        [gui.Frame('Exchange verification configuration',
                   mail_check_frame, title_color='darkblue', font='Any 12'), ],
        [gui.Frame('Output',
                   output_frame, title_color='darkblue', font='Any 12'), ]]

    window.Layout(layout).Finalize()

    return base_config, config, window


def _accounts_to_table(accounts, window):
    listed_accounts = []

    for account in accounts:

        _account = []
        _account.append(account.get('domain_account').get('domain'))
        _account.append(account.get('domain_account').get('username'))
        _account.append(account.get('domain_account').get('password'))
        _account.append(account.get('smtp_address'))
        _account.append(account.get('exchange_autodiscover'))
        _account.append(account.get('autodiscover_server'))

        listed_accounts.append(_account)

    window.FindElement('exc_accs').Update(listed_accounts)


def next_run_in(next_run_at):
    """
    pretty format for durations

    :arg `datetime.datetime` next_run_at: a moment in time

    :returns:

        the difference between :arg next_run_at: and the value
        of :method:<`datetime.dateime.now`> formatted as minutes and seconds
    """
    mins, secs = divmod((next_run_at - datetime.now()).total_seconds(), 60)
    return '{} minutes, {} seconds'.format(int(mins), int(secs))


def mail_check(config, window, update_window_queue):
    """
    invoke the mail check functionality

    """
    window.FindElement('mailcheck').Update(disabled=True)
    if not window.FindElement('run').Disabled:
        window.FindElement('run').Update(disabled=True)
    if not window.FindElement('pause').Disabled:
        window.FindElement('pause').Update(disabled=True)
    window.FindElement('status').Update('running mail check')
    window.FindElement('output').Update(disabled=False)
    window.FindElement('output').Update(
        '{:%c}: running mail check\n'.format(datetime.now()), append=True)
    window.FindElement('output').Update(disabled=True)

    thr = threading.Thread(target=_mail_check, args=(
        update_window_queue, dict(config)))
    thr.start()


def _mail_check(update_window_queue, config):
    witness_messages = WitnessMessages(
        console_logger=update_window_queue, **config)
    witness_messages.verify_receive()


def do_save_config(window):
    """
    save modified configuration to the ini file and, later on,
    to both the configuration file and the server

    """
    items = [
        ('use_cfg_srv', bool(window.FindElement('use_cfg_srv').Get())),
        ('cfg_srv_ip', window.FindElement('cfg_srv_ip').Get()),
        ('cfg_srv_port', int(window.FindElement('cfg_srv_port').Get())),
        ('cfg_srv_conn_timeout',
         int(window.FindElement('cfg_srv_conn_timeout').Get())),
        ('cfg_srv_read_timeout',
         int(window.FindElement('cfg_srv_read_timeout').Get())),
    ]

    save_base_configuration(dict_config=collections.OrderedDict(items))


def _witness_emails_from_list(witness_emails, window):
    window.FindElement('witness_addresses').Update(', '.join(witness_emails))


def do_reload_config(window):
    """
    abandon live configuration and reload from file or server
    """
    items = [
        ('use_cfg_srv', bool(window.FindElement('use_cfg_srv').Get())),
        ('cfg_srv_ip', window.FindElement('cfg_srv_ip').Get()),
        ('cfg_srv_port', int(window.FindElement('cfg_srv_port').Get())),
        ('cfg_srv_conn_timeout',
         int(window.FindElement('cfg_srv_conn_timeout').Get())),
        ('cfg_srv_read_timeout',
         int(window.FindElement('cfg_srv_read_timeout').Get())),
    ]

    current_base_config = collections.OrderedDict(items)
    config = load_config(current_base_config=current_base_config)

    window.FindElement('bot_cfg_url').Update(
        '{}://{}:{}/admin/mail_collector/mailhost/?q={}'.format(
            HTTP_PROTO, current_base_config.get('cfg_srv_ip'),
            current_base_config.get('cfg_srv_port'),
            config.get('host_name'))
    )
    window.FindElement('autorun').Update(
        config.get('exchange_client_config').get('autorun')
    )
    window.FindElement('debug').Update(
        config.get('exchange_client_config').get('debug')
    )
    window.FindElement('check_mx').Update(
        config.get('exchange_client_config').get('check_mx')
    )
    window.FindElement('email_subject').Update(
        config.get('exchange_client_config').get('email_subject')
    )
    window.FindElement('mail_check_period').Update(
        config.get('exchange_client_config').get('mail_check_period')
    )
    window.FindElement('ascii_address').Update(
        config.get('exchange_client_config').get('ascii_address')
    )
    window.FindElement('utf8_email').Update(
        config.get('exchange_client_config').get('utf8_email')
    )
    window.FindElement('check_mx_timeout').Update(
        config.get('exchange_client_config').get('check_mx_timeout')
    )
    window.FindElement('min_wait_receive').Update(
        config.get('exchange_client_config').get('min_wait_receive')
    )
    window.FindElement('backoff_factor').Update(
        config.get('exchange_client_config').get('backoff_factor')
    )
    window.FindElement('max_wait_receive').Update(
        config.get('exchange_client_config').get('max_wait_receive')
    )
    window.FindElement('site').Update(config.get('site').get('site'))
    window.FindElement('tags').Update(
        config.get('exchange_client_config').get('tags')
    )
    _accounts_to_table(config.get(
        'exchange_client_config').get('exchange_accounts'), window)
    _witness_emails_from_list(
        config.get('exchange_client_config').get('witness_addresses'), window)

    return config


def do_reset_config(window):
    """
    reload the default configuration

    """
    reset_base_configuration()
    base_config = load_base_configuration()
    for key, value in base_config.items():
        window.FindElement(key).Update(value)

    return base_config


def _set_autorun(window):
    autorun = window.FindElement('autorun').Get()
    if autorun:
        window.FindElement('pause').Update(disabled=False)
        window.FindElement('run').Update(disabled=True)
    else:
        window.FindElement('pause').Update(disabled=True)
        window.FindElement('run').Update(disabled=False)
        window.FindElement('status').Update(
            'automated mail check execution is paused')
    return autorun


def _do_pause(window):
    window.FindElement('status').Update(
        'automated mail check execution is paused')
    window.FindElement('pause').Update(disabled=True)
    window.FindElement('run').Update(disabled=False)


def _dirty_window(window):
    window.FindElement('save_config').Update(disabled=False)
    window.FindElement('reset_config').Update(disabled=False)


def _do_clear(window):
    window.FindElement('output').Update(disabled=False)
    window.FindElement('output').Update('')
    window.FindElement('output').Update(disabled=True)


def main():  # pylint: disable=too-many-branches,too-many-statements
    """
    the main function
    """
    if sys.platform != 'win32':
        # me only like windows, booooo
        print('%s will not work on %s' % (__name__, sys.platform))

    editable = ['use_cfg_srv', 'cfg_srv_ip', 'cfg_srv_port',
                'cfg_srv_conn_timeout', 'cfg_srv_conn_timeout']

    update_window_queue = Queue(maxsize=500)
    base_config, config, window = get_window()
    _accounts_to_table(
        config.get('exchange_client_config').get('exchange_accounts'), window)

    config_is_dirty = False
    next_run_at = datetime.now() + \
        timedelta(minutes=int(window.FindElement('mail_check_period').Get()))
    autorun = _set_autorun(window)

    while True:
        event, values = window.Read(timeout=0)

        if values is None or event == 'Exit':
            if config_is_dirty:
                save = gui.PopupYesNo(
                    'Save configuration?',
                    'There are unsaved changes'
                    ' in the application configuration.'
                    ' Do you wish to save them?')

                if save == 'Yes':
                    do_save_config(config)

            break

        while not update_window_queue.empty():
            msg = update_window_queue.get_nowait()
            if msg[0] in ['output']:
                window.FindElement('output').Update(disabled=False)
                window.FindElement('output').Update(msg[1], append=True)
                window.FindElement('output').Update(disabled=True)
                window.FindElement('status').Update('mail check in progress')

            if msg[0] in ['abort']:
                window.FindElement('output').Update(disabled=False)
                window.FindElement('output').Update(
                    '\nmail check aborted\n', append=True)
                window.FindElement('output').Update(disabled=True)
                window.FindElement('status').Update(
                    'mail check aborted. please verify the configuration')
                window.FindElement('autorun').Update(value=False)

            if msg[0] in ['control']:
                window.FindElement('output').Update(disabled=False)
                window.FindElement('output').Update('\nmail check complete\n',
                                                    append=True)
                window.FindElement('output').Update(disabled=True)
                window.FindElement('mail_check_period').Update(disabled=False)
                window.FindElement('mailcheck').Update(disabled=False)
                if autorun:
                    window.FindElement('pause').Update(disabled=False)
                    next_run_at = datetime.now() + \
                        timedelta(minutes=int(window.FindElement(
                            'mail_check_period').Get()))
                    window.FindElement('status').Update(
                        'next mail check run in {}'.format(
                            next_run_in(next_run_at))
                    )
                else:
                    window.FindElement('run').Update(disabled=False)
                    window.FindElement('status').Update(
                        'automated mail check execution is paused')

        if event in editable:
            config_is_dirty = True
            if not isinstance(base_config[event], (bool, int)):
                base_config[event] = window.FindElement(event).Get().\
                    replace('\n', '')
            else:
                base_config[event] = window.FindElement(event).Get()

            _dirty_window(window)

            if event == 'autorun':
                autorun = _set_autorun(window)

            if event == 'mail_check_period':
                next_run_at = datetime.now() + \
                    timedelta(
                        minutes=int(
                            window.FindElement('mail_check_period').Get()))

        if event == 'save_config':
            do_save_config(window)
            window.FindElement('save_config').Update(disabled=True)
            config_is_dirty = False

        if event == 'reset_config':
            base_config = do_reset_config(window)

        if event == 'reload_config':
            config = do_reload_config(window)

        if event == 'clear':
            _do_clear(window)

        if autorun:
            window.FindElement('pause').Update(disabled=False)
            window.FindElement('status').Update(
                'next mail check run in {}'.format(next_run_in(next_run_at)))

            if next_run_at <= datetime.now():
                mail_check(config=config, window=window,
                           update_window_queue=update_window_queue)
                next_run_at = datetime.now() + \
                    timedelta(minutes=int(window.FindElement(
                        'mail_check_period').Get()))

        if event == 'mailcheck':
            mail_check(config=config, window=window,
                       update_window_queue=update_window_queue)
            next_run_at = datetime.now() + \
                timedelta(minutes=int(window.FindElement(
                    'mail_check_period').Get()))

            if autorun:
                window.FindElement('run').Update(disabled=True)
                window.FindElement('pause').Update(disabled=False)
                window.FindElement('status').Update(
                    'next mail check run in {}'.format(
                        next_run_in(next_run_at)))
            else:
                window.FindElement('run').Update(disabled=False)
                window.FindElement('pause').Update(disabled=True)
                window.FindElement('status').Update(
                    'automated mail check execution is paused')

        if event == 'pause':
            autorun = False
            _do_pause(window)

        if event == 'run':
            autorun = True
            window.FindElement('run').Update(disabled=True)
            window.FindElement('pause').Update(disabled=False)
            window.FindElement('status').Update(
                'next mail check run in {}'.format(next_run_in(next_run_at)))

        time.sleep(1)

    # Broke out of main loop. Close the window.

    window.Close()


main()
