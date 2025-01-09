"""Config flow for Bestin Smarthome v2"""
import logging
import os
import json

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.const import (CONF_SCAN_INTERVAL, CONF_PASSWORD)

from .const import DOMAIN, CONF_URL, CONF_UUID, CONF_ROOMS, CONF_DEVICES, _ROOMS, _ROOMS_R, _LIMIT, _ACTIONS, _DEVICES, BESTIN_TOKEN, CONF_THER_INTVL, CONF_ROOM_INTVL, CONF_R_LIGHT_INTVL, CONF_R_OUTLET_INTVL, CONF_ENERGY_INTVL, CONF_GAS_INTVL, CONF_FAN_INTVL
from .bestinAPIv2 import login

_LOGGER = logging.getLogger(__name__)

def _json_token():
    try:
        with open(BESTIN_TOKEN, 'r') as f:
            config = json.load(f)
            f.close()
            return config
    except Exception as ex:
        _LOGGER.error( '[_json_read Error] %s 파일이 없거나, 파일 읽는데 실패습니다. %s', filename, ex )
        return {'ret':False,'msg':'config file not found'}


class BestinV2ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Bestin Smarthome v2."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize flow."""
        self._url:  Required[str] = None
        self._uuid: Required[str] = None
        self._site_nm:    Optional[str] = None
        self._identifier: Optional[str] = None

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:

            if user_input['action'] == 'LOGIN':
                return await self.async_step_login()
            else:
                return await self.async_step_install()

#            self._url     = user_input[CONF_URL]
#            self._uuid    = user_input[CONF_UUID]

#            uuid = 'bestin-v2-{}'.format(self._uuid)
#            await self.async_set_unique_id(uuid)

#            tit = ''
#            if self._site_nm is not None:
#                tit = '{}({})'.format(self._site_nm, self._identifier)
#            else:
#                tit = '{}({})'.format(user_input[CONF_URL], user_input[CONF_UUID])

#            return self.async_create_entry(title=tit, data=user_input)

#        if self._async_current_entries():
#            return self.async_abort(reason="single_instance_allowed")

        if user_input is None:
            return self.async_show_form(
                step_id='user',
                data_schema=vol.Schema({ vol.Required('action', default='LOGIN'): vol.In(_ACTIONS) })
                )
            #return self._show_user_form(errors)

    async def async_step_import(self, import_info):
        """Handle import from config file."""
        return await self.async_step_user(import_info)

    @callback
    async def async_step_login(self, user_input=None, error=None):
        errors = {}

        schema = vol.Schema(
            {
                vol.Required(CONF_UUID,  default=None): cv.string,
            }
        )

        if user_input:
            if 'uuid' not in user_input:
                return self.async_show_form(
                    step_id="login", data_schema=schema, errors=errors or {}
                )


            if user_input is not None:
                session = async_create_clientsession(self.hass)

                res = await login(session, user_input['uuid'])

                if res.status == 200:
                    json_login = await res.json()

                    self._url        = json_login['url']
                    self._uuid       = user_input['uuid']
                    self._site_nm    = json_login['site_name']
                    self._identifier = json_login['identifier']

                    return await self.async_step_user()
                else:
                    _LOGGER.error(f'[{DOMAIN}] async_step_login() Failed, %s', res)
                    return self.async_abort(reason="login_failed")
                    #return await self.async_step_login(error='no_uuid')

        if user_input is None:
            return self.async_show_form(
                step_id="login", data_schema=schema, errors=errors or {}
            )

    @callback
    async def async_step_install(self, user_input=None, errors=None):

        if user_input is not None:
            self._url     = user_input[CONF_URL]
            self._uuid    = user_input[CONF_UUID]

            uuid = 'bestin-v2-{}'.format(self._uuid)
            await self.async_set_unique_id(uuid)

            tit = ''
            if self._site_nm is not None:
                tit = '{}({})'.format(self._site_nm, self._identifier)
            else:
                tit = '{}({})'.format(user_input[CONF_URL], user_input[CONF_UUID])

            return self.async_create_entry(title=tit, data=user_input)

#        if self._async_current_entries():
#            return self.async_abort(reason="single_instance_allowed")

        MS_ROOMS = _ROOMS

        if self._url in _LIMIT:
            MS_ROOMS = _ROOMS_R

        schema = vol.Schema(
            {
                vol.Required(CONF_URL,   default=self._url): cv.string,
                vol.Required(CONF_UUID,  default=self._uuid): cv.string,
                vol.Required(CONF_ROOMS, default=[]): cv.multi_select(MS_ROOMS),
                vol.Required(CONF_DEVICES,        default=[]): cv.multi_select(_DEVICES),
                vol.Required(CONF_THER_INTVL,     default=300): cv.positive_int,
                vol.Required(CONF_R_LIGHT_INTVL,  default=300): cv.positive_int,
                vol.Required(CONF_R_OUTLET_INTVL, default=600): cv.positive_int,
                vol.Required(CONF_GAS_INTVL,      default=300): cv.positive_int,
                vol.Required(CONF_FAN_INTVL,      default=300): cv.positive_int,
                vol.Required(CONF_ENERGY_INTVL,   default=600): cv.positive_int,
                #vol.Required(CONF_SCAN_INTERVAL, default=90): vol.All(vol.Coerce(int), vol.Range(min=min_int, max=max_int)),
            }
        )

        return self.async_show_form(
            step_id="install", data_schema=schema, errors=errors or {}
        )

