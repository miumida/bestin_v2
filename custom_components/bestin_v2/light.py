import voluptuous as vol

# Import the device class from the component that you want to support
from homeassistant.components.light import PLATFORM_SCHEMA, LightEntity

import logging
import requests
import json
import re

import homeassistant.helpers.config_validation as cv

from datetime import timedelta
from datetime import datetime
from homeassistant.const import (CONF_NAME, CONF_PASSWORD)
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import Throttle

from .const import DOMAIN, CONF_URL, CONF_UUID, CONF_ROOMS, MODEL, SW_VERSION, _ROOMS


_LOGGER = logging.getLogger(__name__)

_ICONS = {
    'on':  'mdi:lightbulb-on',
    'off': 'mdi:lightbulb'
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_URL): cv.string,
    vol.Required(CONF_UUID): cv.string,
    vol.Required(CONF_ROOMS): cv.string,
})


# For UI
async def async_setup_entry(hass, config_entry, async_add_entities):

    room = hass.data[DOMAIN]["room"][config_entry.entry_id]

    sensors = []

    for r in room:
        for key in room[r]._lights:
            sensors += [ BestinLight(r, key, room[r]._lights[key], room[r]) ]

    async_add_entities(sensors)


class BestinLight(LightEntity):
    def __init__(self, room, name, state, api):
        self._name      = name
        self._room      = room
        self._room_dsc  = _ROOMS[room]
        self._api       = api

        self._state     = state
        self._is_on     = state

        self.data       = {}

    @property
    def unique_id(self):
        """Return the entity ID."""
        return 'light.bestin_v2_{}_light_{}'.format(self._room_dsc, self._name)


    @property
    def name(self):
        """Return the name of the sensor, if any."""
        return 'bestin_v2_{}_light_{}'.format(self._room_dsc, self._name)

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        #return 'mdi:lightbulb' #_ICONS[self._is_on]
        return _ICONS[self._api.isLightOn(self._name)]

    async def async_update(self):
        """Get the latest state of the sensor."""
        if self._api is None:
            return

    @property
    def extra_state_attributes(self):
        """Attributes."""
        data = {}

        data['Device Room']  = self._room_dsc
        data['Device Type']  = self._name
        #data['Device State'] = self._is_on
        data['Device State'] = self._api.isLightOn(self._name)

        return data

    @property
    def is_on(self):
        """If the switch is currently on or off."""
        #return self._is_on
        return self._api.isLightOn(self._name)

    @property
    def state(self):
        """If the switch is currently on or off."""
        #return self._is_on
        return self._api.isLightOn(self._name)


    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        await self._api.lightOn(self._name)

        self._is_on = 'on'

        await self._api.lightState()

        #_LOGGER.error(self._api._lights)

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        await self._api.lightOff(self._name)

        self._is_on = 'off'

        await self._api.lightState()

        #_LOGGER.error(self._api._lights)


    @property
    def device_info(self):
        """Return information about the device."""
        return {
            "identifiers": {(DOMAIN, 'light')},
            'name': 'BESTIN v2 Light',
            'manufacturer': 'HDC현대산업개발',
            'model': MODEL,
            'sw_version': SW_VERSION
        }
