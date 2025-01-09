import logging
import requests
import voluptuous as vol
import json
import re
import xmltodict
import async_timeout

import homeassistant.helpers.config_validation as cv

from datetime import timedelta
from datetime import datetime
from homeassistant.components.switch import PLATFORM_SCHEMA, SwitchEntity
from homeassistant.const import (CONF_NAME, CONF_PASSWORD)
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, CONF_URL, CONF_UUID, CONF_ROOMS, MODEL, SW_VERSION, _ROOMS, DT_GAS, DT_OUTLET

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_URL): cv.string,
    vol.Required(CONF_UUID): cv.string,
    vol.Required(CONF_ROOMS): cv.string,
})

_V_ICONS = {
    'on' : 'mdi:valve-open',
    'off': 'mdi:valve-closed',
}


# For UI
async def async_setup_entry(hass, config_entry, async_add_entities):

    sensors = []

    api = hass.data[DOMAIN]["api"][config_entry.entry_id]

    room = hass.data[DOMAIN]["room"][config_entry.entry_id]

    #= debug ===============================================================
    sensors += [BestinDebugSwitch(api)]


    #= outlet START ========================================================
    if DT_OUTLET in api._devices:
        for r in room:
            if r == 'l': continue

            for key in room[r]._outlets:
                #standby power switch
                #if (key == 'switch1') and ('/' in room[r]._outlets[key]):
                # 대기전력 차단 스위치
                sensors += [BestinOutletSwitch(r, key, room[r]._outlets[key], room[r], True)]

                sensors += [BestinOutletSwitch(r, key, room[r]._outlets[key], room[r])]
    #= outlet END ==========================================================


    #= gas START ===========================================================
    if DT_GAS in api._devices:
        await api._gasState()

        sensors += [BestinGasSwitch(api)]
    #= gas END =============================================================

    async_add_entities(sensors)


def cover_list(dict):
    if not dict:
        return []
    elif isinstance(dict, list):
        return dict
    else:
        return [dict]

def open2on(val):
    if val == 'open':
        return 'on'
    else:
        return 'off'

class BestinGasSwitch(SwitchEntity):
    def __init__(self, api):
        self._api       = api

        self._state     = open2on(self._api._gas['gas1'])
        self._is_on     = open2on(self._api._gas['gas1'])

        self.data       = {}

    @property
    def unique_id(self):
        """Return the entity ID."""
        return 'switch.bestin_v2_gas'


    @property
    def name(self):
        """Return the name of the sensor, if any."""
        return 'bestin_v2_gas'

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return _V_ICONS[self._is_on]

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._is_on

    async def async_update(self):
        """Get the latest state of the sensor."""
        if self._api is None:
            return

        self._state     = open2on(self._api._gas['gas1'])
        self._is_on     = open2on(self._api._gas['gas1'])


    @property
    def extra_state_attributes(self):
        """Attributes."""
        data = {}

        data['Device Type']  = 'gas'
        data['Device State'] = self._is_on

        return data

    @property
    def is_on(self):
        """If the switch is currently on or off."""
        return self._is_on

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        self._is_on = 'off'
        self._state = 'off'

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        await self._api._gasLock()

        self._state     = open2on(self._api._gas['gas1'])
        self._is_on     = open2on(self._api._gas['gas1'])


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

class BestinGaslockSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, api):
        super().__init__(coordinator)

        self._api       = api

        self._state     = 'on' if self._api._gas['gas1'] == 'open' else 'off'
        self._is_on     = 'on' if self._api._gas['gas1'] == 'open' else 'off'

        self.data       = {}

        dt = datetime.now()
        self._syncdate = dt.strftime("%Y-%m-%d %H:%M:%S")

    @property
    def unique_id(self):
        """Return the entity ID."""
        return 'switch.bestin_v2_gaslock'


    @property
    def name(self):
        """Return the name of the sensor, if any."""
        return 'bestin_v2_gaslock'

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return 'mdi:lock' if self._is_on == 'off' else 'mdi:lock-open-variant'

    @property
    def state(self):
        """Return the state of the sensor."""
        return open2on(self.coordinator.data['gas1'])

    async def async_update(self):
        """Get the latest state of the sensor."""
        if self._api is None:
            return

        self._state     = open2on(self.coordinator.data['gas1'])
        self._is_on     = open2on(self.coordinator.data['gas1'])


    @property
    def extra_state_attributes(self):
        """Attributes."""
        data = {}

        data['Device Type']  = 'gas'
        data['Device State'] = self._is_on

        return data

    @property
    def is_on(self):
        """If the switch is currently on or off."""
        return open2on(self.coordinator.data['gas1'])

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        self._is_on = open2on(self.coordinator.data['gas1'])
        self._state = open2on(self.coordinator.data['gas1'])

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        await self._api._gasLock()

        self._state     = open2on(self.coordinator.data['gas1'])
        self._is_on     = open2on(self.coordinator.data['gas1'])

