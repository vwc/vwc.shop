from five import grok
from Acquisition import aq_inner

from vwc.shop.utils import get_cart
from vwc.shop.utils import wipe_cart

from plone.app.layout.navigation.interfaces import INavigationRoot


class ConfirmationView(grok.View):
    grok.context(INavigationRoot)
    grok.require('zope2.View')
    grok.name('order-confirmation')

    def update(self):
        self.txn_id = self.request.get('txnid', None)


class OrderProcessed(grok.View):
    grok.context(INavigationRoot)
    grok.require('zope2.View')
    grok.name('order-processed')

    def update(self):
        context = aq_inner(self.context)
        here_url = context.absolute_url()
        cart = get_cart()
        order_id = self.request.get('oid', '')
        txn_id = cart['txn_id']
        txnid = txn_id[0]
        if self.is_equal(order_id, txnid):
            self.next_url = here_url + '/@@order-confirmation?txnid=' + txn_id
            wipe_cart()

    def render(self):
        return self.request.response.redirect(self.next_url)

    def is_equal(self, a, b):
        if len(a) != len(b):
            return False
        result = 0
        for x, y in zip(a, b):
            result |= ord(x) ^ ord(y)
        return result == 0
