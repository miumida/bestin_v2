# Import the device class from the component that you want to support
from homeassistant.components.sensor import PLATFORM_SCHEMA

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
from homeassistant.const import (CONF_NAME, CONF_PASSWORD, CONF_SCAN_INTERVAL)
from homeassistant.helpers.entity import Entity
from homeassistant.components.sensor import SensorEntity
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import Throttle

from .const import DOMAIN, CONF_URL, CONF_UUID, CONF_ROOMS, _ROOMS, MODEL, SW_VERSION, BESTIN_TOKEN, _ENERGY, CONF_GAS_INTVL, CONF_FAN_INTVL, CONF_R_LIGHT_INTVL, CONF_R_OUTLET_INTVL
from .const import _R_ICON, DT_LIGHT, DT_OUTLET, DT_CLIMATE, DT_FAN, DT_GAS, DT_ENERGY
from .bestinAPIv2 import BestinAPIv2 as API

_ICONS = {
    'thermostat': 'mdi:thermostat',
    'energy'    : 'mdi:lightning-bolt',
}


_LOGGER = logging.getLogger(__name__)

POLLING_TIMEOUT_SEC = 30
SCAN_INTERVAL = timedelta(seconds=3000)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_URL): cv.string,
    vol.Required(CONF_UUID): cv.string,
    vol.Required(CONF_ROOMS): cv.string,
})


