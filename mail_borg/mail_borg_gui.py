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
import time

from datetime import datetime, timedelta

import PySimpleGUI as gui
from config import (
    load_config, save_config, load_default_config, NOT_A_PASSWORD)
from mailer import WitnessMessages

gui.SetOptions(font='Any 10', button_color=('black', 'lightgrey'))


def get_window():
    """
    :returns: the main window for the program
    """
    config = load_config()

    window = gui.Window(config.get('app_name'),
                        auto_size_buttons=True, use_default_focus=False)

    control_frame = [
        [gui.Text('',  key='status', size=(116, 1),  justification='left'),
         gui.Button('Run Mail Check Now', key='mailcheck'),
            gui.Button('Start Auto-run', key='run'),
            gui.Button('Pause Auto-run', key='pause'), ],

    ]

    output_frame = [
        [gui.Multiline(size=(181, 19), key='output', disabled=True,
                       autoscroll=True, enable_events=True), ],
        [gui.Text('', size=(142, 1)),
         gui.Button('Clear execution data', key='clear'), ]
    ]

    conf_labels_col = [
        [gui.Text('Exchange Server Address', justification='left'), ],
        [gui.Text('Check Email Every', justification='left'), ],
        [gui.Text('Domain:', justification='left'), ],
        [gui.Text('User Name:', justification='left'), ],
        [gui.Text('Password:', justification='left'), ],
        [gui.Text('Mail Subject', size=(None, 3), justification='left'), ],
        [gui.Text('Application Name:', justification='left'), ],
        [gui.Text('Verify Email MX Address Timeout:', justification='left'), ],
        [gui.Text('Minimum Wait for Check Receive:', justification='left'), ],
        [gui.Text('Increment Wait for Check Receive:',
                  justification='left'), ],
        [gui.Text('Check Receive Timeout:', justification='left'), ],
        [gui.Text('Originating Site:', justification='left'), ],
        [gui.Text('Additional Email Tags:',
                  size=(None, 3), justification='left'), ],
    ]

    conf_values_col = [
        [gui.InputText(config.get('exchange_server'), key='exchange_server',
                       size=(32, 1), do_not_clear=True, enable_events=True), ],
        [gui.Spin([i for i in range(1, 60)], key='mail_every_minutes',
                  initial_value=config.get('mail_every_minutes'),
                  auto_size_text=True, enable_events=True),
         gui.Text('minutes'), ],
        [gui.InputText(config.get('domain'), key='domain',
                       size=(32, 1), do_not_clear=True, enable_events=True), ],
        [gui.InputText(config.get('username'), key='username',
                       size=(32, 1), do_not_clear=True, enable_events=True), ],
        [gui.InputText(config.get('password'), key='password',
                       size=(32, 1), do_not_clear=True, password_char='*',
                       enable_events=True), ],

        [gui.Multiline(config.get('email_subject'), key='email_subject',
                       size=(32, 3), auto_size_text=True,
                       do_not_clear=True,  enable_events=True), ],
        [gui.InputText(config.get('app_name'), key='app_name', size=(32, 1),
                       do_not_clear=True,  enable_events=True), ],
        [gui.Spin([i for i in range(1, 20)], key='check_mx_timeout',
                  initial_value=config.get('check_mx_timeout'),
                  auto_size_text=True, enable_events=True),
         gui.Text('seconds'), ],
        [gui.Spin([i for i in range(1, 30)], key='min_wait_receive',
                  initial_value=config.get('min_wait_receive'),
                  auto_size_text=True, enable_events=True),
         gui.Text('seconds'), ],
        [gui.Spin([i for i in range(1, 10)], key='step_wait_receive',
                  initial_value=config.get('step_wait_receive'),
                  auto_size_text=True, enable_events=True),
         gui.Text('seconds'), ],
        [gui.Spin([i for i in range(30, 120)], key='max_wait_receive',
                  initial_value=config.get('max_wait_receive'),
                  auto_size_text=True,  enable_events=True),
         gui.Text('seconds'), ],
        [gui.InputText(config.get('site'), key='site', size=(32, 1),
                       do_not_clear=True, enable_events=True), ],
        [gui.Multiline(config.get('tags'), key='tags', size=(32, 3),
                       auto_size_text=True, do_not_clear=True,
                       enable_events=True), ], ]

    conf_emails_col = [
        [gui.Text('Mail Addresses:',  justification='left'), ],
        [gui.Multiline(config.get('email_addresses'), key='email_addresses',
                       size=(46, 22), auto_size_text=True,
                       do_not_clear=True,  enable_events=True), ], ]
    conf_witness_col = [
        [gui.Text('Witness Addresses:', justification='left'), ],
        [gui.Multiline(config.get('witness_addresses'), size=(46, 22),
                       key='witness_addresses', auto_size_text=True,
                       do_not_clear=True,  enable_events=True), ],
    ]

    right_frame = [
        [gui.Text('', size=(96, 1)),
         gui.Button('Save configuration to file', key='save_config',
                    disabled=True),
         gui.Button('Reload configuration from file', key='reload_config',
                    disabled=True),
         gui.Button('Use default configuration', key='reset_config',
                    disabled=False), ],
        [gui.Checkbox('Load Configuration from Server',
                      default=config.get('use_server_config'),
                      key='use_server_config', enable_events=True),
         gui.Checkbox('Debug', default=config.get('debug'),
                      key='debug', enable_events=True),
         gui.Checkbox('Enable Auto-run on startup', key='autorun',
                      default=config.get('autorun'),  enable_events=True),
         gui.Checkbox('Use ASCII from of email addresses',
                      default=config.get('force_ascii_email'),
                      key='force_ascii_email',  enable_events=True),
         gui.Checkbox('Allow UTF-8 characters in email addresses',
                      default=config.get('allow_utf8_email'),
                      key='allow_utf8_email', enable_events=True),
         gui.Checkbox('Verify email address domain for deliverability',
                      default=config.get('check_email_mx'),
                      key='check_email_mx', enable_events=True), ],
        [gui.Checkbox('Autodiscover the Exchange Server',
                      default=config.get('autodiscover'), key='autodiscover',
                      enable_events=True), ],
        [gui.Column(conf_labels_col), gui.Column(conf_values_col),
         gui.Column(conf_emails_col), gui.Column(conf_witness_col), ], ]

    layout = [
        [gui.Frame('Control',
                   control_frame, title_color='darkblue', font='Any 12'), ],
        [gui.Frame('Configuration',
                   right_frame, title_color='darkblue', font='Any 12'), ],
        [gui.Frame('Output',
                   output_frame, title_color='darkblue', font='Any 12'), ]]

    window.Layout(layout).Finalize()

    return config, window


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


