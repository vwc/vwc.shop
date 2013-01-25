from zope.component import getUtility
from zope.site.hooks import getSite
from zope.globalrequest import getRequest
from collective.beaker.interfaces import ISession
from plone.registry.interfaces import IRegistry

from vwc.shop.interfaces import IVWCShopSettings
from vwc.shop.interfaces import IShoppingCartUtility


def format_price(price):
    if price < 0:
        return '-%0.2f EUR' % abs(price)
    else:
        return '%0.2f EUR' % price


def get_cart():
    return getUtility(IShoppingCartUtility).get(getSite())


def wipe_cart():
    return getUtility(IShoppingCartUtility).destroy(getSite())


def update_cart():
    return getUtility(IShoppingCartUtility).update(getSite())


def redirect_to_shop():
    site = getSite()
    request = getRequest()
    registry = getUtility(IRegistry)
    settings = registry.forInterface(IVWCShopSettings)
    shop_url = settings.shop_url
    portal_url = site.absolute_url()
    url = portal_url + shop_url
    request.response.redirect(url)


def redirect_to_cart():
    site = getSite()
    request = getRequest()
    registry = getUtility(IRegistry)
    settings = registry.forInterface(IVWCShopSettings)
    shop_url = settings.shop_url
    portal_url = site.absolute_url()
    url = portal_url + shop_url + '/@@cart'
    request.response.redirect(url)


def redirect_to_checkout():
    site = getSite()
    request = getRequest()
    session = ISession(request)
    session.save()
    registry = getUtility(IRegistry)
    settings = registry.forInterface(IVWCShopSettings)
    shop_url = settings.shop_url
    portal_url = site.absolute_url()
    url = portal_url + shop_url + '/@@checkout'
    request.response.redirect(url)
