from five import grok
from Products.CMFCore.interfaces import ISiteRoot

from plone.z3cform import layout
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper

from vwc.shop.interfaces import IVWCShopSettings


class VWCShopSettingsEditForm(RegistryEditForm):
    """
    Define form logic
    """
    schema = IVWCShopSettings
    label = u"VWC shop settings"


class VWCShopSettingsView(grok.CodeView):
    """
        View which wrap the settings form using ControlPanelFormWrapper
        to a HTML boilerplate frame.
    """
    grok.name("vwc-shop-settings")
    grok.context(ISiteRoot)

    def render(self):
        view_factor = layout.wrap_form(VWCShopSettingsEditForm,
                                       ControlPanelFormWrapper)
        view = view_factor(self.context, self.request)
        return view()
