# -*- coding: utf-8 -*-
# vim:set shiftwidth=4 tabstop=4 softtabstop=4 expandtab textwidth=250:

import requests
import weechat

# script variables
SCRIPT_NAME = "notify"
SCRIPT_AUTHOR = "Arnaud Morin <arnaud.morin@gmail.com>"
SCRIPT_VERSION = "0.0.1"
SCRIPT_LICENSE = "APACHE2"
SCRIPT_DESC = "Send notifications from weechat to notification-queue system"


notify_config_file = None
notify_config_section = {}
notify_config_option = {}


def notify_config_init():
    """ Initialize config file: create sections and options in memory. """
    global notify_config_file, notify_config_section, notify_config_option

    # This will create notify.conf file
    notify_config_file = weechat.config_new(SCRIPT_NAME, "notify_config_reload_cb", "")
    if not notify_config_file:
        return

    # notify section
    notify_config_section["notify"] = weechat.config_new_section(
        notify_config_file, "notify", 0, 0, "", "", "", "", "", "", "", "", "", "")

    notify_config_option["nick"] = weechat.config_new_option(
        notify_config_file, notify_config_section["notify"],
        "nick", "string", "Your local nick, to avoid sending notify if message comes from you", "", 0, 0,
        "nickname", "nickname", 0, "", "", "", "", "", "")
    notify_config_option["debug"] = weechat.config_new_option(
        notify_config_file, notify_config_section["notify"],
        "debug", "string", "debug mode (yes/no)", "", 0, 0,
        "no", "no", 0, "", "", "", "", "", "")
    notify_config_option["endpoint"] = weechat.config_new_option(
        notify_config_file, notify_config_section["notify"],
        "endpoint", "string", "Endpoint URL where notifications are sent", "", 0, 0,
        "https://example.org/queues/url", "https://example.org/queues/url", 0, "", "", "", "", "", "")
    notify_config_option["auth_token"] = weechat.config_new_option(
        notify_config_file, notify_config_section["notify"],
        "auth_token", "string", "X-Auth-Token value", "", 0, 0,
        "token", "token", 0, "", "", "", "", "", "")
    notify_config_option["keywords"] = weechat.config_new_option(
        notify_config_file, notify_config_section["notify"],
        "keywords", "string", "Keywords to trigger notify separated with ,", "", 0, 0,
        "word1,word2", "word1,word2", 0, "", "", "", "", "", "")


def notify_config_reload_cb(data, config_file):
    """ Reload config file. """
    return weechat.config_reload(config_file)


def notify_config_read():
    """ Read config file. """
    global notify_config_file
    return weechat.config_read(notify_config_file)


def notify_config_write():
    """ Write config file """
    global notify_config_file
    return weechat.config_write(notify_config_file)


def get_config_value(option):
    """ Get an option """
    global notify_config_option
    return weechat.config_string(notify_config_option[option])


def notify_unload_cb():
    """ Function called when script is unloaded. """
    notify_config_write()
    return weechat.WEECHAT_RC_OK


def debug(message):
    if get_config_value('debug') == 'yes':
        weechat.prnt("", f"[notify] {message}")


# Functions
def notify_show(data, bufferp, date, tags, is_displayed, is_highlight, prefix, message):
    """Callback function when message comes"""
    is_highlight = int(is_highlight)
    is_displayed = int(is_displayed)
    kind = weechat.buffer_get_string(bufferp, "localvar_type")
    notify = weechat.buffer_get_string(bufferp, "localvar_notify")
    nick = get_config_value('nick')
    send = False

    # Discard unwanted stuff
    if prefix == nick:
        debug(f'Message from {nick}, discarding')
        return weechat.WEECHAT_RC_OK

    if notify == "yes":
        # /buffer setvar notify yes
        debug('Message from a notify=yes buffer')
        send = True

    if kind == "private":
        debug('Message from a private buffer')
        send = True

    if kind == "channel":
        for keyword in get_config_value('keywords').split(','):
            if keyword.lower() in message.lower():
                debug('keyword found!')
                send = True

    if send:
        debug('Sending notif!')
        headers = {
            'Content-Type': 'application/json',
            'X-Auth-Token': get_config_value('auth_token'),
        }

        requests.post(
            get_config_value('endpoint'),
            data=f"{prefix}: {message}".encode('utf-8'),
            headers=headers,
        )

    return weechat.WEECHAT_RC_OK


if __name__ == "__main__":
    if weechat.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION, SCRIPT_LICENSE, SCRIPT_DESC, "notify_unload_cb", ""):
        notify_config_init()
        notify_config_read()
        # Hook privmsg/hilights
        weechat.hook_print("", "", "", 1, "notify_show", "")
