import console
import requests
import shelve

KAKAO_API_URL = 'https://dapi.kakao.com/v2/local/search/address.json'


class KakaoLocal:
    restKey = ''

    def __init__(self, db):
        if db is None:
            raise RuntimeError('empty db object')

        # retrieve rest key
        try:
            self.restKey = db['restKey']

        except KeyError:
            # restKey is not in db
            pass

        except Exception as e:
            raise e

        # dialog to input rest key
        if self.restKey is '':
            while self.restKey is '':
                self.restKey = console.input_alert('Input a REST API key from KakaoDevelopers_')

            # store restKey
            db['restKey'] = self.restKey
            db.sync()

    def address_to_coord(self, addr):
        # build request
        headers = {
            'Authorization': 'KakaoAK ' + self.restKey
        }

        values = {
            'query': addr
        }

        # query to Kakao API server
        r = requests.get(KAKAO_API_URL, params=values, headers=headers, allow_redirects=False)

        if not r.ok:
            raise RuntimeError('failed to request to KAKAO server (%s)' % r.reason)

        # retrieve latitude, longitude
        rj = r.json()

        docs = rj['documents']

        if len(docs) < 1:
            raise RuntimeError('insufficient documents')

        lng = docs[0]['x']
        lat = docs[0]['y']

        return lat, lng


def main():
    with shelve.open('test_kakao') as db:
        kakao = KakaoLocal(db)
        lat, lng = kakao.address_to_coord('경기도 용인시 수지구 동천로35번길 11')

        print('lat: %s' % lat)
        print('lng: %s' % lng)


if __name__ == '__main__':
    main()
