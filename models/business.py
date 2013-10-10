from google.appengine.ext import ndb
from google.appengine.api import images
import geobox
import json


class Business(ndb.Model):
    name = ndb.StringProperty('n', required=True)
    lat = ndb.FloatProperty('a', required=True)
    lon = ndb.FloatProperty('o', required=True)
    geoboxes = ndb.StringProperty('g', repeated=True)
    mark = ndb.BlobKeyProperty('m')

    @classmethod
    def new(cls, **kwargs):
        b = Business(**kwargs)
        b.gen_geoboxes()
        return b

    @classmethod
    def query_location(cls, query=None, lat=None, lon=None):
        '''
        Returns a geolocation query that can be further filtered
        '''
        if not query:
            query = Business.query()
        box = geobox.compute(lat, lon, 1, 1)
        query = query.filter(Business.geoboxes == box)
        return query

    @property
    def mark_url(self):
        try:
            mark_url = images.get_serving_url(self.mark, size=200)
        except images.BlobKeyRequiredError:
            mark_url = None

    def gen_geoboxes(self):
        self.geoboxes = [geobox.compute(self.lat, self.lon, 1, 1)]

    def dict(self):
        data = self.to_dict()
        try:
            data['mark'] = images.get_serving_url(self.mark, 200)
        except images.BlobKeyRequiredError:
            data['mark'] = None
        data['id'] = self.key.id()
        del data['geoboxes']
        return data

    def json(self):
        return json.dumps(self.dict())
