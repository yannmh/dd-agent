import logging
from os.path import basename

log = logging.getLogger(__name__)


def deprecate_old_command_line_tools(file_name):
    name = basename(file_name)
    if name == 'dd-forwarder' or name == 'dogstatsd' or name == 'dd-agent':
        log.warn("Using this command is deprecated and will be removed in a future version,"
                 " for more information see "
                 "https://github.com/DataDog/dd-agent/wiki/Deprecation-notice--(old-command-line-tools)")
