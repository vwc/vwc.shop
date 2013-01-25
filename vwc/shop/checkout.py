import base64
import hashlib
import random
import urllib2
import cStringIO
import formatter
from htmllib import HTMLParser

from five import grok
from Acquisition import aq_inner
from AccessControl import Unauthorized

from zope.component import getUtility
from zope.component import getMultiAdapter

from plone.app.uuid.utils import uuidToObject
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from plone.registry.interfaces import IRegistry
from plone.app.layout.navigation.interfaces import INavigationRoot

from Products.statusmessages.interfaces import IStatusMessage

from vwc.shop.utils import get_cart

from vwc.shop.interfaces import IVWCShopSettings
from vwc.shop.interfaces import ICartUpdaterUtility

from vwc.shop import MessageFactory as _


class CheckoutForm(grok.View):
    grok.context(INavigationRoot)
    grok.require('zope2.View')
    grok.name('checkout-form')

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
        shipping = self.shipping_fields()
        txnid = self._generate_txn_id()
        txn_id = self._url_quote(txnid)
        order = {}
        shippingIdx = 0
        for item in data:
            if item in shipping and not data[item]:
                shippingIdx += 1
                field_name = item.split('.')[1]
                key = 'billing.' + field_name
            else:
                key = item
            order[item] = data[key]
        if shippingIdx > 0:
            order['shipping.usage'] = True
        txn_data = {}
        txn_data[txn_id] = order
        updater = getUtility(ICartUpdaterUtility)
        txnid = updater.mark(txn_data)
        success_url = portal_url + '/@@checkout?txnid=' + txn_id
        return self.request.response.redirect(success_url)

    def required_fields(self):
        fields = ('billing.firstname', 'billing.lastname',
                  'billing.institution', 'billing.city', 'billing.zipcode',
                  'billing.address1', 'billing.country', 'billing.email',
                  'billing.phone')
        return fields

    def shipping_fields(self):
        fields = ('shipping.address1', 'shipping.address2',
                  'shipping.institution', 'shipping.city',
                  'shipping.country', 'shipping.firstname',
                  'shipping.lastname', 'shipping.zipcode')
        return fields

    def default_value(self, error):
        value = ''
        if error['active'] is False:
            value = error['msg']
        return value

    def _url_quote(self, value):
        if value:
            try:
                encoded_value = urllib2.quote(value.encode('utf-8'))
            except:
                encoded_value = urllib2.quote(value)
            return encoded_value
        else:
            return ''

    def _generate_txn_id(self):
        key = base64.b64encode(
            hashlib.sha256(str(random.getrandbits(256))).digest(),
            random.choice(['rA', 'aZ', 'gQ', 'hH', 'hG', 'aR', 'DD']
                          )).rstrip('==')
        return key


