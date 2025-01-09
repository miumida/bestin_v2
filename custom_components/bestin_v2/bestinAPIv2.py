import logging
import requests
import voluptuous as vol
import json
import re
import xmltodict
import os

from datetime import datetime

from homeassistant import exceptions
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.const import (CONF_NAME, CONF_PASSWORD)

from .const import DOMAIN, CONF_URL, CONF_UUID, CONF_ROOMS, CONF_DEVICES, _ROOMS, BESTIN_TOKEN, ACCESS_TOKEN, _LOGIN_URL, _FEATURES_URL, _VALLEY_URL, _CTRL_URL, _ENERGY_URL, _ELEV_URL, _SITE_INFO_URL, TIMEOUT_SEC

_LOGGER = logging.getLogger(__name__)


def cover_list(dict):
    if not dict:
        return []
    elif isinstance(dict, list):
        return dict
    else:
        return [dict]

def units2json(val):
    if 'units' in val:
        units = val['units']

        json = {}

        if units is None:
            return json

        for unit in units:
            json[unit['unit']] = unit['state']

        return json
    else:
        return {}

def map2json(val):
    if 'map' in val:
        map = val['map']

        if map is None:
            return {}

        return map
    else:
        return {}


def feature2json(val):
    features = val['features']

    json = {}

    for ft in features:
        if ft['quantity'] == 0:
            continue

        json[ft['name']] = ft['quantity']

    return json


def setOutlet(val, gb, chgVal):
    arrVal = val.split('/')

    if gb == 'on':
        return '{}/{}'.format('set', chgVal)
    else:
        return '{}/{}'.format(chgVal, arrVal[1])

async def login(session, uuid):
    url = _LOGIN_URL

    hdr = { 'Content-Type': 'application/json'
          , 'Authorization': uuid
          , "User-Agent": ("mozilla/5.0 (windows nt 10.0; win64; x64) applewebkit/537.36 (khtml, like gecko) chrome/78.0.3904.70 safari/537.36") }

    try:
        response = await session.post(url, headers=hdr, timeout=TIMEOUT_SEC)

    except Exception as ex:
        _LOGGER.error(f'[{DOMAIN}] _login() Error Exception -> %s', ex)

    if response.status == 200:
        res = await response.json()
        _LOGGER.error(f"[{DOMAIN}] _login() is success! -> %s", res)

    elif response.status == 500:
        res = await response.json()
        _LOGGER.error(f"[{DOMAIN}] _login() is Failed(500). Error msg is %s", res['err'] )
    else:
        res = await response.json()
        _LOGGER.error(f"[{DOMAIN}] _login() is Failed. -> %s", res)

    return response


