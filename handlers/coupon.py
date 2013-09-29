import webapp2
from google.appengine.api import images
import urllib
import jinja2
import os
import datetime
import logging
from models import Business, Coupon


__all__ = ['CouponHandler', 'CouponIDHandler',
           'CouponIDAdminHandler']

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.join(
        os.path.dirname(__file__), 'templates')),
    extensions=['jinja2.ext.autoescape'],
    trim_blocks=True)


def collection_callback(business):
    coupons = []
    for c in Coupon.get_by_business(business.key.id()):
        c.business_name = business.name
        coupons.append(c)
    return coupons


class CouponHandler(webapp2.RequestHandler):
    '''
    HTTP Request Handler, Collection: /coupon/
    '''
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
        coupons = [c
                   for business in query.map(collection_callback)
                   for c in business]

        logging.info(coupons)
        template = JINJA_ENVIRONMENT.get_template('coupon_list.html')
        self.response.status = '200 OK'
        self.response.write(template.render(coupons=coupons))


class CouponIDHandler(webapp2.RequestHandler):
    '''
    HTTP Request Handler, Entity: /coupon/[id]/
    '''
    def get_id(self):
        return int(urllib.unquote(self.request.path.split('/')[2]))

    def get_coupon(self):
        '''
        Returns business entity, and aborts with code 404 if there's no entity
        '''
        b = Coupon.get_by_id(self.get_id())
        if b:
            return b
        self.abort(404)

    def get(self):
        '''
        Returns business entity
        '''
        b = self.get_coupon()
        coupons = []
        for c in Coupon.get_by_business(b.key.id()):
            c = c.dict()
            c['end'] = c['end'] - c['start']
            c['end'] = {
                'days': c['end'].days,
                'hours': c['end'].seconds/3600,
                'minutes': ((c['end'].seconds -
                            3600*(c['end'].seconds/3600))/60),
                'seconds': c['end'].seconds - 60*(c['end'].seconds/60)
            }
            c['start'] = c['start'] - datetime.datetime.now()
            c['start'] = {
                'days': c['start'].days,
                'hours': c['start'].seconds/3600,
                'minutes': ((c['start'].seconds -
                            3600*(c['start'].seconds/3600))/60),
                'seconds': c['start'].seconds - 60*(c['start'].seconds/60)
            }
            coupons.append(c)
        try:
            mark_url = images.get_serving_url(b.mark, size=200)
        except images.BlobKeyRequiredError:
            mark_url = None
        template = JINJA_ENVIRONMENT.get_template('business.html')
        self.response.status = '200 OK'
        self.response.write(template.render(name=b.name,
                                            mark_url=mark_url,
                                            coupons=coupons))


class CouponIDAdminHandler(webapp2.RequestHandler):
    '''
    HTTP Request Handler, Entity: /coupon/[id]/admin/
    '''
    def get_id(self):
        return int(urllib.unquote(self.request.path.split('/')[2]))

    def get_coupon(self):
        '''
        Returns business entity, and aborts with code 404 if there's no entity
        '''
        b = Coupon.get_by_id(self.get_id())
        if b:
            return b
        self.abort(404)

    def get(self):
        b = self.get_coupon()
        template = JINJA_ENVIRONMENT.get_template('coupon_admin.html')
        self.response.status = '200 OK'
        self.response.write(template.render(name=b.name))