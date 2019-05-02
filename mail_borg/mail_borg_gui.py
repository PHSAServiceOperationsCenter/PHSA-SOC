'''
Created on Apr 30, 2019

@author: serban
'''
import PySimpleGUI as gui
import time

from datetime import datetime, timedelta

from config import load_config

# form that doen't block
# good for applications with an loop that polls hardware


gui.SetOptions(font='Any 12')


def get_window():
    """
    :returns: the main window for the program
    """
    config = load_config()

    window = gui.Window(
        config.get('app_name'),
        auto_size_buttons=True, use_default_focus=False)

    left_frame = [
        [gui.Button('Run Mail Check', key='mailcheck', font='Any 10'),
         gui.Button('Start Auto-run', key='run', font='Any 10'),
         gui.Button('Pause Auto-run', key='pause', font='Any 10'), ],
        [gui.Text('',  key='status',
                  size=(40, 1),  justification='left'), ],
        [gui.Multiline(size=(40, 20), disabled=True, autoscroll=True), ], ]

    conf_labels_col = [
        [gui.Text('Check Email Every:', justification='left', font='Any 10'), ],
        [gui.Text('Domain:', justification='left', font='Any 10'), ],
        [gui.Text('User Name:', justification='left', font='Any 10'), ],
        [gui.Text('Password:', justification='left', font='Any 10'), ],
        [gui.Text('Mail Addresses:', size=(None, 3),
                  justification='left', font='Any 10'), ],
        [gui.Text('Witness Addresses:',
                  size=(None, 3), justification='left', font='Any 10'), ],
        [gui.Text('Mail Subject', size=(None, 3),
                  justification='left', font='Any 10'), ],
        [gui.Text('Application Name:', justification='left', font='Any 10'), ],
        [gui.Text('Verify Email MX Address Timeout:',
                  justification='left', font='Any 10'), ],
        [gui.Text('Minimum Wait for Check Receive:',
                  justification='left', font='Any 10'), ],
        [gui.Text('Increment Wait for Check Receive:',
                  justification='left', font='Any 10'), ],
        [gui.Text('Check Receive Timeout:',
                  justification='left', font='Any 10'), ],
        [gui.Text('Originating Site:', justification='left', font='Any 10'), ],
        [gui.Text('Additional Email Tags:',
                  size=(None, 3), justification='left', font='Any 10'), ], ]

    conf_values_col = [
        [gui.InputText(config.get('mail_every_minutes'),
                       key='mail_every_minutes', size=(30, 1),
                       do_not_clear=True, font='Any 10'), ],
        [gui.InputText(config.get('domain'), key='domain',
                       size=(30, 1), do_not_clear=True, font='Any 10'), ],
        [gui.InputText(config.get('username'), key='username',
                       size=(30, 1), do_not_clear=True, font='Any 10'), ],
        [gui.InputText(config.get('password'), key='password',
                       size=(30, 1), do_not_clear=True, password_char='*', font='Any 10'), ],
        [gui.Listbox(config.get('email_addresses'),
                     size=(30, 3), auto_size_text=True,
                     key='email_addresses', font='Any 10'), ],
        [gui.Listbox(config.get('witness_addresses'),
                     key='witness_addresses',
                     size=(30, 3), auto_size_text=True, font='Any 10'), ],
        [gui.Multiline(config.get('email_subject'), key='email_subject',
                       size=(30, 3), auto_size_text=True,
                       do_not_clear=True, font='Any 10'), ],
        [gui.InputText(config.get('app_name'), key='app_name',
                       size=(30, 1), do_not_clear=True, font='Any 10'), ],
        [gui.InputText(config.get('check_mx_timeout'), key='check_mx_timeout',
                       size=(30, 1), do_not_clear=True, font='Any 10'), ],
        [gui.InputText(config.get('app_name'), key='app_name',
                       size=(30, 1), do_not_clear=True, font='Any 10'), ],
        [gui.InputText(config.get('app_name'), key='app_name',
                       size=(30, 1), do_not_clear=True, font='Any 10'), ],
        [gui.InputText(config.get('app_name'), key='app_name',
                       size=(30, 1), do_not_clear=True, font='Any 10'), ],
        [gui.InputText(config.get('app_name'), key='app_name',
                       size=(30, 1), do_not_clear=True, font='Any 10'), ],
        [gui.Multiline(config.get('tags'), key='tags',
                       size=(30, 3), auto_size_text=True,
                       do_not_clear=True, font='Any 10'), ],
    ]

    right_frame = [
        [
            gui.Checkbox('Load Configuration from Server',
                         default=config.get(
                             'use_server_config'),
                         key='use_server_config', font='Any 10'),
            gui.Checkbox('Debug', default=config.get(
                'debug'), key='debug', font='Any 10'),
            gui.Checkbox('Auto-run',
                         default=config.get('autorun'), key='autorun', font='Any 10'), ],
        [gui.Column(conf_labels_col), gui.Column(conf_values_col)]
    ]

    layout = [
        [
            gui.Frame('Execution', left_frame, title_color='darkblue'),
            gui.Frame('Configuration', right_frame, title_color='darkblue'),

        ],
    ]
    window.Layout(layout).Finalize()

    return window


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


def main():
    """
    the main function
    """
    window = get_window()

    next_run_at = datetime.now() + \
        timedelta(minutes=int(window.FindElement('mail_every_minutes').Get()))

    paused = False
    while True:
        event, values = window.Read(timeout=0)

        if values is None or event == 'Exit':
            break

        if event == 'pause':
            paused = True
            window.FindElement('status').Update('mail check is paused')
            window.FindElement('pause').Update(disabled=True)
            window.FindElement('run').Update(disabled=False)

        if event == 'run':
            paused = False
            window.FindElement('run').Update(disabled=True)
            window.FindElement('pause').Update(disabled=False)

        if not paused:
            window.FindElement('status').Update(
                'next mail check run in {}'.format(next_run_in(next_run_at)))

            if next_run_at <= datetime.now():
                window.FindElement('status').Update('running mail check')
                time.sleep(10)
                next_run_at = datetime.now() + \
                    timedelta(minutes=int(window.FindElement(
                        'mail_every_minutes').Get()))

            time.sleep(1)

    # Broke out of main loop. Close the window.
    window.Close()


main()