def mail_check(config, window):
    """
    invoke the mail check functionality

    """
    window.FindElement('mailcheck').Update(disabled=True)
    window.FindElement('status').Update('running mail check')
    window.FindElement('output').Update(disabled=False)
    window.FindElement('output').Update(
        '{}: running mail check\n'.format(datetime.now()), append=True)

    witness_messages = WitnessMessages(console_logger=window, **config)
    witness_messages.verify_receive()

    window.FindElement('output').Update(disabled=True)
    window.FindElement('mailcheck').Update(disabled=False)


def do_save_config(config, window):
    """
    save modified configuration to the ini file and, later on,
    to both the configuration file and the server

    """
    window.FindElement('save_config').Update(disabled=True)

    items = []
    for key, val in config.items():
        items.append((key, val))

    save_config(dict_config=collections.OrderedDict(items))

    window.FindElement('save_config').Update(disabled=False)


def do_reload_config(window):
    """
    abandon live configuration and reload from file or server
    """
    config = load_config()
    for key, value in config.items():
        if key in ['log_type', 'evt_log_key', 'msg_dll']:
            # these are not configurable from the GUI
            continue
        window.FindElement(key).Update(value)

    window.FindElement('reload_config').Update(disabled=True)


def do_reset_config(window):
    """
    reload the default configuration

    """
    config = load_default_config()
    for key, value in config.items():
        if key in ['log_type', 'evt_log_key', 'msg_dll']:
            # these are not configurable from the GUI
            continue
        window.FindElement(key).Update(value)

    _dirty_window(window)


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
    window.FindElement('reload_config').Update(disabled=False)


def _do_clear(window):
    window.FindElement('output').Update(disabled=False)
    window.FindElement('output').Update('')
    window.FindElement('output').Update(disabled=True)


def _check_password(window):
    if window.FindElement('password').Get() in [NOT_A_PASSWORD]:
        window.FindElement('password').Update(
            gui.PopupGetText(
                'Please enter the password for the domain account.\n'
                ' Do not forget to save the configuration after providing'
                ' the passwword',
                'Invalid or Unconfigured Password Detected!',
                password_char='*'))
        _dirty_window(window)
        return True

    return False


def main():  # pylint: disable=too-many-branches,too-many-statements
    """
    the main function
    """
    editable = ['use_server_config', 'debug', 'autorun', 'mail_every_minutes',
                'domain', 'username', 'password', 'email_addresses',
                'witness_addresses', 'email_subject', 'app_name',
                'check_mx_timeout', 'min_wait_receive', 'step_wait_receive',
                'max_wait_receive', 'site', 'tags', 'autodiscover',
                'exchange_server', ]

    config, window = get_window()
    config_is_dirty = _check_password(window)
    next_run_at = datetime.now() + \
        timedelta(minutes=int(window.FindElement('mail_every_minutes').Get()))
    autorun = _set_autorun(window)

    while True:
        event, values = window.Read(timeout=0)

        if values is None or event == 'Exit':
            break

        if event in editable:
            config_is_dirty = True
            config[event] = window.FindElement(event).Get()

            _dirty_window(window)

            if event == 'autorun':
                autorun = _set_autorun(window)

            if event == 'mail_every_minutes':
                next_run_at = datetime.now() + \
                    timedelta(
                        minutes=int(
                            window.FindElement('mail_every_minutes').Get()))

        if event == 'save_config':
            config_is_dirty = False
            do_save_config(config, window)

        if event == 'reset_config':
            config_is_dirty = True
            do_reset_config(window)

        if event == 'reload_config':
            config_is_dirty = False
            do_reload_config(window)

        if event == 'clear':
            _do_clear(window)

        if autorun:
            window.FindElement('pause').Update(disabled=False)
            window.FindElement('status').Update(
                'next mail check run in {}'.format(next_run_in(next_run_at)))

            if next_run_at <= datetime.now():
                mail_check(config=config, window=window)
                next_run_at = datetime.now() + \
                    timedelta(minutes=int(window.FindElement(
                        'mail_every_minutes').Get()))

        if event == 'mailcheck':
            mail_check(config=config, window=window)
            next_run_at = datetime.now() + \
                timedelta(minutes=int(window.FindElement(
                    'mail_every_minutes').Get()))

            if autorun:
                window.FindElement('run').Update(disabled=True)
                window.FindElement('pause').Update(disabled=False)
                window.FindElement('status').Update(
                    'next mail check run in {}'.format(next_run_in(next_run_at)))
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
    if config_is_dirty:
        save = gui.PopupYesNo(
            'Save configuration?',
            'There are unsaved changes in the application configuration.'
            ' Do you wish to save them?')

        if save == 'Yes':
            do_save_config(config, window)

    window.Close()


main()
