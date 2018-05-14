import bmw
import kakao
import shelve
import appex
import console

DB_NAME = 'bmw_sendcar'


def main():
    if not appex.is_running_extension():
        raise RuntimeError('is not in running extention')

    text = appex.get_text()

    if text == '':
        return

    # split lines
    lines = text.split('\n')

    if len(lines) < 1:
        raise RuntimeError('insufficient lines')

    # retrieve poi and address
    poi = ''
    addr = ''

    if lines[0].startswith('[네이버 지도]'):
        if len(lines) < 3:
            raise RuntimeError('insufficient lines for NaverMap')

        if len(lines) > 3:
            poi = lines[1].strip()
            addr = lines[2].strip()
        else:
            addr = lines[1].strip()

    elif lines[0].startswith('[카카오맵]'):
        if len(lines) < 2:
            raise RuntimeError('insufficient lines for KakaoMap')

        ss = lines[0].split(' ', 1)
        if len(ss) > 1:
            poi = ss[1].strip()

        addr = lines[1].strip()

    # check poi and address
    if poi == '':
        poi = addr

    if poi == '' or addr == '':
        raise RuntimeError('failed to retrieve addr from clipboard')

    # do job
    with shelve.open(DB_NAME) as db:
        bmw_api = bmw.BMW(db)
        kakao_api = kakao.KakaoLocal(db)

        # get lat,lon from address
        lat, lon = kakao_api.address_to_coord(addr)

        # send to message vehicle
        bmw_api.send_message(poi, addr, lat, lon)

        # alert to user
        console.alert('BMW SendCar', 'succeed to send to vehicle\nDestination: %s' % poi, 'OK', hide_cancel_button=True)
        
    appex.finish()


if __name__ == '__main__':
    main()
