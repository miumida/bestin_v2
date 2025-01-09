import logging
import requests
import voluptuous as vol
import json
import re
import xmltodict

import homeassistant.helpers.config_validation as cv

from datetime import timedelta
from datetime import datetime
from homeassistant.components.button import PLATFORM_SCHEMA, ButtonEntity

from homeassistant.helpers.entity import Entity
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, CONF_URL, CONF_UUID, CONF_ROOMS, MODEL, SW_VERSION, _ROOMS, DT_LIGHT, DT_GAS

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_URL): cv.string,
    vol.Required(CONF_UUID): cv.string,
    vol.Required(CONF_ROOMS): cv.string,
})

async def async_setup_entry(hass, config_entry, async_add_entities):

    sensors = []

    api = hass.data[DOMAIN]["api"][config_entry.entry_id]

    room = hass.data[DOMAIN]["room"][config_entry.entry_id]

    if DT_LIGHT in api._devices:
        for r in room:
            if len(room[r]._lights) > 1:
                btn = RoomLightOffButton(r, api)

                sensors += [btn]

    #gas
    if DT_GAS in api._devices:
        gas = GasCloseButton(api)

        sensors += [gas]

    async_add_entities(sensors)



class GasCloseButton(ButtonEntity):
    # Implement one of these methods.

    def __init__(self, api):
        self._api = api

    @property
    def unique_id(self):
        """Return the entity ID."""
        return 'button.bestin_v2_gas_close'

    @property
    def name(self):
        """Return the name of the sensor, if any."""
        return 'bestin_v2_gas_close'

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return 'mdi:valve-closed'

    async def async_press(self) -> None:
        """Handle the button press."""
        await self._api._gasLock()

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


class RoomLightOffButton(ButtonEntity):
    # Implement one of these methods.

    def __init__(self, room, api):
        self._room     = room
        self._room_dsc = _ROOMS[room]
        self._api      = api

    @property
    def unique_id(self):
        """Return the entity ID."""
        return 'button.bestin_v2_{}_light_off'.format(self._room_dsc)

    @property
    def name(self):
        """Return the name of the sensor, if any."""
        return 'bestin_v2_{}_light_off'.format(self._room_dsc)

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return 'mdi:lightbulb-group-off'

    async def async_press(self) -> None:
        """Handle the button press."""
        await self._api._lightAllOff(self._room)

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
