# Import the device class from the component that you want to support
from homeassistant.components.climate import PLATFORM_SCHEMA, ClimateEntity
from homeassistant.components.climate.const import ( ClimateEntityFeature, HVACMode )

import logging
import requests
import voluptuous as vol
import json
import re
import xmltodict

import homeassistant.helpers.config_validation as cv

from datetime import timedelta
from datetime import datetime
from homeassistant.const import (CONF_NAME, CONF_SCAN_INTERVAL, UnitOfTemperature, ATTR_TEMPERATURE, CONF_PASSWORD)
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, CONF_URL, CONF_UUID, CONF_ROOMS, MODEL, SW_VERSION, _ROOMS, TEMP_STEP

_LOGGER = logging.getLogger(__name__)


MAX_TEMP = 45
MIN_TEMP = 10

TEMP_CELSIUS = UnitOfTemperature.CELSIUS


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_URL): cv.string,
    vol.Required(CONF_UUID): cv.string,
    vol.Required(CONF_ROOMS): cv.string,
})

# For UI
async def async_setup_entry(hass, config_entry, async_add_entities):

    api = hass.data[DOMAIN]["thermostat"][config_entry.entry_id]

    units = api._thermostats

    sensors = []

    for room in units:
        sensors += [ BestinClimate(room, 'thermostat', api.isThermostateOn(room), api.getTargetTemp(room), api.getCurrTemp(room), api) ]

    async_add_entities(sensors)


def cover_list(dict):
    if not dict:
        return []
    elif isinstance(dict, list):
        return dict
    else:
        return [dict]

class BestinClimate(ClimateEntity):
    def __init__(self, room, name, is_on, target_temp, cur_temp, api):
        self._name      = name
        self._room      = room
        self._room_dsc  = room
        self._api       = api

        self._is_on     = HVACMode.OFF if is_on == 'off' else HVACMode.HEAT

        self._cur_temp    = cur_temp
        self._target_temp = target_temp

        self.data       = {}

    @property
    def unique_id(self):
        """Return the entity ID."""
        return f'climate.bestin_v2_{self._room_dsc}_{self._name}'


    @property
    def name(self):
        """Return the name of the sensor, if any."""
        return f'bestin_v2_{self._room_dsc}_{self._name}'

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return 'mdi:thermometer'

    @property
    def current_temperature(self):
        return float(self._cur_temp)

    @property
    def target_temperature(self):
        return float(self._target_temp)

    @property
    def temperature_unit(self):
        """Return the unit of measurement which this thermostat uses."""
        return TEMP_CELSIUS

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return TEMP_STEP

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return MIN_TEMP

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return MAX_TEMP

    @property
    def hvac_modes(self):
        """Return the list of available hvac operation modes.
        Need to be a subset of HVAC_MODES.
        """
        return [HVACMode.OFF, HVACMode.HEAT]

    @property
    def hvac_mode(self):
        """Return hvac operation ie. heat, cool mode.
        Need to be one of HVAC_MODE_*.
        """
        return self._is_on

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        rtn = {}

        if hvac_mode == HVACMode.HEAT:
            await self._api.setHvacMode(self._room, 'on', self._target_temp)
        elif hvac_mode == HVACMode.OFF:
            await self._api.setHvacMode(self._room, 'off', self._target_temp)

        # 호출이후, 상태 반영
        await self._api.thermostatState()

        self._is_on       = HVACMode.OFF if self._api.isThermostateOn(self._room) == 'off' else HVACMode.HEAT
        self._target_temp = self._api.getTargetTemp(self._room)
        self._cur_temp    = self._api.getCurrTemp(self._room)



    @property
    def supported_features(self):
        return ClimateEntityFeature.TARGET_TEMPERATURE

    @property
    def is_on(self):
        """Return true if heater is on."""
        return self._is_on

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""

        if self._is_on == HVACMode.HEAT:

            temperature = kwargs.get(ATTR_TEMPERATURE)

            if temperature is None:
                return

            await self._api.setHvacTemperature(self._room, 'on', temperature, self._cur_temp)

            # 호출이후, 상태 반영
            await self._api.thermostatState()

            self._is_on       = HVACMode.OFF if self._api.isThermostateOn(self._room) == 'off' else HVACMode.HEAT
            self._target_temp = self._api.getTargetTemp(self._room)
            self._cur_temp    = self._api.getCurrTemp(self._room)

    async def async_update(self):
        """Get the latest state of the sensor."""
        if self._api is None:
            return

        #상태 반영
        self._is_on       = HVACMode.OFF if self._api.isThermostateOn(self._room) == 'off' else HVACMode.HEAT
        self._target_temp = self._api.getTargetTemp(self._room)
        self._cur_temp    = self._api.getCurrTemp(self._room)

    @property
    def extra_state_attributes(self):
        """Attributes."""
        data = {}

        data['Device Room']  = self._room_dsc
        data['Device Type']  = self._name

        return data

    @property
    def device_info(self):
        """Return information about the device."""
        return {
            "identifiers": {(DOMAIN, 'thermostat')},
            'name': 'BESTIN v2 Thermostat',
            'manufacturer': 'HDC현대산업개발',
            'model': MODEL,
            'sw_version': SW_VERSION
        }
