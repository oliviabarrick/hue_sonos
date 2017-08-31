from nose.tools import *
from colorthief import ColorThief
import requests
import os
import hashlib

def test_rgb_to_xy():
    assert_equal(rgb_to_xy((255, 0, 100)), (0.6464418804969204, 0.22715583071502674))

def test_rgb_to_decimal():
    assert_equal(rgb_to_decimal((255, 0, 100)), (1.0, 0.0, 0.39215686274509803))

def test_gamma_correct():
    assert_equal(gamma_correct(0.5), 0.21404114048223255)
    assert_equal(gamma_correct(0.03), 0.0023219814241486067)

def test_decimal_to_xyz():
    rgb = rgb_to_decimal((255, 0, 100))
    rgb = gamma_correct_rgb(rgb)

    assert_equal(decimal_to_xyz(rgb), (0.67504511375299, 0.23720683670248477, 0.13199523420106749))

def test_xyz_to_xy():
    assert_equal(xyz_to_xy((0.67504511375299, 0.23720683670248477, 0.13199523420106749)), (0.6464418804969204, 0.22715583071502674))

def gamma_correct(color):
    if color > 0.04045:
        return pow((color + 0.055) / 1.055, 2.4)
    else:
        return color / 12.92

def gamma_correct_rgb(rgb):
    return tuple([ gamma_correct(x) for x in rgb ])

def rgb_to_decimal(rgb):
    return tuple([ (x / 255.0) for x in rgb ])

def decimal_to_xyz(rgb):
    red, green, blue = rgb[0], rgb[1], rgb[2]

    x = red * 0.649926 + green * 0.103455 + blue * 0.197109
    y = red * 0.234327 + green * 0.743075 + blue * 0.022598
    z = red * 0.0000000 + green * 0.053077 + blue * 1.035763

    return (x, y, z)

def xyz_to_xy(xyz):
    total = sum(xyz)
    return xyz[0] / total, xyz[1] / total

def rgb_to_xy(rgb):
    decimal = rgb_to_decimal(rgb)
    decimal = gamma_correct_rgb(decimal)

    xyz = decimal_to_xyz(decimal)
    return xyz_to_xy(xyz)

def get_hue_token():
    return open('hue').read()

def get_hue_ip():
    return requests.get('https://www.meethue.com/api/nupnp').json()[0]['internalipaddress']

def hue_api(ip, token, method, endpoint, **kwargs):
    return requests.request(method, 'http://{}/api/{}/{}'.format(ip, token, endpoint), **kwargs)

def get_lights(ip, token):
    return hue_api(ip, token, 'GET', 'lights').json()

def set_light_color(ip, token, light, xy):
    hue_api(ip, token, 'PUT', 'lights/{}/state'.format(light), json={
        "xy": xy
    })

def get_album_art():
    for zone in requests.get('http://127.0.0.1:5005/zones').json():
        if zone['coordinator']['roomName'] != 'Living Room':
            continue

        if 'absoluteAlbumArtUri' not in zone['coordinator']['state']['currentTrack']:
            continue

        return zone['coordinator']['state']['currentTrack']['absoluteAlbumArtUri']

def fetch_album_art(album_art_uri):
    fname = '/tmp/{}'.format(hashlib.md5(album_art_uri).hexdigest())

    if not os.path.exists(fname):
        print 'Downloading album art!'
        album_art = requests.get(album_art_uri).content
        open(fname, 'wb').write(album_art)
    else:
        print 'Album art cached!'

    return fname

def dominant_color(path):
    return ColorThief(fname).get_color(quality=1)

album_art_uri = get_album_art()
if not album_art_uri:
    quit()

print 'Album art URI: {}'.format(album_art_uri)
fname = fetch_album_art(album_art_uri)
rgb = dominant_color(fname)

print 'Album art colors: {}'.format(rgb)

token = get_hue_token()
ip = get_hue_ip()

xy = list(rgb_to_xy(rgb))

for light, data in get_lights(ip, token).items():
    if not data['state']['reachable']:
        continue

    if data['state']['xy'] == xy:
        print 'Light {} already set to {}'.format(light, rgb)

    print 'Setting light {} to {}'.format(light, rgb)
    set_light_color(ip, token, light, xy)