class BestinAPIv2:
    """Bestin Smarthome 2.0 API."""

    def __init__(self, hass, entry):
        """Initialize the Bestin v2 API.."""
        self._hass  = hass
        self._entry = entry

        #user_input
        self._url   = entry.data[CONF_URL]
        self._uuid  = entry.data[CONF_UUID]

        self._rooms   = entry.data[CONF_ROOMS]
        self._devices = entry.data[CONF_DEVICES]

        self._gas   = {}
        self._fan   = {}

        self._features = {}

        #debug
        self._debug = False

        #token
        self._token = None

    # json util
    def _json_read(self, filename):
        try:
            with open(filename, 'r') as f:
                config = json.load(f)
                f.close()
                return config
            return True
        except Exception as ex:
            _LOGGER.error( '[_json_read Error] %s 파일이 없거나, 파일 읽는데 실패습니다. %s', filename, ex )
            return {'ret':False,'msg':'config file not found'}

    def _json_save(self, data, savename):
        try:
            js_w = open(savename, 'w')
            js_w.write(json.dumps(data, sort_keys= True, indent=1))
            js_w.close()
            return True
        except:
            return False

    async def _get(self, url):
        token = self._json_read(BESTIN_TOKEN)
        hdr   = { ACCESS_TOKEN: token[ACCESS_TOKEN]
                , "User-Agent": ("mozilla/5.0 (windows nt 10.0; win64; x64) applewebkit/537.36 (khtml, like gecko) chrome/78.0.3904.70 safari/537.36") }

        websession = async_get_clientsession(self._hass)

        res = await websession.get(url, headers=hdr, timeout=TIMEOUT_SEC)
        #res.raise_for_status()

        if res.status == 500:
            res_json = await res.json()
            _LOGGER.error(f"[{DOMAIN}] _get() is Failed(500). Error msg is %s", res_json['err'] )

        #_LOGGER.error(await res.text())

        return res

    async def _post(self, url, data):

        token = self._json_read(BESTIN_TOKEN)
        hdr   = { 'Content-Type':  'application/json'
                , ACCESS_TOKEN: token[ACCESS_TOKEN]
                , "User-Agent": ("mozilla/5.0 (windows nt 10.0; win64; x64) applewebkit/537.36 (khtml, like gecko) chrome/78.0.3904.70 safari/537.36") }

        websession = async_get_clientsession(self._hass)

        res = await websession.put(url, headers=hdr, json=data , timeout=TIMEOUT_SEC)

        if res.status == 500:
            res_json = await res.json()
            _LOGGER.error(f"[{DOMAIN}] _post() is Failed(500). Error msg is %s", res_json['err'] )

        if self._debug:
            _LOGGER.error(f'[{DOMAIN}] _post() -> %s', data)

        #res.raise_for_status()

        if self._debug:
            _LOGGER.error(await res.text())

        return res

    #connect session
    async def _login(self):
        url = _LOGIN_URL

        hdr = { 'Content-Type': 'application/json'
              , 'Authorization': self._uuid
              , "User-Agent": ("mozilla/5.0 (windows nt 10.0; win64; x64) applewebkit/537.36 (khtml, like gecko) chrome/78.0.3904.70 safari/537.36") }

        session = async_get_clientsession(self._hass)

        try:
            response = await session.post(url, headers=hdr, timeout=TIMEOUT_SEC)

        except Exception as ex:
            _LOGGER.error(f'[{DOMAIN}] _login() Error Exception -> %s', ex)
            return { 'ret':False, 'msg':'network fail' }

        if response.status == 200:
            res = await response.json()

            sucessLogin = { 'ret': True, 'msg': res }

            self._json_save(res, BESTIN_TOKEN)

            if self._debug:
                _LOGGER.error(f"[{DOMAIN}] _login() is success! -> %s", res)

            return sucessLogin
        elif response.status == 500:
            res = await response.json()
            _LOGGER.error(f"[{DOMAIN}] _login() is Failed(500). Error msg is %s", res['err'] )
            return {}
        else:
            res = await response.json()
            _LOGGER.error(f"[{DOMAIN}] _login() is Failed. -> %s", res)
            return { 'ret':False, 'msg': 'Login Failed' }

    def _getLoginInfo(self):
        loginInfo = self._json_read(BESTIN_TOKEN)

        return loginInfo

    #login
    def _isAccessTokenInfo(self):
        if not os.path.isfile(BESTIN_TOKEN):
            _LOGGER.error(f"[{DOMAIN}] File %s doesn't exist.", BESTIN_TOKEN)
            return False

        return True

    #debug
    def _debugOn(self):
        self._debug = True

    def _debugOff(self):
        self._debug = False

    #features
    async def _getFeatures(self):
        url = '{}{}'.format(self._url, _FEATURES_URL)

        res = await self._get(url)

        if res.status == 500:
            resJson = await res.text()
            _LOGGER.error(f"[{DOMAIN}] _getFeatures() Error(500) ->  %s", resJson)

        json = await res.json()

        #_LOGGER.error(f"[{DOMAIN}] _getFeatures() -> %s", json)

        if self._debug:
            _LOGGER.error(f"[{DOMAIN}] _getFeatures() ->  %s", json)

        self._features = feature2json(json)

        return json

    #siteinfo
    async def _getSiteInfo(self):
        url = '{}{}'.format(self._url, _SITE_INFO_URL)

        res = await self._get(url)

        if res.status == 500:
            resJson = await res.text()
            _LOGGER.error(f"[{DOMAIN}] _getSiteInfo() Error(500) ->  %s", resJson)

        json = await res.json()

        #_LOGGER.error(f"[{DOMAIN}] _getSiteInfo() -> %s", json)

        if self._debug:
            _LOGGER.error(f"[{DOMAIN}] _getSiteInfo() ->  %s", json)

        return json



    #valley
    async def _getValley(self):
        url = _VALLEY_URL

        hdr = { 'Content-Type': 'application/json'
              , 'Authorization': self._uuid
              , "User-Agent": ("mozilla/5.0 (windows nt 10.0; win64; x64) applewebkit/537.36 (khtml, like gecko) chrome/78.0.3904.70 safari/537.36") }

        session = async_get_clientsession(self._hass)

        try:
            res = await session.get(url, headers=hdr, timeout=TIMEOUT_SEC)

        except Exceoption as ex:
            _LOGGER.error(f'[{DOMAIN}] _getValley() resonse Error, %s', ex)

        if res.status == 500:
            resJson = await res.text()
            _LOGGER.error(f"[{DOMAIN}] _getValley() Error(500) ->  %s", resJson)

        json = await res.json()

        _LOGGER.error(f"[{DOMAIN}] _getValley() -> %s", json)

        if self._debug:
            _LOGGER.error(f"[{DOMAIN}] _getValley() ->  %s", json)

        return json


    #state
    async def _getState(self, feature, room='1'):
        uri = _CTRL_URL.format(feature, room)

        url = '{}{}'.format(self._url, uri)

        res = await self._get(url)

        if res.status == 500:
            resJson = await res.text()
            _LOGGER.error(f"[{DOMAIN}] _getState({feature}, {room}) Error(500) ->  %s", resJson)

        json = await res.json()

        if self._debug:
            _LOGGER.error(f"[{DOMAIN}] _getState({feature}, {room}) ->  %s", json)

        return units2json(json)

    #command
    async def _command(self, feature, unit, state, room='1'):
        uri = _CTRL_URL.format(feature, room)

        url = '{}{}'.format(self._url, uri)

        data = { 'unit': unit, 'state': state }

        if feature == "ventil":
            data = { 'unit': unit, 'state': state, 'mode': "", 'unit_mode': "" }

        res = await self._post(url, data)

        #json = await res.json()

        if self._debug:
            _LOGGER.error(f"[{DOMAIN}] _command({feature}, {room}, {unit}, {state}) ->  %s", await res.read())

    #climate
    async def _setHvacMode(self, room, action, temp):
        res = await self._command('thermostat', room, '{}/{}'.format(action,temp))
        return res

    async def _setHvacTemperature(self, room, action, temp, cur_temp):
        res = await self._command('thermostat', room, '{}/{}/{}'.format(action, temp, cur_temp))
        return res

    #outlet command
    async def _outletOnOff(self, room, unit, state):
        res = await self._command('electric', unit, state, room)

    #light command
    async def _lightOnOff(self, room, unit, state):
        if room == 'l':
            res = await self._command('livinglight', unit, state)
        else:
            res = await self._command('light', unit, state, room)

    #light room all turn off command
    async def _lightAllOff(self, room):
        if room == 'l':
            res = await self._command('livinglight', 'all', 'off')
        else:
            res = await self._command('light', 'all', 'off', room)

        # sync state callx

    #ventil
    async def _ventilState(self):
        res = await self._getState('ventil')

        self._fan = res

        if self._debug:
            _LOGGER.error(f"[{DOMAIN}] _ventilState() -> %s", res)

        return res

    #ventil command
    async def _ventilOnOff(self, unit, state):
        res = await self._command('ventil', unit, state)

    #gas
    async def _gasState(self):
        res = await self._getState('gas')

        self._gas = res

        if self._debug:
            _LOGGER.error(f"[{DOMAIN}] _gasState() -> %s", res)

        return res

    #gas command
    async def _gasLock(self):
        res = await self._command('gas', 'gas1', 'close')

        await self._gasState()


    #energy
    async def _getEnergy(self):
        uri = _ENERGY_URL

        url = '{}{}'.format(self._url, uri)

        res = await self._get(url)

        r_json = await res.text()

        if self._debug:
            _LOGGER.error(f"[{DOMAIN}] _getEnergy() ->  %s", json.loads(r_json) )

        return json.loads(r_json)

    #elevator
    async def _callElevator(self, addr, dir):
        uri = _ELEV_URL

        url = '{}{}'.format(self._url, uri)

        hdr   = { "Content-Type": "application/json"
                , "Authorization": self._uuid
                , "User-Agent": ("mozilla/5.0 (windows nt 10.0; win64; x64) applewebkit/537.36 (khtml, like gecko) chrome/78.0.3904.70 safari/537.36") }

        data = { "address": addr, "direction": dir }

        websession = async_get_clientsession(self._hass)

        res = await websession.post(url, headers=hdr, json=data, timeout=TIMEOUT_SEC)
        #res.raise_for_status()

        if res.status == 500:
            res_json = await res.json()
            _LOGGER.error(f"[{DOMAIN}] _callElevator() is Failed(500). Error msg is %s", res_json['err'] )



