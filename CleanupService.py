# -*- coding: utf-8 -*-
# LambdaScrapers Cleanup Service

import os
import re

import xbmc
import xbmcvfs
import xbmcaddon

from lib.lambdascrapers import getAllHosters
from lib.lambdascrapers import providerSources

'''
Temporary service to TRY to make some file changes, and then prevent itself from running again.
'''

ADDON = xbmcaddon.Addon()

# 1) Do the actual housekeeping changes.
try:
    profileFolderPath = xbmc.translatePath(ADDON.getAddonInfo('profile')).decode('utf-8')
    settingsPath = os.path.join(profileFolderPath, 'settings.xml')

    # We rewrite the user settings file while ignoring all obsolete providers.
    if xbmcvfs.exists(settingsPath):
        with open(settingsPath, 'r+') as settingsFile:
            # Parse an XML tree from the settings file.
            from xml.etree import ElementTree
            tree = ElementTree.fromstring(settingsFile.read())
            currentProviders = set(getAllHosters())
            if len(currentProviders) > 0:
                # Traverse the tree backwards so we can safely remove elements on the go.
                for element in reversed(tree):
                    id = element.get('id')
                    if id and id.startswith('provider.') and id.split('.', 1)[1] not in currentProviders:
                        tree.remove(element)
                # Dump the cleaned up XML tree back to the file.
                settingsFile.seek(0)
                settingsFile.write(ElementTree.tostring(tree))
                settingsFile.truncate()
                                
    # Reset obsolete module providers to Lambdascrapers.
    if ADDON.getSetting('module.provider') not in providerSources():
        ADDON.setSetting('module.provider', ' Lambdascrapers')
except:
    pass


# 2) Disable the service in the 'addon.xml' file.
try:
    addonFolderPath = xbmc.translatePath(ADDON.getAddonInfo('path')).decode('utf-8')
    addonXMLPath = os.path.join(addonFolderPath, 'addon.xml')

    # Disabling is done by commenting out the XML line with the service extension so it doesn't run anymore.
    with open(addonXMLPath, 'r+') as addonXMLFile:
        xmlText = addonXMLFile.read()
        serviceFilename = 'CleanupService\.py'
        pattern = r'(<\s*?extension.*?' + serviceFilename + '.*?>)'
        updatedXML = re.sub(pattern, r'<!--\1-->', xmlText, count=1, flags=re.IGNORECASE)
        addonXMLFile.seek(0)
        addonXMLFile.write(updatedXML)
        addonXMLFile.truncate()
except:
    pass
