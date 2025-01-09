import voluptuous as vol

# Import the device class from the component that you want to support
from homeassistant.components.fan import (PLATFORM_SCHEMA, FanEntity, SUPPORT_PRESET_MODE, SUPPORT_SET_SPEED)
import logging
import requests
import json
import re
import math
from typing import Any, Optional

import homeassistant.helpers.config_validation as cv

from datetime import timedelta
from datetime import datetime
from homeassistant.const import (CONF_NAME, CONF_SCAN_INTERVAL, CONF_PASSWORD)
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from homeassistant.util.percentage import ordered_list_item_to_percentage, percentage_to_ordered_list_item
from homeassistant.util.percentage import (
    percentage_to_ranged_value,
    ranged_value_to_percentage,
)

from .const import DOMAIN, CONF_URL, CONF_UUID, CONF_ROOMS, MODEL, SW_VERSION, _ROOMS, SPEED_LIST, SPEED_LOW, SPEED_MID, SPEED_HIGH

_LOGGER = logging.getLogger(__name__)


_ICONS = {
    'off':  'mdi:fan-off',
    'on':   'mdi:fan',
    'low':  'mdi:fan-speed-1',
    'mid':  'mdi:fan-speed-2',
    'high': 'mdi:fan-speed-3',
    'unknown': 'mdi:fan-alert'
}

SCAN_INTERVAL = timedelta(seconds=300)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_URL): cv.string,
    vol.Required(CONF_UUID): cv.string,
    vol.Required(CONF_ROOMS): cv.string,
})

def off2boolean(val):
    if val == 'off' or val == 'unknown':
        return False
    else:
        return True

# For UI
async def async_setup_entry(hass, config_entry, async_add_entities):

    api = hass.data[DOMAIN]["api"][config_entry.entry_id]

    sensors = []

    fan_info = await api._ventilState()

    if fan_info:
        sensors += [ BestinFan('ventil', fan_info['ventil'], api) ]
        async_add_entities(sensors)


class BestinFan(FanEntity):
    def __init__(self, name, state, api):
        self._name      = name
        self._api       = api

        self._state     = state
        self._is_on     = off2boolean(self._state)

        self.data       = {}

    @property
    def unique_id(self):
        """Return the entity ID."""
        return 'fan.bestin_v2_fan'


    @property
    def name(self):
        """Return the name of the sensor, if any."""
        return 'bestin_v2_fan'

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return _ICONS[self._state]

    async def async_update(self):
        """Get the latest state of the sensor."""
        if self._api is None:
            return

        self._state = self._api._fan['ventil']
        self._is_on = off2boolean(self._api._fan['ventil'])


    @property
    def extra_state_attributes(self):
        """Attributes."""
        data = {}

        data['Device Type']  = self._name
        data['Device State'] = self._state

        return data

    @property
    def is_on(self):
        """If the switch is currently on or off."""
        return self._is_on


    async def async_turn_on(self, speed: Optional[str] = None, percentage: Optional[int] = None, preset_mode: Optional[str] = None, **kwargs: Any) -> None:
        """Turn on the fan."""
        await self._api._ventilOnOff(self._name, 'on')

        fan_info = await self._api._ventilState()

        self._is_on  = off2boolean(fan_info['ventil'])

        self._state = fan_info['ventil']

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the fan off."""
        await self._api._ventilOnOff(self._name, 'off')

        fan_info = await self._api._ventilState()

        self._is_on  = off2boolean(fan_info['ventil'])

        self._state = fan_info['ventil']


    async def async_toggle(self, **kwargs: Any) -> None:
        """Toggle the fan."""

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return SUPPORT_SET_SPEED

    @property
    def preset_mode(self):
        """Return the preset mode."""
        return self._state if self._is_on else 'off'

    @property
    def preset_modes(self) -> list:
        """Return the list of available preset modes."""
        return SPEED_LIST

    @property
    def speed_count(self) -> int:
        """Return the number of speeds the fan supports."""
        return len(SPEED_LIST)

    @property
    def percentage(self):
        """Return the current percentage based speed."""
        if self._is_on:
            return ordered_list_item_to_percentage(SPEED_LIST, self._state)

        return None

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""
        #_LOGGER.error(f'[{DOMAIN}] async_set_percentage().percentage, %s', percentage)

        speed_mode = math.ceil(
            percentage_to_ranged_value((1, len(SPEED_LIST)), percentage)
        )

        #_LOGGER.error(f'[{DOMAIN}] async_set_percentage().speed_mode, %s', speed_mode)


    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode of the fan."""

        if self._is_on:
            await self._api._ventilOnOff(self._name, preset_mode)

            fan_info = await self._api._ventilState()

            self._is_on  = off2boolean(fan_info['ventil'])

            self._state = fan_info['ventil']


    async def async_set_direction(self, direction: str) -> None:
        """Set the direction of the fan."""


    @property
    def device_info(self):
        """Return information about the device."""
        return {
            "identifiers": {(DOMAIN, 'etc')},
            'name': 'BESTIN v2 Etc',
            'manufacturer': 'HDC현대산업개발',
            'model': MODEL,
            'sw_version': SW_VERSION
        }