class BestinRoom:

    def __init__(self, room, api):
        self._room     = room
        self._room_dsc = _ROOMS[room]
        self._api      = api

        self._lights  = {}
        self._outlets = {}

    # lights
    async def lightState(self):
        if self._room == 'l':
            self._lights = await self._api._getState( 'livinglight' )
        else:
            self._lights = await self._api._getState( 'light', self._room )

    async def dimmingLightState(self):
        if self._room == 'l':
            self._lights = await self._api._getState( 'dimming_livinglight' )
        else:
            self._lights = await self._api._getState( 'dimming_light', self._room )


    async def lightOn(self, switch):
        await self._api._lightOnOff(self._room, switch, 'on')

    async def lightOff(self, switch):
        await self._api._lightOnOff(self._room, switch, 'off')

    def isLightOn(self, switch):
        return self._lights[switch]


    # outlets
    async def outletState(self):
        self._outlets = await self._api._getState( 'electric', self._room )

    async def outletOn(self, switch):
        await self._api._outletOnOff(self._room, switch, 'on')

    async def outletOff(self, switch):
        await self._api._outletOnOff(self._room, switch, 'off')

    async def outletSet(self, switch):
        await self._api._outletOnOff(self._room, switch, 'set')

    async def outletUnset(self, switch):
        await self._api._outletOnOff(self._room, switch, 'unset')

    def isOutletOn(self, switch):
        return self._outlets[switch]


class BestinThermostat:

    def __init__(self, api):
        self._api      = api

        self._thermostats = {}

    def stateParse(self, room, index):
        return self._thermostats[room].split('/')[index]

    async def thermostatState(self):
        self._thermostats = await self._api._getState('thermostat')

    async def setHvacMode(self, room, action, target_temp):
        await self._api._setHvacMode(room, action, target_temp)

    async def setHvacTemperature(self, room, action, target_temp,cur_temp):
        await self._api._setHvacTemperature(room, action, target_temp, cur_temp)

    def isThermostateOn(self, room):
        return self.stateParse(room, 0)

    def getTargetTemp(self, room):
        return self.stateParse(room, 1)

    def getCurrTemp(self, room):
        return self.stateParse(room, 2)

