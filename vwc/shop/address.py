from five import grok
from Acquisition import aq_inner
from AccessControl import Unauthorized

from zope.component import getUtility
from zope.component import getMultiAdapter

from plone.app.layout.navigation.interfaces import INavigationRoot

from Products.statusmessages.interfaces import IStatusMessage

from vwc.shop.utils import get_cart

from vwc.shop.interfaces import ICartUpdaterUtility

from vwc.shop import MessageFactory as _


class AddressBilling(grok.View):
    grok.context(INavigationRoot)
    grok.require('zope2.View')
    grok.name('address-billing')

    def update(self):
        context = aq_inner(self.context)
        self.errors = {}
        unwanted = ('_authenticator', 'form.button.Submit')
        required = self.required_fields()
        if 'form.button.Submit' in self.request:
            form = self.request.form
            authenticator = getMultiAdapter((context, self.request),
                                            name=u"authenticator")
            if not authenticator.verify():
                raise Unauthorized
            formdata = {}
            formerrors = {}
            errorIdx = 0
            for value in form:
                if value not in unwanted:
                    formdata[value] = form[value]
                    if value in required and not form[value]:
                        error = {}
                        error['active'] = True
                        error['msg'] = _(u"This field is required")
                        formerrors[value] = error
                        errorIdx += 1
                    else:
                        error = {}
                        error['active'] = False
                        error['msg'] = form[value]
                        formerrors[value] = error
            if errorIdx > 0:
                self.errors = formerrors
            else:
                self._storeCheckoutData(formdata)

    def _storeCheckoutData(self, data):
        pstate = getMultiAdapter((self.context, self.request),
                                 name=u"plone_portal_state")
        portal_url = pstate.portal_url()
        txn_id = self.get_txnid()
        cart = get_cart()
        address = cart['txn_id']
        order = address.values()[0]
        for item in data:
            order[item] = data[item]
        txn_data = {}
        txn_data[txn_id] = order
        updater = getUtility(ICartUpdaterUtility)
        updater.mark(txn_data)
        IStatusMessage(self.request).add(
            _(u"Billing address successfully updated"),
            type='info')
        success_url = portal_url + '/@@checkout?txnid=' + txn_id
        return self.request.response.redirect(success_url)

    def required_fields(self):
        fields = ('billing.firstname', 'billing.lastname',
                  'billing.institution', 'billing.city', 'billing.zipcode',
                  'billing.address1', 'billing.country', 'billing.email',
                  'billing.phone')
        return fields

    def get_default(self, name):
        cart = get_cart()
        address = cart['txn_id']
        data = address.values()[0]
        try:
            value = data[name]
        except TypeError:
            value = ''
        return value

    def default_value(self, error):
        value = ''
        if error['active'] is False:
            value = error['msg']
        return value

    def get_txnid(self):
        cart = get_cart()
        address = cart['txn_id']
        tid = address.keys()[0]
        return tid


class AddressShipping(grok.View):
    grok.context(INavigationRoot)
    grok.require('zope2.View')
    grok.name('address-shipping')

    def update(self):
        context = aq_inner(self.context)
        self.errors = {}
        unwanted = ('_authenticator', 'form.button.Submit')
        required = self.required_fields()
        if 'form.button.Submit' in self.request:
            form = self.request.form
            authenticator = getMultiAdapter((context, self.request),
                                            name=u"authenticator")
            if not authenticator.verify():
                raise Unauthorized
            formdata = {}
            formerrors = {}
            errorIdx = 0
            for value in form:
                if value not in unwanted:
                    formdata[value] = form[value]
                    if value in required and not form[value]:
                        error = {}
                        error['active'] = True
                        error['msg'] = _(u"This field is required")
                        formerrors[value] = error
                        errorIdx += 1
                    else:
                        error = {}
                        error['active'] = False
                        error['msg'] = form[value]
                        formerrors[value] = error
            if errorIdx > 0:
                self.errors = formerrors
            else:
                self._storeCheckoutData(formdata)

    def _storeCheckoutData(self, data):
        pstate = getMultiAdapter((self.context, self.request),
                                 name=u"plone_portal_state")
        portal_url = pstate.portal_url()
        txn_id = self.get_txnid()
        cart = get_cart()
        address = cart['txn_id']
        order = address.values()[0]
        for item in data:
            order[item] = data[item]
        txn_data = {}
        txn_data[txn_id] = order
        updater = getUtility(ICartUpdaterUtility)
        updater.mark(txn_data)
        IStatusMessage(self.request).add(
            _(u"Shipping address successfully updated"),
            type='info')
        success_url = portal_url + '/@@checkout?txnid=' + txn_id
        return self.request.response.redirect(success_url)

    def required_fields(self):
        fields = ('shipping.address1', 'shipping.city',
                  'shipping.country', 'shipping.firstname',
                  'shipping.lastname', 'shipping.zipcode')
        return fields

    def get_default(self, name):
        cart = get_cart()
        address = cart['txn_id']
        data = address.values()[0]
        try:
            value = data[name]
        except TypeError:
            value = ''
        return value

    def default_value(self, error):
        value = ''
        if error['active'] is False:
            value = error['msg']
        return value

    def get_txnid(self):
        cart = get_cart()
        address = cart['txn_id']
        tid = address.keys()[0]
        return tid


class AddressBase(grok.View):
    grok.context(INavigationRoot)
    grok.require('zope2.View')
    grok.name('address-base')

    def update(self):
        context = aq_inner(self.context)
        self.errors = {}
        unwanted = ('_authenticator', 'form.button.Submit')
        required = self.required_fields()
        if 'form.button.Submit' in self.request:
            form = self.request.form
            authenticator = getMultiAdapter((context, self.request),
                                            name=u"authenticator")
            if not authenticator.verify():
                raise Unauthorized
            formdata = {}
            formerrors = {}
            errorIdx = 0
            for value in form:
                if value not in unwanted:
                    formdata[value] = form[value]
                    if value in required and not form[value]:
                        error = {}
                        error['active'] = True
                        error['msg'] = _(u"This field is required")
                        formerrors[value] = error
                        errorIdx += 1
                    else:
                        error = {}
                        error['active'] = False
                        error['msg'] = form[value]
                        formerrors[value] = error
            if errorIdx > 0:
                self.errors = formerrors
            else:
                self._storeCheckoutData(formdata)

    def _storeCheckoutData(self, data):
        pstate = getMultiAdapter((self.context, self.request),
                                 name=u"plone_portal_state")
        portal_url = pstate.portal_url()
        txn_id = self.get_txnid()
        cart = get_cart()
        address = cart['txn_id']
        order = address.values()[0]
        for item in data:
            order[item] = data[item]
        txn_data = {}
        txn_data[txn_id] = order
        updater = getUtility(ICartUpdaterUtility)
        updater.mark(txn_data)
        IStatusMessage(self.request).add(
            _(u"Address details successfully updated"),
            type='info')
        success_url = portal_url + '/@@checkout?txnid=' + txn_id
        return self.request.response.redirect(success_url)

    def required_fields(self):
        fields = ('billing.email', 'billing.phone')
        return fields

    def get_default(self, name):
        cart = get_cart()
        address = cart['txn_id']
        data = address.values()[0]
        try:
            value = data[name]
        except TypeError:
            value = ''
        return value

    def default_value(self, error):
        value = ''
        if error['active'] is False:
            value = error['msg']
        return value

    def get_txnid(self):
        cart = get_cart()
        address = cart['txn_id']
        tid = address.keys()[0]
        return tid