# For UI
async def async_setup_entry(hass, config_entry, async_add_entities):

    sensors = []

    #api
    api = hass.data[DOMAIN]["api"][config_entry.entry_id]

    sensors += [LoginInfoSensor(api)]

    #= energy Sensor START =======================================================
    async def async_update_energy():
        try:
            # handled by the data update coordinator.
            async with async_timeout.timeout(POLLING_TIMEOUT_SEC):
                data = await api._getEnergy()

                rtn = {}

                for key in data[0]:
                    rtn[key] = data[0][key]

                #_LOGGER.error(f"[{DOMAIN}] async_update_energy() Error, %s", rtn )

                dt = datetime.now()
                syncdate = dt.strftime("%Y-%m-%d %H:%M:%S")
                rtn['syncdate'] = syncdate

                return rtn
        except Exception as err:
            raise UpdateFailed(f"[{DOMAIN}] Error communicating with API: {err}")

    if DT_ENERGY in api._devices:
        coordinatorEnergy = DataUpdateCoordinator(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="sensor",
            update_method=async_update_energy,
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta( seconds=int(config_entry.data.get("e_interval", 600)) ),
        )

    #try:
        await coordinatorEnergy.async_config_entry_first_refresh()

        sensors += [ BestinEnergySyncSensor(coordinatorEnergy, 'energy') ]

        for key in coordinatorEnergy.data:
            if key in _ENERGY:
                sensors += [ BestinEnergySyncSensor(coordinatorEnergy, key) ]
    #except Exception as err:
    #    _LOGGER.error(f"[{DOMAIN}] BestinEnergySncSensor() Setup failed, %s", err)
    #= energy END =============================================================


    #= room Sensor START =======================================================
    rooms = hass.data[DOMAIN]["room"][config_entry.entry_id]

    # room light
    async def async_update_room():
        try:
            # handled by the data update coordinator.
            async with async_timeout.timeout(120):

                data = {}

                for room in rooms:
                    dt = datetime.now()
                    syncdate = dt.strftime("%Y-%m-%d %H:%M:%S")

                    await rooms[room].lightState()

                    # on count
                    on = 0

                    light = rooms[room]._lights

                    for key in light:
                        val = light[key]
                        if 'on' in val:
                            on = on + 1

                    data[room] = { 'lights' : rooms[room]._lights, 'on_light': on, 'syncdate' : syncdate }

                return data
        except Exception as err:
            raise UpdateFailed(f"[{DOMAIN}] Error communicating with API: {err}")

    if DT_LIGHT in api._devices:
        coordinatorRoom = DataUpdateCoordinator(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="sensor",
            update_method=async_update_room,
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta( seconds=int(config_entry.data.get(CONF_R_LIGHT_INTVL, 300)) ),
        )

        await coordinatorRoom.async_config_entry_first_refresh()

        for key in coordinatorRoom.data:
            sensors += [ BestinRoomSyncSensor(coordinatorRoom, key, DT_LIGHT) ]

    # room outlet
    async def async_update_room_outlet():
        try:
            # handled by the data update coordinator.
            async with async_timeout.timeout(120):

                data = {}

                for room in rooms:
                    dt = datetime.now()
                    syncdate = dt.strftime("%Y-%m-%d %H:%M:%S")

                    if room != 'l':
                        await rooms[room].outletState()

                    # on count
                    on = 0

                    outlet = rooms[room]._outlets

                    for key in outlet:
                        val = outlet[key]
                        if 'on' in val:
                            on = on + 1

                    data[room] = { 'outlets' : rooms[room]._outlets, 'on_outlet': on, 'syncdate' : syncdate }

                return data
        except Exception as err:
            raise UpdateFailed(f"[{DOMAIN}] Error communicating with API: {err}")

    if DT_OUTLET in api._devices:
        coordinatorRoomOutlet = DataUpdateCoordinator(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="sensor",
            update_method=async_update_room_outlet,
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta( seconds=int(config_entry.data.get(CONF_R_OUTLET_INTVL, 600)) ),
        )

        await coordinatorRoomOutlet.async_config_entry_first_refresh()

        for key in coordinatorRoomOutlet.data:
            if key == 'l': continue

            sensors += [ BestinRoomSyncSensor(coordinatorRoomOutlet, key, DT_OUTLET) ]

    #= room Sensor END ===============================================================


    #= thermostat Sensor START ========================================================
    if DT_CLIMATE in api._devices:
        cli =  hass.data[DOMAIN]["thermostat"][config_entry.entry_id]

    async def async_update_data():
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with async_timeout.timeout(POLLING_TIMEOUT_SEC):
                await cli.thermostatState()

                dt = datetime.now()
                syncdate = dt.strftime("%Y-%m-%d %H:%M:%S")

                data = cli._thermostats
                on = 0

                for key in data:
                    val = data[key]
                    if 'on' in val:
                        on = on + 1

                data['on_count'] = on
                data['syncdate'] = syncdate

                return data
        except ApiAuthError as err:
            # Raising ConfigEntryAuthFailed will cancel future updates
            # and start a config flow with SOURCE_REAUTH (async_step_reauth)
            raise ConfigEntryAuthFailed from err
        except ApiError as err:
            raise UpdateFailed(f"Error communicating with API: {err}")

    if DT_CLIMATE in api._devices:
        coordinator = DataUpdateCoordinator(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="sensor",
            update_method=async_update_data,
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta( seconds=int(config_entry.data.get("t_interval", 600)) ),
        )

        await coordinator.async_config_entry_first_refresh()

        sensors += [BestinClimateSyncSensor(coordinator, 'thermostat')]
    #= thermostat END =============================================================

    #= gaslock Senser START =======================================================
    async def async_update_gaslock():
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with async_timeout.timeout(60):
                await api._gasState()

                dt = datetime.now()
                syncdate = dt.strftime("%Y-%m-%d %H:%M:%S")

                data = api._gas

                data['syncdate'] = syncdate

                return data
        except Exception as err:
            raise UpdateFailed(f"[{DOMAIN}] Error communicating with API: {err}")

    if DT_GAS in api._devices:
        coordinatorGaslock = DataUpdateCoordinator(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="sensor",
            update_method=async_update_gaslock,
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta( seconds=int(config_entry.data.get(CONF_GAS_INTVL, 300)) ),
        )

        await coordinatorGaslock.async_config_entry_first_refresh()

        sensors += [BestinGasSyncSensor(coordinatorGaslock)]
    #= gaslock END =============================================================


    #= fan Sensor START ========================================================
    async def async_update_fan():
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with async_timeout.timeout(60):
                await api._ventilState()

                dt = datetime.now()
                syncdate = dt.strftime("%Y-%m-%d %H:%M:%S")

                data = api._fan

                data['syncdate'] = syncdate

                return data
        except Exception as err:
            raise UpdateFailed(f"[{DOMAIN}] Error communicating with API: {err}")

    # FAN이 있는 경우만 추가
    if DT_FAN in api._devices:
        coordinatorFan = DataUpdateCoordinator(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="sensor",
            update_method=async_update_fan,
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta( seconds=int(config_entry.data.get(CONF_FAN_INTVL, 300)) ),
        )

        await coordinatorFan.async_config_entry_first_refresh()

        sensors += [BestinFanSyncSensor(coordinatorFan)]
    #= fan END =================================================================


    #add entities
    async_add_entities(sensors)



