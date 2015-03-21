__author__ = 'jason'
import pycurl
import io
import json
from urllib.parse import urlencode


class LifxClient(object):
    """
    Interface to managing LIFX bulbs through the cloud server.
    """
    def __init__(self, client_token, server_version='v1beta1'):
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

    def request(self, sub_uri, method='GET', fields=None):
        buffer = io.BytesIO()
        c = pycurl.Curl()
        c.setopt(pycurl.URL, '{}{}'.format(self.lifx_server_url, sub_uri))
        c.setopt(pycurl.USERPWD, self.credentials)
        c.setopt(pycurl.WRITEDATA, buffer)
        if method == 'POST':
            if fields is None:
                fields = {}
            if not isinstance(fields, dict):
                raise TypeError('Fields has to be a dict type.')
            c.setopt(pycurl.POSTFIELDS, urlencode(fields))
        c.perform()
        body = buffer.getvalue().decode('utf-8')
        return json.loads(body)
if __name__ == '__main__':
    print('Hello World')
    client_token = str(input('Client token: '))
    client = LifxClient(client_token=client_token)
    print(client.request('lights/all'))
    print(client.request('lights/label:Door/toggle', method='POST'))