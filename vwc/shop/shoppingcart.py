import json
from five import grok
from Acquisition import aq_inner
from AccessControl import Unauthorized
from zope.component import getMultiAdapter
from zope.component import getUtility

from plone.app.uuid.utils import uuidToObject

from plone.app.layout.navigation.interfaces import INavigationRoot

from Products.statusmessages.interfaces import IStatusMessage
from plone.uuid.interfaces import IUUID
from Products.CMFCore.interfaces import IContentish

from vwc.shop.utils import get_cart
from vwc.shop.utils import wipe_cart
from vwc.shop.utils import format_price

from vwc.shop.interfaces import ICartUpdaterUtility

from vwc.shop import MessageFactory as _


class ShoppingCart(grok.View):
    grok.context(INavigationRoot)
    grok.require('zope2.View')
    grok.name('cart')

    def update(self):
        context = aq_inner(self.context)
        self.context_url = context.absolute_url()
        pstate = getMultiAdapter((context, self.request),
                                 name=u"plone_portal_state")
        self.portal_url = pstate.portal_url()
        self.uuid = IUUID(context, None)
        unwanted = ('_authenticator', 'form.button.Submit',
                    'form.button.Clear')
        if 'form.button.Clear' in self.request:
            authenticator = getMultiAdapter((context, self.request),
                                            name=u"authenticator")
            if not authenticator.verify():
                raise Unauthorized
            wipe_cart()
            IStatusMessage(self.request).addStatusMessage(
                _(u"Your shopping cart has successfully been purged"),
                type="info")
            return self.request.response.redirect(self.context_url)
        if 'form.button.Submit' in self.request:
            self.errors = {}
            item = self.request.get('item.uuid', None)
            quantity = self.request.get('item.quantity', None)
            form = self.request.form
            idx = 0
            for item in form:
                if item not in unwanted:
                    fieldname = item.split('.')
                    uuid = fieldname[0]
                    quantity = form[item]
                    if quantity is None or quantity is '':
                        self.errors[item] = _(u"Quantity must be given")
                    else:
                        updater = getUtility(ICartUpdaterUtility)
                        updater.add(uuid, quantity)
                        idx += 1
            IStatusMessage(self.request).add(
                _(u"%s cart items successfully updated") % idx,
                type="info")
            redirect_url = self.context_url + '/@@cart'
            return self.request.response.redirect(redirect_url)

    def cart(self):
        cart = get_cart()
        data = []
        for item in cart:
            if item != 'txn_id':
                info = {}
                product = uuidToObject(item)
                quantity = cart[item]
                info['uuid'] = item
                info['quantity'] = quantity
                info['title'] = self.localized_value(product,
                                                     fieldname='title')
                info['detail'] = self.localized_value(product,
                                                      fieldname='details')
                info['oid'] = product.productCode
                info['url'] = product.absolute_url()
                data.append(info)
        return data

    def has_cart(self):
        cart = get_cart()
        return len(cart) > 0

    def has_txn_info(self):
        cart = get_cart()
        info = False
        if 'txn_id' in cart:
            info = True
        return info

    def address_information(self):
        cart = get_cart()
        address = cart['txn_id']
        return address.keys()[0]

    def cart_total(self):
        total = 0.0
        for item in self.cart():
            value = item['price']
            value = value * int(item['quantity'])
            total = total + value
        return format_price(total)

    def total_is_zero(self):
        return self.cart_total() <= 0

    def localized_value(self, obj, fieldname=None):
        fieldname = fieldname + '_' + self.current_lang()
        return getattr(obj, fieldname, None)

    def current_lang(self):
        context = aq_inner(self.context)
        pstate = getMultiAdapter((context, self.request),
                                 name=u'plone_portal_state')
        lang = pstate.language()
        return lang

    def checkout_url(self):
        if self.has_txn_info():
            txnid = self.address_information()
            url_part = '/@@checkout?txnid=' + txnid
        else:
            url_part = '/@@checkout-form'
        url = self.portal_url + url_part
        return url

    def image_tag(self, obj):
        scales = getMultiAdapter((obj, self.request), name='images')
        scale = scales.scale('image', scale='thumb')
        imageTag = None
        if scale is not None:
            imageTag = scale.tag()
        return imageTag


class CartAddItem(grok.View):
    grok.context(INavigationRoot)
    grok.require('zope2.View')
    grok.name('cart-add-item')

    def update(self):
        context = aq_inner(self.request)
        self.context_url = context.absolute_url()
        item = self.request.get('item.uuid', None)
        qty = self.request.get('quantity', None)
        IStatusMessage(self.request).addStatusMessage(
            _(u"Add item to cart executed: %s %s ") % (item, qty),
            type="info")
        redirect_url = self.context_url() + '/@@cart'
        return self.request.response.redirect(redirect_url)

    def render(self):
        return ''


class CartRemoveItem(grok.View):
    grok.context(INavigationRoot)
    grok.require('zope2.View')
    grok.name('cart-remove-item')

    def update(self):
        context = aq_inner(self.context)
        #self.context_url = context.absolute_url()
        if 'form.button.Submit' in self.request:
            updater = getUtility(ICartUpdaterUtility)
            item_uuid = self.request.get('item_uuid', None)
            item = updater.delete(item_uuid)
            if not item:
                IStatusMessage(self.request).addStatusMessage(
                    _(u"Item could not be removed from the shopping cart. "
                      u"Please try again. If the error should persist, please "
                      u"contact the shop owner"),
                    type="error")
                return self.request.response.redirect(context.absolute_url())
            else:
                IStatusMessage(self.request).addStatusMessage(
                    _(u"Item has been removed from the shopping cart"),
                    type="info")
                return_url = context.absolute_url() + '/@@cart'
                return self.request.response.redirect(return_url)

    def cartitem(self):
        uuid = self.request.get('item_uuid', None)
        if uuid:
            info = {}
            product = uuidToObject(uuid)
            info['uuid'] = uuid
            info['title'] = product.Title()
            info['url'] = product.absolute_url()
            return info


class CartClear(grok.View):
    grok.context(INavigationRoot)
    grok.require('zope2.View')
    grok.name('cart-clear')

    def update(self):
        context = aq_inner(self.context)
        wipe_cart()
        self.context_url = context.absolute_url()
        IStatusMessage(self.request).addStatusMessage(
            _(u"Remove item from cart executed. This is not yet implemented"),
            type="info")
        redirect_url = self.context_url + '/@@cart'
        return self.request.response.redirect(redirect_url)

    def render(self):
        return ''


class CartJSONView(grok.View):
    grok.context(IContentish)
    grok.require('zope2.View')
    grok.name('cart-json-view')

    def render(self):
        return json.dumps(self.cart())

    def cart(self):
        cart = get_cart()
        data = []
        for item in cart:
            info = {}
            product = uuidToObject(item)
            quantity = cart[item]
            info['uuid'] = item
            info['quantity'] = quantity
            if product:
                info['title'] = product.Title()
                info['description'] = product.Description()
                info['image_tag'] = self.image_tag(product)
                info['url'] = product.absolute_url()
                info['price'] = product.price
                info['shipping'] = product.shipping_price
                info['price_pretty'] = format_price(product.price)
                total = int(quantity) * product.price
                info['price_total'] = format_price(total)
            data.append(info)
        return data
