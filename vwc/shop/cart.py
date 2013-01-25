from five import grok
from zope.interface import implements
from zope.component import getUtility
from zope.globalrequest import getRequest
from plone import api

from collective.beaker.interfaces import ISession
from vwc.shop.interfaces import IShoppingCartUtility
from vwc.shop.interfaces import ICartUpdaterUtility


class ShoppingCartUtility(grok.GlobalUtility):
    implements(IShoppingCartUtility)

    def get(self, portal, key=None):
        cart_id = 'kk.shopified.cart.%s' % '/'.join(
            portal.getPhysicalPath())
        session = ISession(getRequest())
        if cart_id not in session:
            session[cart_id] = dict()
            session.save()
        return session[cart_id]

    def destroy(self, portal, key=None):
        cart_id = 'kk.shopified.cart.%s' % '/'.join(
            portal.getPhysicalPath())
        session = ISession(getRequest())
        if cart_id in session:
            del session[cart_id]
            session.save()


class CartUpdaterUtility(grok.GlobalUtility):
    grok.provides(ICartUpdaterUtility)

    def add(self, item_uuid, quantity=1):
        """
            Add item to shopping cart
        """
        cart = self.cart()
        qty = int(quantity)
        item = self.is_incremental_update(item_uuid, qty)
        if not item:
            cart[item_uuid] = qty
            return cart[item_uuid]

    def delete(self, item_uuid):
        """ Remove item from shopping cart """
        cart = self.cart()
        if item_uuid in cart:
            del cart[item_uuid]
            return item_uuid

    def mark(self, txn_id):
        """ Mark cart when initializing transactions """
        cart = self.cart()
        cart['txn_id'] = txn_id
        return txn_id

    def is_incremental_update(self, product_code, quantity):
        cart = self.cart()
        item_id = product_code
        if item_id in cart:
            cart[item_id] = quantity
            return cart[item_id]
        return None

    def cart(self):
        portal = api.portal.get()
        return getUtility(IShoppingCartUtility).get(portal)
