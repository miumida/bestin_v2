DOMAIN = 'bestin_v2'

# Conf
CONF_URL   = 'url'
CONF_UUID  = 'uuid'
CONF_ROOMS = 'rooms'
CONF_DEVICES = 'devices'

CONF_THER_INTVL   = 't_interval'
CONF_ROOM_INTVL   = 'r_interval'
CONF_R_LIGHT_INTVL  = 'r_light_interval'
CONF_R_OUTLET_INTVL = 'r_outlet_interval'
CONF_ENERGY_INTVL = 'e_interval'
CONF_GAS_INTVL    = 'gas_interval'
CONF_FAN_INTVL    = 'fan_interval'

# Device Info
MODEL      = 'BESTIN v2'
SW_VERSION = '1.0.0'

BESTIN_TOKEN = 'bestin_token.json'
ACCESS_TOKEN = 'access-token'
TIMEOUT_SEC  = 60

_ROOMS = {
    'l' : 'living',
    '1' : 'room1',
    '2' : 'room2',
    '3' : 'room3',
    '4' : 'room4',
    '5' : 'room5',
    '6' : 'room6'
}

_ROOMS_R = {
    '1' : 'room1',
}

_LIMIT = {
    'https://hskrh.hdc-smart.com',
}

# DEVICE TYPE
DT_LIGHT   = 'light'
DT_OUTLET  = 'outlet'
DT_CLIMATE = 'climate'
DT_FAN     = 'fan'
DT_GAS     = 'gas'
DT_ENERGY  = 'energy'
DT_DOOR    = 'door'

_DEVICES = {
    DT_LIGHT   : '조명',
    DT_OUTLET  : '콘센트',
    DT_CLIMATE : '온도조절기',
    DT_FAN     : '환기장치',
    DT_GAS     : '가스벨브',
    DT_ENERGY  : '에너지',
}

# on / off / low / mid / high
SPEED_LOW  = 'low'
SPEED_MID  = 'mid'
SPEED_HIGH = 'high'
SPEED_LIST = [SPEED_LOW, SPEED_MID, SPEED_HIGH]


# room sensor icon
_R_ICON = {
    'l' : 'mdi:alpha-l-box-outline',
    '1' : 'mdi:numeric-1-box-outline',
    '2' : 'mdi:numeric-2-box-outline',
    '3' : 'mdi:numeric-3-box-outline',
    '4' : 'mdi:numeric-4-box-outline',
    '5' : 'mdi:numeric-5-box-outline',
    '6' : 'mdi:numeric-6-box-outline',
}

_ACTIONS = {
    'LOGIN' : 'Login',
#    'REGIST': 'Registration',
#    'VERIFY': 'Verify',
    'INSTALL': 'Install'
}

#REGIST
CONF_SITE       = 'site'
CONF_IDENTIFIER = 'identifier'
CONF_ALIAS      = 'alias'

TEMP_STEP       = 1

#VERIFY
CONF_TRANSACTION = 'transaction'
CONF_PASSWORD    = 'password'

# API URL
## auth
_LOGIN_URL        = "https://center.hdc-smart.com/v3/auth/login"
_REG_URL          = "https://center.hdc-smart.com/v3/auth/registration"
_VERIFY_URL       = "https://center.hdc-smart.com/v3/auth/verify"

_VALLEY_URL       = "https://center.hdc-smart.com/v3/auth/valley"


## 상태 조회
_SITE_INFO_URL    = "/v2/api/refs/site"
_FEATURES_URL     = "/v2/api/features/apply"

_CTRL_URL         = "/v2/api/features/{}/{}/apply"

_LIGHT_ROOM_URL   = "/v2/api/features/light/{}/apply"
_LIGHT_LIVING_URL = "/v2/api/features/livinglight/1/apply"

_LIGHT_DIMM_ROOM_URL   = "/v2/api/features/dimming_light/{}/apply"
_LIGHT_DIMM_LIVING_URL = "/v2/api/features/dimming_livinglight/1/apply"

_OUTLET_URL       = "/v2/api/features/electric/{}/apply"

_THERMOSTAT_URL   = "/v2/api/features/thermostat/1/apply"

_VENTIL_URL       = "/v2/api/features/ventil/1/apply"

_GAS_URL          = "/v2/api/features/gas/1/apply"

#_ENERGY_URL       = "/v2/api/meter/daily/energies/{}" #now().strftime('%Y/%m/%d')
_ENERGY_URL       = "/v2/api/meter/daily/energies?skip=0&limit=1"
_DOOR_URL         = ""

_ELEV_URL         = "/v2/admin/elevators/home/apply"

