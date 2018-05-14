import console
import requests
from uuid import uuid4
import urllib.parse
import re
import time
import shelve

CLIENT_ID = 'dbf0a542-ebd1-4ff0-a9a7-55172fbfce35'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:57.0) Gecko/20100101 Firefox/57.0'

GET_VIN_URL = 'https://customer.bmwgroup.com/api/me/vehicles/v2?all=true&brand=BM'
SEND_MSG_URL = 'https://customer.bmwgroup.com/api/vehicle/myinfo/v1'
AUTH_URL = 'https://customer.bmwgroup.com/gcdm/oauth/authenticate'


class BMW:
    userID = ''
    userPass = ''
    vin = ''
    bearerToken = ''
    expires = 0

    def __init__(self, db):
        if db is None:
            raise RuntimeError('empty db')

        # retrieve user id and pass
        try:
            self.userID = db['userID']
            self.userPass = db['userPass']

        except:
            pass

        if self.userID == '' or self.userPass == '':
            while self.userID == '' or self.userPass == '':
                self.userID, self.userPass = console.login_alert('BMWGROUP ID/Password', 'Please input your ID/Password.')

            db['userID'] = self.userID
            db['userPass'] = self.userPass

            db.sync()

        # retrive access token
        try:
            self.bearerToken = db['accessToken']
            self.expires = db['accessTokenExpires']

            # check expires
            if self.expires - int(time.time()) < 0:
                # expired, reset access token
                self.bearerToken = ''

        except:
            pass

        if self.bearerToken == '' or self.expires == 0:
            self.__authenticate()

            db['accessToken'] = self.bearerToken
            db['accessTokenExpires'] = self.expires

            db.sync()

        # retrieve vin
        try:
            self.vin = db['vin']
        except:
            pass

        if self.vin == '':
            self.get_vin()

            db['vin'] = self.vin
            db.sync()

        return

    def __authenticate(self):
        if self.userID == '' or self.userPass == '':
            # never happened
            raise RuntimeError('insufficient user credentials')

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': USER_AGENT
        }

        state = str(uuid4())

        values = {
            'username': self.userID,
            'password': self.userPass,
            'client_id': CLIENT_ID,
            'redirect_uri': 'https://www.bmw-connecteddrive.com/app/default/static/external-dispatch.html',
            'response_type': 'token',
            'scope': 'authenticate_user fupo',
            'state': state,
            'locale': 'KR-ko'
        }

        data = urllib.parse.urlencode(values)

        # request
        r = requests.post(AUTH_URL, data=data, headers=headers, allow_redirects=False)
        # https://www.bmw-connecteddrive.com/app/default/static/external-dispatch.html?error=access_denied

        payload = r.headers['Location']
        if 'error=access_denied' in payload:
            raise RuntimeError('failed to authenticate: access denied')
        else:
            m = re.match(".*access_token=([\w\d]+).*token_type=(\w+).*expires_in=(\d+).*", payload)

            tokenType = (m.group(2))

            self.bearerToken = (m.group(1))
            self.expires = int(time.time()) + int(m.group(3))

        if self.bearerToken == '':
            raise RuntimeError('empty access token')

        if self.expires == 0:
            raise RuntimeError('invalid access token expires')

        return

    def __make_authenticated_headers(self):
        if self.bearerToken is '':
            # never happened
            raise RuntimeError('bearer token is none')

        return {
            'Origin': 'https://www.bmw-connecteddrive.kr',
            'Authorization': 'Bearer ' + self.bearerToken,
            'User-agent': USER_AGENT,
            'Content-Type': 'application/json;charset=UTF-8',
            'Accept': 'application/json',
            'Referer': 'https://www.bmw-connecteddrive.kr'
        }

    def get_vin(self):
        # make request
        headers = self.__make_authenticated_headers()

        r = requests.get(GET_VIN_URL, headers=headers)

        if r.ok is False:
            raise RuntimeError('failed to get vin: %s', r.reason)

        rj = r.json()

        if len(rj) < 1:
            raise RuntimeError('insufficient car info: empty list')

        self.vin = rj[0]['vin']

        if self.vin == '':
            raise RuntimeError('insufficient car info: empty vin')

        return

    def send_message(self, poi, addr, lat, lng):
        # make request
        headers = self.__make_authenticated_headers()
        payload = {
            'vins': [self.vin],
            'message': addr,
            'subject': poi,
            'lat': lat,
            'lng': lng,
        }

        r = requests.post(SEND_MSG_URL, headers=headers, json=payload)

        if r.ok is False:
            raise RuntimeError('failed to send message to car: %s' % r.reason)

        return


def main():
    with shelve.open('test_bmw') as db:
        bmw = BMW(db)

        # print out authentication info
        print('at: %s' % db['accessToken'])
        print('expires: %d' % db['accessTokenExpires'])
        print('vin: %s' % db['vin'])


if __name__ == '__main__':
    main()
