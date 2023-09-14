# -*- coding: utf-8 -*-
# vim:set shiftwidth=4 tabstop=4 softtabstop=4 expandtab textwidth=250:

from collections import deque
import weechat

# script variables
SCRIPT_NAME = "plik"
SCRIPT_AUTHOR = "Arnaud Morin <arnaud.morin@gmail.com>"
SCRIPT_VERSION = "0.0.1"
SCRIPT_LICENSE = "APACHE2"
SCRIPT_DESC = "Send attachments to plik"

plik_config_file = None
plik_config_section = {}
plik_config_option = {}
plik_logs = {}
# Store the current buffer we are in for callback output print
plik_buffer = ""


def plik_config_init():
    """ Initialize config file: create sections and options in memory. """
    global plik_config_file, plik_config_section, plik_config_option

    # This will create plik.conf file
    plik_config_file = weechat.config_new(SCRIPT_NAME, "plik_config_reload_cb", "")
    if not plik_config_file:
        return

    # plik section
    plik_config_section["plik"] = weechat.config_new_section(
        plik_config_file, "plik", 0, 0, "", "", "", "", "", "", "", "", "", "")

    plik_config_option["path"] = weechat.config_new_option(
        plik_config_file, plik_config_section["plik"],
        "path", "string", "Path to plik binary", "", 0, 0,
        "/usr/local/bin/plik", "/usr/local/bin/plik", 0, "", "", "", "", "", "")
    plik_config_option["server"] = weechat.config_new_option(
        plik_config_file, plik_config_section["plik"],
        "server", "string", "server url", "", 0, 0,
        "https://plik.ovh", "https://plik.ovh", 0, "", "", "", "", "", "")
    plik_config_option["token"] = weechat.config_new_option(
        plik_config_file, plik_config_section["plik"],
        "token", "string", "token to talk to server", "", 0, 0,
        "xyz", "xyz", 0, "", "", "", "", "", "")
    plik_config_option["run_link_command"] = weechat.config_new_option(
        plik_config_file, plik_config_section["plik"],
        "run_link_command", "string", "Whether to run or not /link command after plik", "", 0, 0,
        "true", "true", 0, "", "", "", "", "", "")


def plik_config_reload_cb(data, config_file):
    """ Reload config file. """
    return weechat.config_reload(config_file)


def plik_config_read():
    """ Read config file. """
    global plik_config_file
    return weechat.config_read(plik_config_file)


def plik_config_write():
    """ Write config file """
    global plik_config_file
    return weechat.config_write(plik_config_file)


def get_config_value(option):
    """ Get an option """
    global plik_config_option
    return weechat.config_string(plik_config_option[option])


def plik_unload_cb():
    """ Function called when script is unloaded. """
    plik_config_write()
    return weechat.WEECHAT_RC_OK


def plik_log_cb(data, bufferp, date, tags, is_displayed, is_highlight, prefix, message):
    """Callback when receiving a message
       It will store the attachments path. Up to five in a deque
    """
    global plik_logs
    if message:
        # Yes, this is hacky, but this is IT in 2023
        if "An attachment has been saved to" in message:
            words = message.split(" ")
            buf_name = weechat.buffer_get_string(bufferp, "name")
            if buf_name not in plik_logs.keys():
                plik_logs[buf_name] = deque([], maxlen=5)
            plik_logs[buf_name].appendleft(words[-1])

    return weechat.WEECHAT_RC_OK


def plik_action_cb(data, command, return_code, out, err):
    """Callback function when the plik command has been executed"""
    global plik_buffer
    if return_code == weechat.WEECHAT_HOOK_PROCESS_ERROR:
        weechat.prnt(plik_buffer, "Error with plik command")
        return weechat.WEECHAT_RC_OK

    weechat.prnt(plik_buffer, out)

    if get_config_value('run_link_command') == "true":
        weechat.command(plik_buffer, "/link")

    return weechat.WEECHAT_RC_OK


def plik_cmd_cb(data, bufferp, number):
    """Callback function when we want to save an attachment"""
    global plik_logs, plik_buffer
    plik_buffer = bufferp
    send = False

    # If /plik
    if not number:
        number = 1

    buf_name = weechat.buffer_get_string(bufferp, "name")
    try:
        # Number given by callback can be a string
        number = int(number)
        if buf_name in plik_logs.keys():
            plik = plik_logs[buf_name][number - 1]
            send = True
    except Exception:
        pass

    if send:
        command = get_config_value('path') + ' -q --server ' + get_config_value('server') + ' --token ' + get_config_value('token') + ' ' + plik
        # https://weechat.org/files/doc/devel/weechat_plugin_api.en.html#_hook_process
        weechat.hook_process(command, 5000, "plik_action_cb", "")

    return weechat.WEECHAT_RC_OK


if __name__ == "__main__":
    if weechat.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION, SCRIPT_LICENSE, SCRIPT_DESC, "plik_unload_cb", ""):
        plik_config_init()
        plik_config_read()
        # Hook privmsg/hilights
        weechat.hook_print("", "", "", 1, "plik_log_cb", "")
        weechat.hook_command("plik", "Send attachment to plik",
                             "<number>",
                             " number: plik number",
                             "",
                             "plik_cmd_cb", "")
