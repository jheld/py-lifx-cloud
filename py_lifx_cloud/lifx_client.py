__author__ = 'jason'
import pycurl
import io
import json
from urllib.parse import urlencode
import time

from lifx_bulb import LifxBulb


class LifxClient(object):
    """
    Interface to manage LIFX bulbs through the cloud server.
    """
    def __init__(self, client_token, server_version='v1beta1',bulbs=[], find_bulbs=True):
        """
        Setup the client with credentials
        :param client_token: secret id for the client
        :type client_token: str
        :return:
        """
        if not client_token:
            raise ValueError('Need a client token; cannot be None/Falsy.')
        self.client_token = client_token
        self.credentials = '{}:'.format(self.client_token)
        self.lifx_server_url = 'https://api.lifx.com/{}/'.format(server_version)
        self.bulbs = bulbs
        if find_bulbs:
            all_lights = self.request('lights/all')
            for light in all_lights:
                new_bulb = LifxBulb(light['id'], light['label'], light['group'], light['power'].lower() == 'on')
                self.bulbs.append(new_bulb)
            print(all_lights)

    def dim_off(self, transition=1.0, bulbs=()):
        # TODO: does not currently handle a different list of bulbs, in so far as making requests
        fields = {'state': 'off', 'duration': transition}
        print(self.request('lights/all/power', method='PUT', fields=fields))

    def request(self, sub_uri, method='GET', fields=None):
        buffer = io.BytesIO()
        c = pycurl.Curl()
        c.setopt(pycurl.URL, '{}{}'.format(self.lifx_server_url, sub_uri))
        c.setopt(pycurl.USERPWD, self.credentials)
        c.setopt(pycurl.WRITEDATA, buffer)
        if method != 'GET':
            if fields is None:
                fields = {}
            if not isinstance(fields, dict):
                raise TypeError('Fields has to be a dict type.')
            encoded_fields= urlencode(fields)
            c.setopt(pycurl.POSTFIELDS, encoded_fields)
            c.setopt(pycurl.CUSTOMREQUEST, method)
        c.perform()
        body = buffer.getvalue().decode('utf-8')
        return json.loads(body)

    def watch_dog_dim(self, bulbs=(), period=2700, transition=300):
        """
        Recurring watch dog "timer" to dim bulbs over time.

        :param bulbs:
        :param period:
        :param transition:
        :return:
        """
        # TODO: generalize this method to take a callable & args and rename to "watch_dog".
        while True:
            time.sleep(period)
            self.dim_off(transition=transition, bulbs=bulbs)
if __name__ == '__main__':
    print('Hello World')
    client_token = str(input('Client token: '))
    client = LifxClient(client_token=client_token)
    # print(client.request('lights/all'))
    # print(client.request('lights/label:Door/toggle', method='POST'))
    client.watch_dog_dim()