def cover_list(dict):
    if not dict:
        return []
    elif isinstance(dict, list):
        return dict
    else:
        return [dict]


class LoginInfoSensor(Entity):
    def __init__(self, api):
        self._api       = api

        self.data       = {}

        if self._api is not None:
            self.data = self._api._getLoginInfo()

        dt = datetime.now()
        self._syncdate = dt.strftime("%Y-%m-%d %H:%M:%S")

    @property
    def unique_id(self):
        """Return the entity ID."""
        return 'sensor.bestin_v2_login'


    @property
    def name(self):
        """Return the name of the sensor, if any."""
        return 'bestin_v2_login'

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return 'mdi:account-key'

    @property
    def state(self):
        return self._syncdate

    async def async_update(self):
        """Get the latest state of the sensor."""
        if self._api is None:
            return

        await self._api._login()

        login = self._api._getLoginInfo()

        self.data = login

        dt = datetime.now()
        self._syncdate = dt.strftime("%Y-%m-%d %H:%M:%S")

    @property
    def extra_state_attributes(self):
        """Attributes."""

        data = {}

        data = self.data

        data['features'] = self._api._features

        data['syncdate'] = self._syncdate

        return data

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


class BestinRoomSensor(Entity):
    def __init__(self, room, api):
        self._room      = room
        self._api       = api

        self._state     = None

        self.data       = {}

        dt = datetime.now()
        self._syncdate = dt.strftime("%Y-%m-%d %H:%M:%S")


    @property
    def unique_id(self):
        """Return the entity ID."""
        return 'sensor.bestin_v2_{}'.format(self._room)


    @property
    def name(self):
        """Return the name of the sensor, if any."""
        return 'bestin_v2_{}'.format(_ROOMS[self._room])

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return _R_ICON[self._room]

    @property
    def state(self):
        return str(self._syncdate)


    async def async_update(self):
        """Get the latest state of the sensor."""
        if self._api is None:
            return

        await self._api.lightState()

        if self._room != 'l':
            await self._api.outletState()

        dt = datetime.now()
        self._syncdate = dt.strftime("%Y-%m-%d %H:%M:%S")


    @property
    def extra_state_attributes(self):
        """Attributes."""
        data = {}

        data['lights']  = self._api._lights
        data['outlets'] = self._api._outlets

        data['syncdate'] = self._syncdate

        return data

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

class BestinClimateSensor(Entity):
    def __init__(self, api):
        self._api       = api

        self.data       = {}

        if self._api is not None:
            self.data = self._api._thermostats

        dt = datetime.now()
        self._syncdate = dt.strftime("%Y-%m-%d %H:%M:%S")


    @property
    def unique_id(self):
        """Return the entity ID."""
        return 'sensor.bestin_v2_thermostat'


    @property
    def name(self):
        """Return the name of the sensor, if any."""
        return 'bestin_v2_thermostat'

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return 'mdi:thermostat'

    @property
    def state(self):
        return self._syncdate


    async def async_update(self):
        """Get the latest state of the sensor."""
        if self._api is None:
            return

        await self._api.thermostatState()

        cli = self._api._thermostats

        dt = datetime.now()
        self._syncdate = dt.strftime("%Y-%m-%d %H:%M:%S")

        self.data = cli

    @property
    def extra_state_attributes(self):
        """Attributes."""

        attr = {}

        attr = self.data

        attr['syncdate'] = self._syncdate

        return attr

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

