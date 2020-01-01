"""Support for EnOcean switches."""
import logging

import voluptuous as vol

from enocean.protocol.packet import RadioPacket

from custom_components import enocean

from homeassistant.components.switch import PLATFORM_SCHEMA
from homeassistant.const import CONF_ID, CONF_NAME
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import ToggleEntity

from custom_components.enocean.const import *

_LOGGER = logging.getLogger(__name__)

CONF_EEP = "EEP"
CONF_CHANNEL = "channel"
DEFAULT_NAME = "EnOcean Switch"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_ID): vol.All(cv.ensure_list, [vol.Coerce(int)]),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_CHANNEL, default=0): cv.positive_int,
        vol.Optional(CONF_EEP, default=0): cv.string, #TODO: hex string
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the EnOcean switch platform."""
    channel = config.get(CONF_CHANNEL)
    dev_id = config.get(CONF_ID)
    dev_name = config.get(CONF_NAME)
    dev_eep = config.get(CONF_EEP)

    _LOGGER.debug("Load Switch %s with EEP: %s" % (dev_name, dev_eep))

    add_entities([EnOceanD2(dev_id, dev_name, channel, dev_eep)])

class EnOceanD2(enocean.EnOceanDevice, ToggleEntity):
    """Representation of an EnOcean switch device."""

    def __init__(self, dev_id, dev_name, channel, dev_eep):
        """Initialize the EnOcean switch device."""
        super().__init__(dev_id, dev_name)
        self.dev_eep = dev_eep
        self._light = None
        self._on_state = False
        self._on_state2 = False
        self.channel = channel

    @property
    def is_on(self):
        """Return whether the switch is on or off."""
        return self._on_state

    @property
    def name(self):
        """Return the device name."""
        return self.dev_name

    def turn_on(self, **kwargs):
        """Turn on the switch."""
        packet = RadioPacket.create(rorg=0xD2, rorg_func=0x01, rorg_type=0x0B,
                            sender=self.hass.data[DATA_ENOCEAN].device_id,
                            destination=self.dev_id,
                            CMD=1,
                            OV=1)

        self.send_command(packet)
        self._on_state = True

    def turn_off(self, **kwargs):
        """Turn off the switch."""
        packet = RadioPacket.create(rorg=0xD2, rorg_func=0x01, rorg_type=0x0B,
                            sender=self.hass.data[DATA_ENOCEAN].device_id,
                            destination=self.dev_id,
                            CMD=1,
                            OV=0)

        self.send_command(packet)
        self._on_state = False

    def value_changed(self, packet):
        """Update the internal state of the switch."""
        # if packet.data[0] == 0xA5:
        #     # power meter telegram, turn on if > 10 watts
        #     packet.parse_eep(0x12, 0x01)
        #     if packet.parsed["DT"]["raw_value"] == 1:
        #         raw_val = packet.parsed["MR"]["raw_value"]
        #         divisor = packet.parsed["DIV"]["raw_value"]
        #         watts = raw_val / (10 ** divisor)
        #         if watts > 1:
        #             self._on_state = True
        #             self.schedule_update_ha_state()
        # elif packet.data[0] == 0xD2:
        #     # actuator status telegram
        #     packet.parse_eep(0x01, 0x01)
        #     if packet.parsed["CMD"]["raw_value"] == 4:
        #         channel = packet.parsed["IO"]["raw_value"]
        #         output = packet.parsed["OV"]["raw_value"]
        #         if channel == self.channel:
        #             self._on_state = output > 0
        #             self.schedule_update_ha_state()


# class EnOceanSwitch(enocean.EnOceanDevice, ToggleEntity):
#     """Representation of an EnOcean switch device."""

#     def __init__(self, dev_id, dev_name, channel, dev_eep):
#         """Initialize the EnOcean switch device."""
#         super().__init__(dev_id, dev_name)
#         self.dev_eep = dev_eep
#         self._light = None
#         self._on_state = False
#         self._on_state2 = False
#         self.channel = channel

#     @property
#     def is_on(self):
#         """Return whether the switch is on or off."""
#         return self._on_state

#     @property
#     def name(self):
#         """Return the device name."""
#         return self.dev_name

#     def turn_on(self, **kwargs):
#         """Turn on the switch."""
#         optional = [0x03]
#         optional.extend(self.dev_id)
#         optional.extend([0xFF, 0x00])
#         self.send_command(
#             data=[0xD2, 0x01, self.channel & 0xFF, 0x64, 0x00, 0x00, 0x00, 0x00, 0x00],
#             optional=optional,
#             packet_type=0x01,
#         )
#         self._on_state = True

#     def turn_off(self, **kwargs):
#         """Turn off the switch."""
#         optional = [0x03]
#         optional.extend(self.dev_id)
#         optional.extend([0xFF, 0x00])
#         self.send_command(
#             data=[0xD2, 0x01, self.channel & 0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
#             optional=optional,
#             packet_type=0x01,
#         )
#         self._on_state = False

#     def value_changed(self, packet):
#         """Update the internal state of the switch."""
#         if packet.data[0] == 0xA5:
#             # power meter telegram, turn on if > 10 watts
#             packet.parse_eep(0x12, 0x01)
#             if packet.parsed["DT"]["raw_value"] == 1:
#                 raw_val = packet.parsed["MR"]["raw_value"]
#                 divisor = packet.parsed["DIV"]["raw_value"]
#                 watts = raw_val / (10 ** divisor)
#                 if watts > 1:
#                     self._on_state = True
#                     self.schedule_update_ha_state()
#         elif packet.data[0] == 0xD2:
#             # actuator status telegram
#             packet.parse_eep(0x01, 0x01)
#             if packet.parsed["CMD"]["raw_value"] == 4:
#                 channel = packet.parsed["IO"]["raw_value"]
#                 output = packet.parsed["OV"]["raw_value"]
#                 if channel == self.channel:
#                     self._on_state = output > 0
#                     self.schedule_update_ha_state()