#        await self.coordinator.async_request_refresh()

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


class BestinOutletSwitch(SwitchEntity):
    def __init__(self, room, name, state, api, standby=False):
        self._room      = room
        self._room_dsc  = _ROOMS[room]
        self._name      = name
        self._api       = api

        self._standby   = standby

        self._state     = state.split('/')[0] if ('/' in state) else state
        self._is_on     = state.split('/')[1] if ('/' in state) else state

        if self._standby:
            self._is_on = 'on' if state.split('/')[0] == 'set' else 'off'

        self.data       = {}

    @property
    def unique_id(self):
        """Return the entity ID."""
        if self._standby:
            return 'switch.bestin_v2_{}_standby_{}'.format(self._room_dsc, self._name)
        else:
            return 'switch.bestin_v2_{}_{}'.format(self._room_dsc, self._name)


    @property
    def name(self):
        """Return the name of the sensor, if any."""
        if self._standby:
            return 'bestin_v2_{}_standby_{}'.format(self._room_dsc, self._name)
        else:
            return 'bestin_v2_{}_{}'.format(self._room_dsc, self._name)

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return 'mdi:power-socket-eu'

    async def async_update(self):
        """Get the latest state of the sensor."""
        if self._api is None:
            return

    @property
    def extra_state_attributes(self):
        """Attributes."""
        data = {}

        data['Device Room']   = self._room
        data['Device Type']   = self._name
        data['Device State']  = self._api.isOutletOn(self._name)

        return data

    @property
    def is_on(self):
        """If the switch is currently on or off."""
        state = self._api.isOutletOn(self._name)

        if self._standby:
            value = 'on' if state.split('/')[0] == 'set' else 'off'
        else:
            value = state.split('/')[1] if ('/' in state) else state

        return value

    @property
    def state(self):
        """If the switch is currently on or off."""
        state = self._api.isOutletOn(self._name)

        if self._standby:
            value = 'on' if state.split('/')[0] == 'set' else 'off'
        else:
            value = state.split('/')[1] if ('/' in state) else state

        return value


    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        if self._standby:
            await self._api.outletSet(self._name)
        else:
            await self._api.outletOn(self._name)

        await self._api.outletState()

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        if self._standby:
            await self._api.outletUnset(self._name)
        else:
            await self._api.outletOff(self._name)

        await self._api.outletState()

    @property
    def device_info(self):
        """Return information about the device."""
        return {
            "identifiers": {(DOMAIN, 'outlet')},
            'name': 'BESTIN v2 Outlet',
            'manufacturer': 'HDC현대산업개발',
            'model': MODEL,
            'sw_version': SW_VERSION
        }


class BestinDebugSwitch(SwitchEntity):
    def __init__(self, api):
        self._api       = api

        self._state     = 'on' if api._debug else 'off'
        self._is_on     = 'on' if api._debug else 'off'

    @property
    def unique_id(self):
        """Return the entity ID."""
        return 'switch.bestin_v2_debug'


    @property
    def name(self):
        """Return the name of the sensor, if any."""
        return 'bestin_v2_debug'

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return 'mdi:math-log'

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._is_on

    def turn_on(self, **kwargs):
        """Turn the switch on."""
        self._api._debugOn()
        self._is_on = 'on' if self._api._debug else 'off'
        self._state = 'on' if self._api._debug else 'off'

    def turn_off(self, **kwargs):
        """Turn the switch off."""
        self._api._debugOff()
        self._is_on = 'on' if self._api._debug else 'off'
        self._state = 'on' if self._api._debug else 'off'

    @property
    def is_on(self):
        """If the switch is currently on or off."""
        return self._is_on


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

