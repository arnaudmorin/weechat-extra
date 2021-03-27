# -*- coding: utf-8 -*-
# vim:set shiftwidth=4 tabstop=4 softtabstop=4 expandtab textwidth=250:

import weechat
import requests
from collections import deque

# script variables
SCRIPT_NAME = "link"
SCRIPT_AUTHOR = "Arnaud Morin <arnaud.morin@gmail.com>"
SCRIPT_VERSION = "0.0.1"
SCRIPT_LICENSE = "APACHE2"
SCRIPT_DESC = "Send chat links to notification-queue system"

link_config_file = None
link_config_section = {}
link_config_option = {}
link_logs = {}


def link_config_init():
    """ Initialize config file: create sections and options in memory. """
    global link_config_file, link_config_section, link_config_option

    # This will create link.conf file
    link_config_file = weechat.config_new(SCRIPT_NAME, "link_config_reload_cb", "")
    if not link_config_file:
        return

    # link section
    link_config_section["link"] = weechat.config_new_section(
        link_config_file, "link", 0, 0, "", "", "", "", "", "", "", "", "", "")

    link_config_option["endpoint"] = weechat.config_new_option(
        link_config_file, link_config_section["link"],
        "endpoint", "string", "Endpoint URL where links are sent", "", 0, 0,
        "https://example.org/queues/url", "https://example.org/queues/url", 0, "", "", "", "", "", "")
    link_config_option["auth_token"] = weechat.config_new_option(
        link_config_file, link_config_section["link"],
        "auth_token", "string", "X-Auth-Token value", "", 0, 0,
        "token", "token", 0, "", "", "", "", "", "")


def link_config_reload_cb(data, config_file):
    """ Reload config file. """
    return weechat.config_reload(config_file)


def link_config_read():
    """ Read config file. """
    global link_config_file
    return weechat.config_read(link_config_file)


def link_config_write():
    """ Write config file """
    global link_config_file
    return weechat.config_write(link_config_file)


def get_config_value(option):
    """ Get an option """
    global link_config_option
    return weechat.config_string(link_config_option[option])


def link_unload_cb():
    """ Function called when script is unloaded. """
    link_config_write()
    return weechat.WEECHAT_RC_OK


def link_log_cb(data, bufferp, date, tags, is_displayed, is_highlight, prefix, message):
    """Callback when receiving a message
       It will store the http links. Up to five in a deque
    """
    global link_logs
    if message:
        for word in message.split(" "):
            if word.startswith('http'):
                buf_name = weechat.buffer_get_string(bufferp, "name")
                if buf_name not in link_logs.keys():
                    link_logs[buf_name] = deque([], maxlen=5)
                link_logs[buf_name].appendleft(word)

    return weechat.WEECHAT_RC_OK


def link_cmd_cb(data, bufferp, number):
    """Callback function when we want to open a link"""
    global link_logs
    send = False

    # If /link
    if not number:
        number = 1

    buf_name = weechat.buffer_get_string(bufferp, "name")
    try:
        # Number given by callback can be a string
        number = int(number)
        if buf_name in link_logs.keys():
            link = link_logs[buf_name][number - 1]
            send = True
    except Exception:
        pass

    if send:
        headers = {
            'Content-Type': 'application/json',
            'X-Auth-Token': get_config_value('auth_token'),
        }

        requests.post(
            get_config_value('endpoint'),
            data=f"xdg-open {link}",
            headers=headers,
        )

    return weechat.WEECHAT_RC_OK


if __name__ == "__main__":
    if weechat.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION, SCRIPT_LICENSE, SCRIPT_DESC, "link_unload_cb", ""):
        link_config_init()
        link_config_read()
        # Hook privmsg/hilights
        weechat.hook_print("", "", "", 1, "link_log_cb", "")
        weechat.hook_command("link", "Send link to notification",
                             "<number>",
                             " number: link number",
                             "",
                             "link_cmd_cb", "")
