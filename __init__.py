"""Support for EnOcean devices."""
import logging
import time

from enocean.communicators.serialcommunicator import SerialCommunicator
from enocean.protocol.packet import Packet, RadioPacket, ResponsePacket
from enocean.protocol import constants as enocean_const
from enocean.utils import combine_hex, from_hex_string
import voluptuous as vol

from homeassistant.const import CONF_DEVICE
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity

from custom_components.enocean.const import *

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema({vol.Required(CONF_DEVICE): cv.string})}, extra=vol.ALLOW_EXTRA
)

SIGNAL_RECEIVE_MESSAGE = "enocean.receive_message"
SIGNAL_SEND_MESSAGE = "enocean.send_message"

def setup(hass, config):
    """Set up the EnOcean component."""
    serial_dev = config[DOMAIN].get(CONF_DEVICE)
    dongle = EnOceanDongle(hass, serial_dev)
    hass.data[DATA_ENOCEAN] = dongle

    return True


class EnOceanDongle:
    """Representation of an EnOcean dongle."""

    def __init__(self, hass, ser):
        """Initialize the EnOcean dongle."""
        self.hass = hass

        #Hack for base_id discover due to callback function
        #create a first communicator without callback
        self.__communicator = SerialCommunicator(port=ser)
        self.__communicator.start()
        base_id = self.__communicator.base_id
        self.__communicator.stop()
        #End Hack


        self.__communicator = SerialCommunicator(port=ser, callback=self.callback)
        self.__communicator.start()
        self.__communicator._base_id = base_id

        self.hass.helpers.dispatcher.dispatcher_connect(
            SIGNAL_SEND_MESSAGE, self._send_message_callback
        )

        _LOGGER.debug("Enocean loaded")

    def _send_message_callback(self, packet):
        """Send a command through the EnOcean dongle.
        packet: RadioPacket object"""
        print(packet)
        self.__communicator.send(packet)

    def callback(self, packet):
        """Handle EnOcean device's callback.

        This is the callback function called by python-enocan whenever there
        is an incoming packet.
        """
        _LOGGER.debug("Get Packet !!!")
        if isinstance(packet, ResponsePacket):
            if packet.data[0] == enocean_const.RETURN_CODE.OK :
                _LOGGER.debug("Response OK")
            if packet.data[0] == enocean_const.RETURN_CODE.ERROR :
                _LOGGER.debug("Response ERROR")

        if isinstance(packet, RadioPacket):
            _LOGGER.debug("Received radio packet: %s", packet)
            self.hass.helpers.dispatcher.dispatcher_send(SIGNAL_RECEIVE_MESSAGE, packet)

    @property
    def device_id(self):
        """Return dongle id"""
        return self.__communicator._base_id

class EnOceanDevice(Entity):
    """Parent class for all devices associated with the EnOcean component."""

    def __init__(self, dev_id, dev_name="EnOcean device"):
        """Initialize the device."""
        self.dev_id = dev_id
        self.dev_name = dev_name

    async def async_added_to_hass(self):
        """Register callbacks."""
        self.hass.helpers.dispatcher.async_dispatcher_connect(
            SIGNAL_RECEIVE_MESSAGE, self._message_received_callback
        )

    def _message_received_callback(self, packet):
        """Handle incoming packets."""

        if packet.sender_int == combine_hex(self.dev_id):
            self.value_changed(packet)

    def value_changed(self, packet):
        """Update the internal state of the device when a packet arrives."""

    def send_command(self, packet):
        """Send a command via the EnOcean dongle."""
        self.hass.helpers.dispatcher.dispatcher_send(SIGNAL_SEND_MESSAGE, packet)
