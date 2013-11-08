import webapp2
import urllib
import json

from google.appengine.ext import ndb
from google.appengine.api import users
from models import User, Coupon, Business


__all__ = ['UserHandler', 'UserIDHandler',
           'UserIDCouponHandler', 'UserIDCouponIDHandler']


def is_admin(uid=None, bid=None):
    if users.is_current_user_admin():
        return True
    cur_user = users.get_current_user().user_id()
    if uid:
        if uid == cur_user:
            return True
        if bid:
            return cur_user in Business.get_by_id(bid).admins
    return False


def authenticate(uid=None, bid=None):
    if not is_admin(uid, bid):
        webapp2.abort(401)


class UserHandler(webapp2.RequestHandler):
    '''
    HTTP Request Handler: /api/user
    '''
    def filter_by(self, query, key, value, type=str):
        try:
            value = type(urllib.unquote(self.request.get(value)))
        except ValueError:
            return query
        if not value:
            return query
        return query.filter(key == value)

    def get(self):
        '''
        HTTP GET Method Handler
        Returns a list of user URI's
        '''
        q = User.query()
        q = self.filter_by(q, User.name, 'name')
        q = self.filter_by(q, User.address.number, 'number', int)
        q = self.filter_by(q, User.address.street, 'street')
        q = self.filter_by(q, User.address.city, 'city')
        q = self.filter_by(q, User.address.zip, 'zip', int)
        q = self.filter_by(q, User.address.country, 'country')
        q = self.filter_by(q, User.phone, 'phone', int)

        self.response.status = '200 OK'
        for key in q.iter(keys_only=True):
            self.response.write(str(key.id()) + '\n')

    def post(self):
        '''
        HTTP POST Method Handler
        Creates new user from JSON representation
        '''
        authenticate()
        name = urllib.unquote(self.request.get('name'))
        user = User(name=name)
        key = user.put()
        self.response.status = '200 OK'
        self.response.write('/api/user/' + key.id())


class UserIDHandler(webapp2.RequestHandler):
    '''
    HTTP Request Handler: /api/user/[id]
    '''
    def get_id(self):
        return urllib.unquote(self.request.path.split('/')[3])

    def get(self):
        '''
        HTTP GET Method Handler
        Returns JSON representation of coupon
        '''
        user = User.get_by_id(self.get_id())
        self.response.status = '200 OK'
        self.response.write(user.json())

    def put(self):
        '''
        HTTP PUT Method Handler
        Creates new user at the requested URI
        '''
        authenticate(self.get_uid())
        data = json.loads(self.request.body)
        try:
            data['held_coupons'] = [ndb.Key('Coupon', i) for i in
                                    data['held_coupons']]
        except KeyError:
            pass
        user = User.get_by_id(self.get_id())
        for key, value in data.iteritems():
            setattr(user, key, value)
        key = user.put()
        self.response.status = '200 OK'
        self.response.write('/api/user/' + str(key.id()))

    def delete(self):
        '''
        HTTP DELETE Method Handler
        Deletes exiting user
        '''
        user = User.get_by_id(self.get_id())
        user.key.delete()
        self.response.status = '204 No Content'


class UserIDCouponHandler(webapp2.RequestHandler):
    '''
    HTTP Request Handler: /api/user/[id]/coupons/
    '''
    def get_uid(self):
        try:
            return urllib.unquote(self.request.path.split('/')[3])
        except ValueError:
            self.abort(404)

    def get_bid(self):
        try:
            return int(urllib.unquote(self.request.get('business')))
        except ValueError:
            self.abort(400)

    def get_cid(self):
        try:
            return int(urllib.unquote(self.request.get('coupon')))
        except ValueError:
            self.abort(400)

    def get(self):
        '''
        HTTP POST Method Handler
        Searches user's coupons
        '''
        authenticate(self.get_uid(), self.get_bid())
        self.response.status = '200 OK'
        for k in Coupon.get_by_user_and_business(self.get_uid(),
                                                 self.get_bid(),
                                                 keys_only=True):
            self.response.write(str(k.id()) + '\n')

    def post(self):
        '''
        HTTP POST Method Handler
        Gives user a coupon
        '''
        authenticate(self.get_uid())
        user = User.get_by_id(self.get_uid())
        coupon = Coupon.get_by_id(self.get_cid())
        if not coupon:
            self.abort(400)
        if not user:
            self.abort(400)
        if coupon.key not in user.held_coupons:
            user.held_coupons.append(coupon.key)
            user.put()
        self.response.status = '200 OK'
        self.response.write('/api/user/' + str(user.key.id()))


class UserIDCouponIDHandler(webapp2.RequestHandler):
    '''
    HTTP Request Handler: /api/user/[id]/coupons/[id]
    '''
    def get_uid(self):
        try:
            return urllib.unquote(self.request.path.split('/')[3])
        except ValueError:
            self.abort(404)

    def get_cid(self):
        try:
            return int(urllib.unquote(self.request.path.split('/')[5]))
        except ValueError:
            self.abort(404)

    def delete(self):
        '''
        HTTP DELETE Method Handler
        Takes coupon away from user
        '''
        user = User.get_by_id(self.get_uid())
        if not user:
            self.abort(400)
        coupon_key = ndb.Key('Coupon', self.get_cid())
        authenticate(self.get_uid(), coupon_key.get().business.id())
        user.held_coupons.remove(coupon_key)
        user.put()
        self.response.status = '204 No Content'
