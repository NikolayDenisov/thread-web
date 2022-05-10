import datetime
import logging
import os
import re
import time
import traceback


from silk.device.netns_base import NetnsController
from silk.node.wpantund_base import role_is_thread
from silk.node.wpantund_base import WpantundWpanNode

from silk.utils.network import get_local_ip
import silk.hw.hw_module as hw_module
import silk.hw.hw_resource as hw_resource

import silk.config.defaults as defaults
from silk.tools import wpan_table_parser

LOG_PATH = "/opt/openthread_test/results/"
POSIX_PATH = "/opt/openthread_test/posix"
RETRY = 3


class FifteenFourDevBoardNode(WpantundWpanNode, NetnsController):
    """
    This class is meant to be used to control wpantund and wpanctl inside of
    network namespaces.
    All inheriting classes require sudo.
    """

    def __init__(self,
                 wpantund_verbose_debug=False,
                 sw_version=None,
                 virtual=False,
                 virtual_name="",
                 device=None,
                 device_path=None):
        self.logger = None
        self.wpantund_logger = None
        #TODO: fix getting netns
        # self.netns = None
        self.netns = 'wpan0'
        self.wpantund_process = None
        self.wpantund_monitor = None
        self.virtual_link_peer = None
        self.sw_version = sw_version
        self.virtual_eth_peer = "v-eth1"
        self.flash_result = False
        self.otns_manager = None

        self.wpantund_verbose_debug = wpantund_verbose_debug
        self.thread_mode = "NCP"
        if not virtual:
            local_ip = get_local_ip()

            # try:
            #     cluster_list = JsonFile.get_json("clusters.conf")["clusters"]
            #     for cluster in cluster_list:
            #         if cluster["ip"] == local_ip:
            #             self.thread_mode = cluster["thread_mode"]
            # except Exception as error:
            #     logging.info("Cannot load cluster.conf file." f" Running on NCP mode. Error: {error}")

        logging.debug("Thread Mode: {}".format(self.thread_mode))

        # TODO: Check what platform Silk is running on.
        # This will be addressed by issue ID #32.
        self.wpantund_start_time = 30

        if not virtual and os.geteuid() != 0:
            logging.error("ERROR: {0} requires 'sudo' access" % type(self).__name__)
            raise EnvironmentError

        # Acquire necessary hardware
        self.device = device
        self.device_path = device_path
        #TODO: fix it
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
    #   base_node functionality
    #################################

    def set_up(self):
        """
        Set commissioning data to default state.
        Get the piece of hardware required for this test.
        Generate a fake MAC address to use for constructing addresses.
        Create a network namespace for this device.
        Start wpantund in the network namespace.
        """

        self.__stop_wpantund()

        self.log_debug(f"Device Interface Serial: {self.device.interface_serial()}")
        self.log_debug(f"Device Port: {self.device.port()}")

        try:
            self.__start_wpantund(self.thread_mode)
            time.sleep(5)

            self.wpanctl_async("setup", "getprop NCP:HardwareAddress", "[0-9a-fA-F]{16}", 1, self.wpan_mac_addr_label)
        except (RuntimeError, ValueError) as e:
            self.logger.critical(e.message)
            self.logger.debug(f"Cannot start wpantund on {self.netns}")

        NetnsController.__init__(self, self.netns, self.device_path)

        self.thread_interface = self.netns
        self.legacy_interface = self.netns + "-L"
        self.leave()

    def tear_down(self):
        """
        Stop wpantund in this network namespace.
        Stop all PIDs running in this network namespace.
        Free the hardware device resource.
        """
        if self.virtual_link_peer is not None:
            self.virtual_link_peer.tear_down()

        # Added leave to help avoiding NCP init issue
        self.leave()
        time.sleep(3)

        self.__stop_wpantund()
        if self.otns_manager is not None:
            self.otns_manager.remove_node(self)
        self.cleanup_netns()
        self.free_device()
        time.sleep(10)

    #################################
    #   wpan_node functionality
    #################################

    def _get_addr(self, cmd):
        if role_is_thread(self.role):
            # Get the colon-separated thread prefix
            fabric_id = self.get_data("fabric-id")

            # Get the MAC that was generated earlier
            wpan_mac = self.wpan_mac_addr

            # Add the address
            self.add_ip6_addr(fabric_id, "0006", wpan_mac, self.thread_interface, self.ip6_thread_ula_label)

            # Get the link-local address
            wpanctl_command = "get IPv6:LinkLocalAddress"
            self.wpanctl_async("Wpanctl get", wpanctl_command, self._ip6_lla_regex, 1, self.ip6_lla_label)

            # Get the mesh-local address
            wpanctl_command = "get IPv6:MeshLocalAddress"
            self.wpanctl_async("Wpanctl get", wpanctl_command, self._ip6_mla_regex, 1, self.ip6_mla_label)

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
        print('wpanctl')
        wpanctl_command = defaults.WPANCTL_PATH + f" -I {self.netns} "
        wpanctl_command += command
        output = self.make_netns_call(wpanctl_command, timeout)
        return output

    _hw_model = hw_module.HW_NRF52840

    def get_device(self, name=None, sw_version=None):
        """Find an unused dev board, or other hardware.
        """
        try:
            self.device = hw_resource.global_instance().get_hw_module(hw_module.HW_NRF52840,
                                                                      name=name,
                                                                      sw_version=sw_version)
            self.hwModel = hw_module.HW_NRF52840
        except Exception:
            try:
                self.device = hw_resource.global_instance().get_hw_module(hw_module.HW_EFR32,
                                                                          name=name,
                                                                          sw_version=sw_version)
                self.hwModel = hw_module.HW_EFR32
            except Exception as error:
                self.log_critical("Cannot find nRF52840 or efr32 Dev. board!! Error: %s" % error)

        self.device_path = self.device.port()

if __name__ == '__main__':
    scan_result = []
    scanner = FifteenFourDevBoardNode()
    scan_result.append(wpan_table_parser.parse_scan_result(scanner.get_active_scan(15)))
    print(scan_result)
