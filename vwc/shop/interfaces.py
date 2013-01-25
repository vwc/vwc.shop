from zope.interface import Interface
from zope import schema

from vwc.shop import MessageFactory as _


class IVWCShop(Interface):
    """ Generic interface usable as a marker """


class IShoppingCartUtility(Interface):

    def get(context):
        """
        Return the user's shopping cart or none if not found. If
        no cart is available create a new one.
        """

    def destroy(context):
        """ Remove the current user's cart from the session if it exists. """


class ICartUpdaterUtility(Interface):
    """ Utility to update the cart. This utility is callable format_price
        external product implementations as a plugin point
    """

    def add(context):
        """ Add an item to the shopping cart

            @param product_uuid: catalog uuid
            @param quantity: item quantity
        """

    def delete(context):
        """ Delete an item from the shopping cart

            @param product_uuid: catalog uuid
        """

    def mark(context):
        """ Mark cart with a transaction id when submitted for Payments
            processing

            @param txn_id: unique transaction id
        """


class IVWCShopSettings(Interface):
    """ Controlpanel settings for shopified stored in the registry"""

    paypal_key = schema.TextLine(
        title=_(u"Paypal Merchant Key"),
        description=_(u"Please enter your PayPal merchant account key"),
        required=False,
        default=u"",
    )
    paypal_sandbox = schema.TextLine(
        title=_(u"PayPal Sandbox Key"),
        description=_(u"Enter your PayPal sandbox account key. This is "
                      u"usually an E-mail address"),
        required=False,
    )
    paypal_url = schema.Choice(
        title=_(u"Paypal Website Payments Server"),
        values=[_(u"Sandbox"), _(u"Production")],
        required=False,
    )
    shop_email = schema.TextLine(
        title=_(u"Shop E-mail"),
        description=_(u"Enter shop email address that will recieve order "
                      u"mail from customers"),
        required=True,
    )
    shop_url = schema.TextLine(
        title=_(u"Shop URL"),
        description=_(u"Please enter relative URL to the shop content"),
        default=u"/shop",
        required=True,
    )
    email_order_url = schema.TextLine(
        title=_(u"Email Order"),
        description=_(u"Please enter optional email order url (relative to "
                      u"the site root. Leave empty for the default form"),
        required=False,
    )
