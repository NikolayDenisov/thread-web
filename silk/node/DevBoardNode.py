import logging
import os

import silk.config.defaults as defaults
import silk.hw.hw_module as hw_module
from silk.config import wpan_constants as wpan
from silk.device.netns_base import NetnsController
from silk.node.wpantund_base import WpantundWpanNode
from silk.tools import wpan_table_parser
from silk.utils.network import get_local_ip


class DevBoardNode(WpantundWpanNode, NetnsController):
    """
    This class is meant to be used to control wpantund and wpanctl inside of
    network namespaces.
    All inheriting classes require sudo.
    """
    _hw_model = hw_module.HW_NRF52840

    def __init__(self,
                 wpantund_verbose_debug=False,
                 sw_version=None,
                 virtual=False,
                 virtual_name="",
                 device=None,
                 device_path=None):
        self.logger = None
        self.wpantund_logger = None
        # TODO: fix getting netns
        # self.netns = None
        self.netns = 'wpan0'
        self.wpantund_process = None
        self.wpantund_monitor = None
        self.virtual_link_peer = None
        self.sw_version = sw_version
        self.virtual_eth_peer = "v-eth1"
        self.flash_result = False
        self.otns_manager = None

        local_ip = get_local_ip()

        # TODO: Check what platform Silk is running on.
        # This will be addressed by issue ID #32.
        self.wpantund_start_time = 30

        if not virtual and os.geteuid() != 0:
            logging.error("ERROR: {0} requires 'sudo' access" % type(self).__name__)
            raise EnvironmentError

        # Acquire necessary hardware
        self.device = device
        self.device_path = device_path
        # TODO: fix it
        # if self.device is None and self.device_path is None:
        #     if not virtual:
        #         self.get_device(sw_version=sw_version)
        #     else:
        #         self.get_unclaimed_device(virtual_name)
        # super().__init__(self.device.name())

        # self.log_info(f"Device interface: {self.device.interface_serial()}")
        # if not virtual:
        #     self.log_info(f"Device Path: {self.device_path}")
        #
        #     # Setup netns
        #     NetnsController.__init__(self, self.netns, self.device_path)

    #################################
    #   Logging functions
    #################################

    def set_logger(self, parent_logger):
        self.logger = parent_logger.getChild(self.device.name())
        self.wpantund_logger = self.logger.getChild("wpantund")

        self.logger.setLevel(logging.DEBUG)
        self.wpantund_logger.setLevel(logging.DEBUG)

        if self.wpantund_monitor is not None:
            self.wpantund_monitor.logger = self.wpantund_logger

    def log_debug(self, log_line):
        if self.logger is not None:
            self.logger.debug(log_line)

    def log_info(self, log_line):
        if self.logger is not None:
            self.logger.info(log_line)

    def log_warning(self, log_line):
        if self.logger is not None:
            self.logger.warning(log_line)

    def log_error(self, log_line):
        if self.logger is not None:
            self.logger.error(log_line)

    def log_critical(self, log_line):
        if self.logger is not None:
            self.logger.critical(log_line)

    #################################
    #   Handle wpantund and wpanctl
    #################################

    def wpanctl_async(self, action, command, expect, timeout, field=None):
        """Queue a system call into wpanctl inside the network namespace.
        """
        wpanctl_command = defaults.WPANCTL_PATH + f" -I {self.netns} "
        wpanctl_command += command
        self.make_netns_call_async(wpanctl_command, expect, timeout, field)

    def wpanctl(self, action, command, timeout):
        """Make a system call into wpanctl inside the network namespace.
        Return the response
        """
        wpanctl_command = defaults.WPANCTL_PATH + f" -I {self.netns} "
        wpanctl_command += command
        output = self.make_netns_call(wpanctl_command, timeout)
        return output

    def find_ip6_address_with_prefix(self, prefix):
        """Find an IPv6 address on node matching a given prefix.
        `prefix` should be an string containing the prefix.
        Returns a string containing the IPv6 address matching the prefix or
        empty string if no address found.
        """
        if len(prefix) > 2 and prefix[-1] == ":" and prefix[-2] == ":":
            prefix = prefix[:-1]
        all_addrs = wpan_table_parser.parse_list(self.get(wpan.WPAN_IP6_ALL_ADDRESSES))
        matched_addr = [addr for addr in all_addrs if addr.startswith(prefix)]
        return matched_addr[0] if len(matched_addr) >= 1 else ""
