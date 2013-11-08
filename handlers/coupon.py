import webapp2
from RequestHandler import RequestHandler
from google.appengine.api import images
from google.appengine.api import users
import urllib
import jinja2
import os
import datetime
from models import Business, Coupon, User


__all__ = ['CouponHandler',
           'CouponIDHandler',
           'CouponIDAdminHandler']


def collection_callback(business):
    return Coupon.get_by_business(business.key.id())


class CouponHandler(RequestHandler):
    '''
    HTTP Request Handler, Collection: /coupon/
    '''
    def __init__(self, *args, **kwargs):
        super(CouponHandler, self).__init__(*args, **kwargs)
        self.template = self.JINJA_ENVIRONMENT.get_template('coupon_list.jinja')
        self.idtype = int

    def get(self):
        '''
        Lists coupons, filtered by optional parameters
        Parameters:
            name - Name of the business
            lat,lon - Location of the business
        '''
        try:
            lat = float(urllib.unquote(self.request.get('lat')))
            lon = float(urllib.unquote(self.request.get('lon')))
        except ValueError:
            query = Business.query()
        else:
            query = Business.query_location(lat=lat, lon=lon)

        name = urllib.unquote(self.request.get('name'))
        if name:
            query = query.filter(Business.name == name)
        coupons = [c for business in query.map(collection_callback)
                   for c in business]
        coupons = sorted(coupons, lambda x, y: cmp(x.end, y.end))

        self.response.status = '200 OK'
        self.response.write(self.template.render(
            coupons=coupons
        ))


class CouponIDHandler(RequestHandler):
    '''
    HTTP Request Handler, Entity: /coupon/[id]/
    '''
    def __init__(self, *args, **kwargs):
        super(CouponIDHandler, self).__init__(*args, **kwargs)
        self.template = self.JINJA_ENVIRONMENT.get_template('coupon.jinja')
        self.idtype = int

    def get(self):
        '''
        Returns business entity
        '''
        c = self.get_page_entity()
        b = c.business.get()
        self.response.status = '200 OK'
        self.response.write(self.template.render(
            c=c,
            b=b
        ))


class CouponIDAdminHandler(RequestHandler):
    '''
    HTTP Request Handler, Entity: /coupon/[id]/admin/
    '''
    def __init__(self, *args, **kwargs):
        super(CouponIDAdminHandler, self).__init__(*args, **kwargs)
        self.template = self.JINJA_ENVIRONMENT.get_template('coupon_admin.jinja')
        self.idtype = int

    def get(self):
        c = self.get_page_entity()
        b = c.business.get()
        if not is_admin(b):
            self.abort(401)
        self.response.status = '200 OK'
        self.response.write(self.template.render(
        ))
