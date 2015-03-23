__author__ = 'jason'
import pycurl
import io
import json
from urllib.parse import urlencode
import time
import threading

from lifx_bulb import LifxBulb


class LifxClient(object):
    """
    Interface to manage LIFX bulbs through the cloud server.
    """

    def __init__(self, client_token, server_version='v1beta1', bulbs=None, find_bulbs=True):
        """
        Setup the client with credentials
        :param client_token: secret id for the client
        :type client_token: str
        :return:
        """
        if not bulbs:
            bulbs = []
        if not client_token:
            raise ValueError('Need a client token; cannot be None/Falsy.')
        self.client_token = client_token
        self.credentials = '{}:'.format(self.client_token)
        self.lifx_server_url = 'https://api.lifx.com/{}/'.format(server_version)
        # TODO: make this a dict, label (or id) for the bulb, preferably the label, but I'm not solid on that
        self.bulbs = bulbs
        if find_bulbs:
            all_lights = self.request('lights/all')
            for light in all_lights:
                new_bulb = LifxBulb(light['id'], light['label'], light['group'], light['power'].lower() == 'on')
                self.bulbs.append(LifxBulbManager(new_bulb, self))

    def dim_off(self, transition=1.0):
        # TODO: does not currently handle a different list of bulbs, in so far as making requests
        fields = {'state': 'off', 'duration': transition}
        self.request('lights/all/power', method='PUT', fields=fields)

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
            encoded_fields = urlencode(fields)
            c.setopt(pycurl.POSTFIELDS, encoded_fields)
            c.setopt(pycurl.CUSTOMREQUEST, method)
        c.perform()
        body = buffer.getvalue().decode('utf-8')
        return json.loads(body)

    def watch_dog_dim(self, period=2700, transition=300):
        """
        Recurring watch dog "timer" to dim bulbs over time.

        :param period:
        :param transition:
        :return:
        """
        # TODO: generalize this method to take a callable & args and rename to "watch_dog".
        while True:
            time.sleep(period)
            self.dim_off(transition=transition)

    def watch_dog_is_on(self, bulbs=(), period=300):
        """
        Queries each bulb and updates its powered on/off setting.
        :param bulbs:
        :param period:
        :return:
        """
        while True:
            if not len(bulbs) or len(bulbs) == len(self.bulbs):
                response = self.request('lights/all')
                for bulb_response in response:
                    for bulb in self.bulbs:
                        if bulb.bulb_name == bulb_response['label']:
                            bulb.is_on = bulb_response['power'].lower() == 'on'
                            break
            else:
                for bulb in self.bulbs:
                    response = self.request('lights/label:{}'.format(bulb.bulb_name))
                    bulb.is_on = response['power'].lower() == 'on'
            time.sleep(period)


class LifxBulbManager(object):
    def __init__(self, bulb, lifx_client):
        self.bulb = bulb
        self.lifx_client = lifx_client

    def watch_dog_dim(self, period=2700, transition=300):
        """
        Recurring watch dog "timer" to dim bulbs over time.

        :param period:
        :param transition:
        :return:
        """
        # TODO: generalize this method to take a callable & args and rename to "watch_dog".
        while True:
            time.sleep(period)
            self.lifx_client.dim_off(transition=transition, bulbs=[self.bulb])

    def watch_dog_is_on(self, period=300):
        """
        Queries the bulb and updates its powered on/off setting.
        :param period:
        :return:
        """
        while True:
            response = self.lifx_client.request('lights/label:{}'.format(self.bulb.bulb_name))
            self.bulb.is_on = response['power'].lower() == 'on'
            if not self.bulb.is_on:
                time.sleep(5)
                response = self.lifx_client.request('lights/label:{}'.format(self.bulb.bulb_name))
                self.bulb.is_on = response['power'].lower() == 'on'
            time.sleep(period)


if __name__ == '__main__':
    input_client_token = str(input('Client token: '))
    client = LifxClient(client_token=input_client_token)
    # print(client.request('lights/all'))
    # print(client.request('lights/label:Door/toggle', method='POST'))
    watch_dog_on_thread = threading.Thread(target=client, name=client.watch_dog_is_on,
                                           kwargs={'bulbs': (), 'period': 300})
    watch_dog_on_thread.start()
    watch_dog_dim_thread = threading.Thread(target=client, name=client.watch_dog_dim,
                                            kwargs={'bulbs': (), 'period': 2700, 'transition': 300})
    watch_dog_dim_thread.start()