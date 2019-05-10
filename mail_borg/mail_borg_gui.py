'''
Created on Apr 30, 2019

@author: serban
'''
from datetime import datetime, timedelta
import time

from celery.worker.control import enable_events

import PySimpleGUI as gui
from config import load_config, save_config, load_default_config


# form that doen't block
# good for applications with an loop that polls hardware
gui.SetOptions(font='Any 12')


def get_window():
    """
    :returns: the main window for the program
    """
    config = load_config()

    window = gui.Window(config.get('app_name'),
                        auto_size_buttons=True, use_default_focus=False)

    left_frame = [
        [
            gui.Button('Run Mail Check', key='mailcheck', font='Any 10'),
            gui.Button('Start Auto-run', key='run', font='Any 10'),
            gui.Button('Pause Auto-run', key='pause', font='Any 10'),
        ],
        [
            gui.Text('',  key='status', size=(52, 1),  justification='left'),
        ],
        [
            gui.Multiline(
                size=(52, 26), key='output', disabled=True, autoscroll=True),
        ],
        [
            gui.Text(''),
        ],
        [
            gui.Text('', size=(38, 1)),
            gui.Button('Clear execution data', key='clear', font='Any 10'), ]
    ]

    conf_labels_col = [
        [
            gui.Text('Check Email Every:',
                     justification='left', font='Any 10'),
        ],
        [
            gui.Text('Domain:', justification='left', font='Any 10'),
        ],
        [
            gui.Text('User Name:', justification='left', font='Any 10'),
        ],
        [
            gui.Text('Password:', justification='left', font='Any 10'),
        ],
        [
            gui.Text('Mail Addresses:',
                     size=(None, 3), justification='left', font='Any 10'),
        ],
        [
            gui.Text('Witness Addresses:',
                     size=(None, 3), justification='left', font='Any 10'),
        ],
        [
            gui.Text('Mail Subject',
                     size=(None, 3), justification='left', font='Any 10'),
        ],
        [
            gui.Text('Application Name:', justification='left', font='Any 10'),
        ],
        [
            gui.Text('Verify Email MX Address Timeout:',
                     justification='left', font='Any 10'),
        ],
        [
            gui.Text('Minimum Wait for Check Receive:',
                     justification='left', font='Any 10'),
        ],
        [
            gui.Text('Increment Wait for Check Receive:',
                     justification='left', font='Any 10'),
        ],
        [
            gui.Text('Check Receive Timeout:',
                     justification='left', font='Any 10'),
        ],
        [
            gui.Text('Originating Site:', justification='left', font='Any 10'),
        ],
        [
            gui.Text('Additional Email Tags:',
                     size=(None, 3), justification='left', font='Any 10'),
        ],
    ]

    conf_values_col = [
        [
            gui.Spin([i for i in range(1, 60)],
                     initial_value=config.get('mail_every_minutes'),
                     key='mail_every_minutes',
                     auto_size_text=True, font='Any 10', enable_events=True),
            gui.Text('minutes'),
        ],
        [
            gui.InputText(config.get('domain'), key='domain',
                          size=(32, 1), do_not_clear=True, font='Any 10',
                          enable_events=True),
        ],
        [
            gui.InputText(config.get('username'), key='username',
                          size=(32, 1), do_not_clear=True, font='Any 10',
                          enable_events=True),
        ],
        [
            gui.InputText(config.get('password'), key='password',
                          size=(32, 1), do_not_clear=True, password_char='*',
                          font='Any 10', enable_events=True),
        ],
        [
            gui.Listbox(config.get('email_addresses'), key='email_addresses',
                        size=(32, 3), auto_size_text=True, font='Any 10',
                        enable_events=True),
        ],
        [
            gui.Listbox(config.get('witness_addresses'),
                        key='witness_addresses',
                        size=(32, 3), auto_size_text=True, font='Any 10',
                        enable_events=True),
        ],
        [
            gui.Multiline(config.get('email_subject'), key='email_subject',
                          size=(32, 3), auto_size_text=True,
                          do_not_clear=True, font='Any 10',
                          enable_events=True),
        ],
        [
            gui.InputText(config.get('app_name'), key='app_name',
                          size=(32, 1), do_not_clear=True, font='Any 10',
                          enable_events=True),
        ],
        [
            gui.Spin([i for i in range(1, 20)],
                     initial_value=config.get('check_mx_timeout'),
                     key='check_mx_timeout',
                     auto_size_text=True, font='Any 10', enable_events=True),
            gui.Text('seconds'),
        ],
        [
            gui.Spin([i for i in range(1, 30)],
                     initial_value=config.get('min_wait_receive'),
                     key='min_wait_receive',
                     auto_size_text=True, font='Any 10',
                     enable_events=True),
            gui.Text('seconds'),
        ],
        [
            gui.Spin([i for i in range(1, 10)],
                     initial_value=config.get('step_wait_receive'),
                     key='step_wait_receive',
                     auto_size_text=True, font='Any 10',
                     enable_events=True),
            gui.Text('seconds'),
        ],
        [
            gui.Spin([i for i in range(30, 120)],
                     initial_value=config.get('max_wait_receive'),
                     key='max_wait_receive',
                     auto_size_text=True, font='Any 10',
                     enable_events=True),
            gui.Text('seconds'),
        ],
        [
            gui.InputText(config.get('site'), key='site',
                          size=(32, 1), do_not_clear=True, font='Any 10',
                          enable_events=True),
        ],
        [
            gui.Multiline(config.get('tags'), key='tags',
                          size=(32, 3), auto_size_text=True,
                          do_not_clear=True, font='Any 10',
                          enable_events=True),
        ],
        [gui.Text('')],
        [
            gui.Button('Save configuration', key='save_config',
                       disabled=True, font='Any 10'),
            gui.Button('Reset configuration', key='reset_config',
                       disabled=True, font='Any 10'),
        ]
    ]

    right_frame = [
        [
            gui.Checkbox('Load Configuration from Server',
                         default=config.get('use_server_config'),
                         key='use_server_config', font='Any 10',
                         enable_events=True),
            gui.Checkbox('Debug',
                         default=config.get('debug'), key='debug',
                         font='Any 10', enable_events=True),
            gui.Checkbox('Auto-run',
                         default=config.get('autorun'), key='autorun',
                         font='Any 10', enable_events=True),
        ],
        [
            gui.Column(conf_labels_col), gui.Column(conf_values_col),
        ],
    ]

    layout = [
        [
            gui.Frame('Execution', left_frame, title_color='darkblue'),
            gui.Frame('Configuration', right_frame, title_color='darkblue'),

        ],
    ]

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

    #TODO: implement it, tight now it's just a place-holder
    """
    window.FindElement('run').Update(disabled=True)
    window.FindElement('pause').Update(disabled=True)
    window.FindElement('status').Update('running manual mail check')
    # TODO: here run
    window.FindElement('output').Update(disabled=False)
    window.FindElement('output').Update('{}\n'.format(datetime.now()),
                                        append=True)
    window.FindElement('output').Update(disabled=True)


def do_save_config(window):
    """
    save modified configuration to the ini file and, later on,
    to both the configuration file and the server

    #TODO: right now it's just a place holder
    """
    gui.PopupTimed('save config', auto_close_duration=5)
    window.FindElement('save_config').Update(disabled=True)


def do_reload_config(window):
    """
    abandon live configuration and reload from file or server
    """


def do_reset_config(window):
    """
    reload the default configuration

    #TODO: right now it's just a place holder
    """
    gui.PopupTimed('reset config', auto_close_duration=5)
    do_save_config(window)
    window.FindElement('reset_config').Update(disabled=True)


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


def main():
    """
    the main function
    """
    config_is_dirty = False
    editable = ['use_server_cconfig', 'debug', 'autorun', 'mail_every_minutes',
                'domain', 'username', 'password', 'email_addresses',
                'witness_addresses', 'email_subject', 'app_name',
                'check_mx_timeout', 'min_wait_receive', 'step_wait_receive',
                'max_wait_receive', 'site', 'tags']

    config, window = get_window()

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
            do_save_config(window)

        if event == 'reset_config':
            config_is_dirty = False
            do_reset_config(window)

        if autorun:
            window.FindElement('pause').Update(disabled=False)
            window.FindElement('status').Update(
                'next mail check run in {}'.format(next_run_in(next_run_at)))

            if next_run_at <= datetime.now():
                window.FindElement('pause').Update(disabled=True)
                window.FindElement('mailcheck').Update(disabled=True)
                window.FindElement('status').Update('running mail check')
                mail_check(window)
                next_run_at = datetime.now() + \
                    timedelta(minutes=int(window.FindElement(
                        'mail_every_minutes').Get()))
                window.FindElement('pause').Update(disabled=False)
                window.FindElement('mailcheck').Update(disabled=False)

        if event == 'mailcheck':
            mail_check(window)
            next_run_at = datetime.now() + \
                timedelta(minutes=int(window.FindElement(
                    'mail_every_minutes').Get()))
            if autorun:
                window.FindElement('run').Update(disabled=True)
                window.FindElement('pause').Update(disabled=False)
            else:
                window.FindElement('run').Update(disabled=False)
                window.FindElement('pause').Update(disabled=True)

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
            do_save_config(window)

    window.Close()


main()
