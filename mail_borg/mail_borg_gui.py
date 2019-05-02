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


gui.SetOptions(element_padding=(1, 1))


def get_window():
    """
    :returns: the main window for the program
    """
    config = load_config()

    window = gui.Window(
        config.get('app_name'), auto_size_buttons=True)

    layout = [
        [
            gui.Text(
                '',  key='status',
                size=(30, 1), font=('Helvetica', 20), justification='left'),
            gui.Button('Pause',  font=('Helvetica', 10), pad=(1, 1)),
            gui.Text('Check Email Every:', font=('Helvetica', 20),
                     justification='left'),
            gui.InputText(
                config.get('mail_every_minutes'),
                do_not_clear=True, key='mail_every_minutes'),

        ],
        [
            gui.CloseButton(button_text='Exit',
                            button_color=('white', 'firebrick4')),
        ]
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
        event, values = window.Read(timeout=1)

        if values is None or event == 'Exit':
            break

        if event is 'Pause':
            paused = not paused

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