class Checkout(grok.View):
    grok.context(INavigationRoot)
    grok.require('zope2.View')
    grok.name('checkout')

    def update(self):
        context = aq_inner(self.context)
        self.txnid = self.request.get('txnid', None)
        self.errors = {}
        unwanted = ('_authenticator', 'form.button.Submit',
                    'form.button.Enquiry')
        if ('form.button.Submit' in self.request
                or 'form.button.Enquiry' in self.request):
            form = self.request.form
            authenticator = getMultiAdapter((context, self.request),
                                            name=u"authenticator")
            if not authenticator.verify():
                raise Unauthorized
            formdata = {}
            formerrors = {}
            errorIdx = 0
            accept = self.request.get('terms-accept', None)
            if accept is None:
                errorIdx += 1
                formerrors['terms-accept'] = _(u"You need to accept that you "
                                               u"have read and understood the "
                                               u"terms of use.")
            for value in form:
                if value not in unwanted:
                    formdata[value] = form[value]
            formdata['enquiry'] = self.request.get('form.button.Enquiry', None)
            if errorIdx > 0:
                self.errors = formerrors
                IStatusMessage(self.request).add(
                    _(u"Required input missing"),
                    type='error')
            else:
                self._process_order(formdata)

    def _process_order(self, data):
        pstate = getMultiAdapter((self.context, self.request),
                                 name=u"plone_portal_state")
        portal_url = pstate.portal_url()
        settings = self._payment_settings()
        cart = get_cart()
        txn = cart['txn_id']
        orderinfo = txn[self.txnid]
        txnid = self._generate_txn_id()
        txn_id = self._url_quote(txnid)
        success_url = portal_url + '/@@order-processed?oid=' + txn_id
        mto = settings['shop_email']
        envelope_from = orderinfo['billing.email']
        if data['enquiry'] is None:
            order_type = _(u"Order")
        else:
            order_type = _(u"Enquiry")
        subject = _(u'Chromsystems Shop: %s') % order_type
        options = orderinfo
        cart = self.cart()
        options['cartitems'] = cart
        body = ViewPageTemplateFile("enquiry_mail.pt")(self, **options)
        # send email
        mailhost = getToolByName(self.context, 'MailHost')
        mailhost.send(body, mto=mto, mfrom=envelope_from,
                      subject=subject, charset='utf-8')
        IStatusMessage(self.request).add(
            _(u"Your email has been forwarded."),
            type='info')
        return self.request.response.redirect(success_url)

    def _payment_settings(self):
        registry = getUtility(IRegistry)
        settings = registry.forInterface(IVWCShopSettings)
        processor = settings.paypal_url
        info = {}
        info['shop_url'] = settings.shop_url
        info['shop_email'] = settings.shop_email
        if processor == 'Sandbox':
            info['key'] = settings.paypal_sandbox
            info['url'] = 'https://www.sandbox.paypal.com/cgi-bin/webscr'
        else:
            info['key'] = settings.paypal_key
            info['url'] = 'https://www.paypal.com/cgi-bin/webscr'
        return info

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

    def address_information(self):
        cart = get_cart()
        address = cart['txn_id']
        return address[self.txnid]

    def has_cart(self):
        cart = get_cart()
        return len(cart) > 0

    def service_url(self):
        pstate = getMultiAdapter((self.context, self.request),
                                 name=u"plone_portal_state")
        portal_url = pstate.portal_url()
        lang = self.current_lang()
        url = portal_url + '/service-' + lang
        return url

    def localized_value(self, obj, fieldname=None):
        fieldname = fieldname + '_' + self.current_lang()
        return getattr(obj, fieldname, None)

    def current_lang(self):
        context = aq_inner(self.context)
        pstate = getMultiAdapter((context, self.request),
                                 name=u'plone_portal_state')
        lang = pstate.language()
        return lang

    def _url_quote(self, value):
        if value:
            try:
                encoded_value = urllib2.quote(value.encode('utf-8'))
            except:
                encoded_value = urllib2.quote(value)
            return encoded_value
        else:
            return ''

    def _generate_txn_id(self):
        key = base64.b64encode(
            hashlib.sha256(str(random.getrandbits(256))).digest(),
            random.choice(['rA', 'aZ', 'gQ', 'hH', 'hG', 'aR', 'DD']
                          )).rstrip('==')
        return key

    def create_plaintext_message(self, text):
        """ Create a plain-text-message by parsing the html
            and attaching links as endnotes
        """
        plain_text_maxcols = 72
        textout = cStringIO.StringIO()
        formtext = formatter.AbstractFormatter(formatter.DumbWriter(
            textout, plain_text_maxcols))
        parser = HTMLParser(formtext)
        parser.feed(text)
        parser.close()
        # append the anchorlist at the bottom of a message
        # to keep the message readable.
        counter = 0
        anchorlist = "\n\n" + ("-" * plain_text_maxcols) + "\n\n"
        for item in parser.anchorlist:
            counter += 1
            if item.startswith('https://'):
                new_item = item.replace('https://', 'http://')
            else:
                new_item = item
            anchorlist += "[%d] %s\n" % (counter, new_item)
        text = textout.getvalue() + anchorlist
        del textout, formtext, parser, anchorlist
        return text

    def default_value(self, error):
        value = ''
        if error['active'] is False:
            value = error['msg']
        return value

    def image_tag(self, obj):
        scales = getMultiAdapter((obj, self.request), name='images')
        scale = scales.scale('image', scale='thumb')
        imageTag = None
        if scale is not None:
            imageTag = scale.tag()
        return imageTag

    def required_fields(self):
        fields = ()
        return fields

    def eu_countries(self):
        countries = ('Belgium', 'Bulgaria', 'Czech Republic', 'Denmark',
                     'Estonia', 'Ireland', 'Greece', 'Spain', 'France',
                     'Italy', 'Cyprus', 'Latvia', 'Lithuania', 'Luxembourg',
                     'Hungary', 'Malta', 'Netherlands', 'Austria', 'Poland',
                     'Portugal', 'Romania', 'Slovenia', 'Slovakia', 'Finland',
                     'Sweden', 'United Kingdom')
        return countries