class BestinClimateSyncSensor(CoordinatorEntity, SensorEntity):

    def __init__(self, coordinator, id):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)

        dt = datetime.now()
        self._id = id
        self._name = None
        self._syncdate = dt.strftime("%Y-%m-%d %H:%M:%S")


    @property
    def unique_id(self):
        """Return the entity ID."""
        return 'sensor.bestin_v2_sync_{}'.format(self._id.lower())


    @property
    def name(self):
        """Return the name of the sensor, if any."""
        if self._name is None:
            self._name = 'bestin_v2_sync_{}'.format(self._id.lower())
            return self._name
        else:
            return self._name

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return _ICONS[self._id]

    @property
    def state(self):
        return self.coordinator.data.get('on_count', '-')

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this sensor."""
        return "room"


    async def async_update(self):
        """Get the latest state of the sensor."""
        if self._api is None:
            return

        dt = datetime.now()
        self._syncdate = dt.strftime("%Y-%m-%d %H:%M:%S")


    @property
    def extra_state_attributes(self):
        """Attributes."""

        attr = {}

        attr = self.coordinator.data

        return attr

    @property
    def device_info(self):
        group = 'Sync'

        """Return information about the device."""
        return {
            "identifiers": {(DOMAIN, group.lower())},
            'name': 'BESTIN v2 {}'.format(group),
            'manufacturer': 'HDC현대산업개발',
            'model': MODEL,
            'sw_version': SW_VERSION
        }

class BestinEnergySyncSensor(CoordinatorEntity, SensorEntity):

    def __init__(self, coordinator, id):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)

        dt = datetime.now()
        self._id = id
        self._name = None
        self._syncdate = dt.strftime("%Y-%m-%d %H:%M:%S")


    @property
    def unique_id(self):
        """Return the entity ID."""
        return 'sensor.bestin_v2_{}'.format(self._id.lower())


    @property
    def name(self):
        """Return the name of the sensor, if any."""
        if self._name is None:
            self._name = _ENERGY[self._id][0] if self._id in _ENERGY else 'bestin_v2_{}'.format(self._id.lower())
            return 'bestin_v2_sync_{}'.format(self._id.lower())
        else:
            return self._name

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""

        if self._id in _ENERGY:
            return _ENERGY[self._id][1]
        else:
            return _ICONS[self._id]

    @property
    def state(self):
        if self._id in _ENERGY:
            return self.coordinator.data.get(self._id, '-')
        else:
            return self.coordinator.data.get('syncdate', '-')

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this sensor."""
        if self._id in _ENERGY:
            return _ENERGY[self._id][2]
        else:
            return ""


    async def async_update(self):
        """Get the latest state of the sensor."""
        if self._api is None:
            return

        dt = datetime.now()
        self._syncdate = dt.strftime("%Y-%m-%d %H:%M:%S")


    @property
    def extra_state_attributes(self):
        """Attributes."""

        attr = {}

        if self._id in _ENERGY:
            attr[_ENERGY[self._id][0]] = self.coordinator.data[self._id]
            attr['craeted_at'] = self.coordinator.data['craeted_at']
            attr['updated_at'] = self.coordinator.data['updated_at']
        else:
            attr = self.coordinator.data

        return attr

    @property
    def device_info(self):
        group = 'Sync'

        if self._id in _ENERGY:
            group = 'Energy'

        """Return information about the device."""
        return {
            "identifiers": {(DOMAIN, group.lower())},
            'name': 'BESTIN v2 {}'.format(group),
            'manufacturer': 'HDC현대산업개발',
            'model': MODEL,
            'sw_version': SW_VERSION
        }

