""" Bestin v2 """
import logging
import asyncio
import voluptuous as vol

import homeassistant.helpers.config_validation as cv

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.core import HomeAssistant

from datetime import timedelta
from datetime import datetime
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (CONF_NAME, CONF_SCAN_INTERVAL, CONF_PASSWORD)
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import Throttle

from .const import DOMAIN, CONF_URL, CONF_UUID, CONF_ROOMS, DT_LIGHT, DT_OUTLET, DT_CLIMATE, DT_FAN, DT_GAS, DT_ENERGY
from .bestinAPIv2 import BestinAPIv2 as API
from .bestinAPIv2 import BestinRoom
from .bestinAPIv2 import BestinThermostat

PLATFORMS = ['sensor', 'light', 'climate', 'switch', 'fan', 'button']

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.All(
            vol.Schema({vol.Required(CONF_URL): cv.string}),
            vol.Schema({vol.Required(CONF_UUID): cv.string}),
            vol.Schema({vol.Required(CONF_ROOMS): cv.string}),
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up local_ip from configuration.yaml."""
    hass.data.setdefault(DOMAIN, {"api":{}, "room":{}, "thermostat": {}})

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up bestin  from a config entry."""
    #api
    hass.data.setdefault(DOMAIN, {"api": {}, "room": {}, "thermostat": {}})

    api = API(hass, entry)

    #bestin_token.json check
    if not api._isAccessTokenInfo():
        _LOGGER.error(f'[{DOMAIN}] bestin_token.json is not exist.')
        ret = await api._login()

    await api._login()

    hass.data[DOMAIN]["api"][entry.entry_id] = api

    try:
        await api._getFeatures()
    except Exception as ex:
        _LOGGER.error(f'[{DOMAIN}] api._getFeatures() Exception. -> %s', ex)

    #rooms
    room_info = {}

    for room in api._rooms:
        r = BestinRoom(room, api)

        if DT_LIGHT in api._devices:
            await r.lightState()

        if DT_OUTLET in api._devices:
            if room != 'l':
                await r.outletState()

        room_info[room] = r

    hass.data[DOMAIN]["room"][entry.entry_id] = room_info

    #thermostat
    if DT_CLIMATE in api._devices:
        thermostat = BestinThermostat(api)

        await thermostat.thermostatState()

        hass.data[DOMAIN]['thermostat'][entry.entry_id] = thermostat

    #async create task
    # MULTI
    # default sensor : login + sync
    platforms = ['sensor', 'switch']
    
    #await hass.config_entries.async_forward_entry_setups(entry, ['sensor'])
    #await hass.config_entries.async_forward_entry_setups(entry, ['switch'])

    # SINGLE
    if DT_LIGHT in api._devices:
        platforms += ['light']
        #await hass.config_entries.async_forward_entry_setups(entry, ['light'])

    if DT_CLIMATE in api._devices:
        platforms += ['climate']
        #await hass.config_entries.async_forward_entry_setups(entry, ['climate'])

    if DT_FAN in api._devices:
        platforms += ['fan']
        #await hass.config_entries.async_forward_entry_setup(entry, ['fan'])

    #button
    if DT_LIGHT in api._devices or DT_GAS in api._devices:
        platforms += ['button']
        #await hass.config_entries.async_forward_entry_setup(entry, ['button'])

    # async forward entry setups
    await hass.config_entries.async_forward_entry_setups(entry, platforms)

    # light room all off serivce
    async def room_light_all_off(service):
        room = service.data["room"]

        await api._lightAllOff(room)

    hass.services.async_register(DOMAIN, "room_light_all_off", room_light_all_off)

    # elevator
    async def call_elevator(service):
        addr = service.data["address"]
        dir  = service.data["direction"]

        await api._callElevator(addr, dir)

    hass.services.async_register(DOMAIN, "call_elevator", call_elevator)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""

    #api
    api = hass.data[DOMAIN]["api"][config_entry.entry_id]

#    return await hass.config_entries.async_forward_entry_unload(entry, PLATFORM)
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    return unload_ok