#energy
# 내역/아이콘/단위
_ENERGY = {
#  "ENERGY_YEAR":  ['년', '', ''],
#  "ENERGY_MONTH": ['월', '', ''],
#  "ENERGY_DAY":   ['일', '', ''],

  "ENERGY_CNT01": ['전기 총 사용량', 'mdi:flash',      'kWh'],
  "ENERGY_CNT02": ['수도 총 사용량', 'mdi:water-pump', '㎥'],
  "ENERGY_CNT03": ['가스 총 사용량', 'mdi:fire',       '㎥'],
  "ENERGY_CNT04": ['온수 총 사용량', 'mdi:hot-tub',    '㎥'],
  "ENERGY_CNT05": ['난방 총 사용량', 'mdi:radiator',   '㎥'],
#  "ENERGY_CNT06": ['', '', ''],

  "ENERGY_USE01": ['전기 일일 사용량', 'mdi:flash',      'kWh'],
  "ENERGY_USE02": ['수도 일일 사용량', 'mdi:water-pump', '㎥'],
  "ENERGY_USE03": ['가스 일일 사용량', 'mdi:fire',       '㎥'],
  "ENERGY_USE04": ['온수 일일 사용량', 'mdi:hot-tub',    '㎥'],
  "ENERGY_USE05": ['난방 일일 사용량', 'mdi:radiator',   '㎥'],
#  "ENERGY_USE06": ['', '', ''],

#  "PYE_RANK01":   ['', '', ''],
#  "PYE_RANK02":   ['', '', ''],
#  "PYE_RANK03":   ['', '', ''],
#  "PYE_RANK04":   ['', '', ''],
#  "PYE_RANK05":   ['', '', ''],
#  "PYE_RANK06":   ['', '', ''],

#  "PYE_AVG01":    ['동평형 평균 전기 사용량', 'mdi:flash',   'kWh'],
#  "PYE_AVG02":    ['동평형 평균 수도 사용량', 'mdi:water-pump',   '㎥'],
#  "PYE_AVG03":    ['동평형 평균 가스 사용량', 'mdi:fire',    '㎥'],
#  "PYE_AVG04":    ['동평형 평균 온수 사용량', 'mdi:hot-tub', '㎥'],
#  "PYE_AVG05":    ['동평형 평균 난방 사용량', 'mdi:radiator', '㎥'],
#  "PYE_AVG06":    ['', '', ''],

#  "PYE_CHARGE01": ['', '', ''],
#  "PYE_CHARGE02": ['', '', ''],
#  "PYE_CHARGE03": ['', '', ''],
#  "PYE_CHARGE04": ['', '', ''],
#  "PYE_CHARGE05": ['', '', ''],
#  "PYE_CHARGE06": ['', '', ''],

#  "ALL_RANK01":   ['', '', ''],
#  "ALL_RANK02":   ['', '', ''],
#  "ALL_RANK03":   ['', '', ''],
#  "ALL_RANK04":   ['', '', ''],
#  "ALL_RANK05":   ['', '', ''],
#  "ALL_RANK06":   ['', '', ''],

#  "ALL_AVG01":    ['', '', ''],
#  "ALL_AVG02":    ['', '', ''],
#  "ALL_AVG03":    ['', '', ''],
#  "ALL_AVG04":    ['', '', ''],
#  "ALL_AVG05":    ['', '', ''],
#  "ALL_AVG06":    ['', '', ''],

#  "ALL_CHARGE01": ['', '', ''],
#  "ALL_CHARGE02": ['', '', ''],
#  "ALL_CHARGE03": ['', '', ''],
#  "ALL_CHARGE04": ['', '', ''],
#  "ALL_CHARGE05": ['', '', ''],
#  "ALL_CHARGE06": ['', '', ''],

#  "CHARGE01":     ['', '', ''],
#  "CHARGE02":     ['', '', ''],
#  "CHARGE03":     ['', '', ''],
#  "CHARGE04":     ['', '', ''],
#  "CHARGE05":     ['', '', ''],
#  "CHARGE06":     ['', '', ''],

#  "ALL_CNT":      ['', '', ''],
#  "PYE_CNT":      ['', '', ''],

#  "CHARGE_USE":   ['', '', ''],
#  "PYE_RANK_USE": ['', '', ''],
#  "ALL_RANK_USE": ['', '', ''],
#  "PYE_AVG_USE":  ['', '', ''],
#  "ALL_AVG_USE":  ['', '', ''],

#  "craeted_at":   ['', '', ''],
#  "updated_at":   ['', '', ''],
#  "deleted_at":   ['', '', ''],
}


#elevators
ADDRESS = "address"
DIRECTION = "direction"