class BestinRoomSyncSensor(CoordinatorEntity, SensorEntity):

    def __init__(self, coordinator, id, type):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)

        dt = datetime.now()
        self._id   = id
        self._type = type
        self._name = None
        self._syncdate = dt.strftime("%Y-%m-%d %H:%M:%S")


    @property
    def unique_id(self):
        """Return the entity ID."""
        return 'sensor.bestin_v2_sync_{}_{}'.format(_ROOMS[self._id.lower()], self._type)


    @property
    def name(self):
        """Return the name of the sensor, if any."""
        if self._name is None:
            self._name = 'bestin_v2_sync_{}_{}'.format(_ROOMS[self._id.lower()], self._type)
            return self._name
        else:
            return self._name

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return _R_ICON[self._id]

    @property
    def state(self):
        return str(self.coordinator.data[self._id].get('on_{}'.format(self._type), '-'))

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this sensor."""
        return self._type


    async def async_update(self):
        """Get the latest state of the sensor."""
        if self._api is None:
            return

        dt = datetime.now()
        self._syncdate = dt.strftime("%Y-%m-%d %H:%M:%S")


    @property
    def extra_state_attributes(self):
        """Attributes."""

        attr = {}

        attr = self.coordinator.data[self._id]

        return attr

    @property
    def device_info(self):
        group = 'Sync'

        """Return information about the device."""
        return {
            "identifiers": {(DOMAIN, group.lower())},
            'name': 'BESTIN v2 {}'.format(group),
            'manufacturer': 'HDC현대산업개발',
            'model': MODEL,
            'sw_version': SW_VERSION
        }


class BestinGasSyncSensor(CoordinatorEntity, SensorEntity):

    def __init__(self, coordinator):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)

        dt = datetime.now()
        self._name = None
        self._syncdate = dt.strftime("%Y-%m-%d %H:%M:%S")


    @property
    def unique_id(self):
        """Return the entity ID."""
        return 'sensor.bestin_v2_sync_gas'


    @property
    def name(self):
        """Return the name of the sensor, if any."""
        if self._name is None:
            self._name = 'bestin_v2_sync_gas'
            return self._name
        else:
            return self._name

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return 'mdi:valve'

    @property
    def state(self):
        return self.coordinator.data.get('gas1', '-')

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this sensor."""
        return None


    async def async_update(self):
        """Get the latest state of the sensor."""
        if self._api is None:
            return

        dt = datetime.now()
        self._syncdate = dt.strftime("%Y-%m-%d %H:%M:%S")


    @property
    def extra_state_attributes(self):
        """Attributes."""

        attr = {}

        attr = self.coordinator.data

        return attr

    @property
    def device_info(self):
        group = 'Sync'

        """Return information about the device."""
        return {
            "identifiers": {(DOMAIN, group.lower())},
            'name': 'BESTIN v2 {}'.format(group),
            'manufacturer': 'HDC현대산업개발',
            'model': MODEL,
            'sw_version': SW_VERSION
        }


class BestinFanSyncSensor(CoordinatorEntity, SensorEntity):

    def __init__(self, coordinator):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)

        dt = datetime.now()
        self._name = None
        self._syncdate = dt.strftime("%Y-%m-%d %H:%M:%S")


    @property
    def unique_id(self):
        """Return the entity ID."""
        return 'sensor.bestin_v2_sync_fan'


    @property
    def name(self):
        """Return the name of the sensor, if any."""
        if self._name is None:
            self._name = 'bestin_v2_sync_fan'
            return self._name
        else:
            return self._name

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return 'mdi:fan'

    @property
    def state(self):
        return self.coordinator.data.get('syncdate', '-')

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this sensor."""
        return ""


    async def async_update(self):
        """Get the latest state of the sensor."""
        if self._api is None:
            return

        dt = datetime.now()
        self._syncdate = dt.strftime("%Y-%m-%d %H:%M:%S")


    @property
    def extra_state_attributes(self):
        """Attributes."""

        attr = {}

        attr = self.coordinator.data

        return attr

    @property
    def device_info(self):
        group = 'Sync'

        """Return information about the device."""
        return {
            "identifiers": {(DOMAIN, group.lower())},
            'name': 'BESTIN v2 {}'.format(group),
            'manufacturer': 'HDC현대산업개발',
            'model': MODEL,
            'sw_version': SW_VERSION
        }

