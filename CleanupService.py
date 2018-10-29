# -*- coding: utf-8 -*-
# CleanupService.py

import os

import xbmc
import xbmcvfs
import xbmcaddon

'''
Temporary service to TRY to make some file changes, and then remove itself.
'''

ADDON = xbmcaddon.Addon()

# 1) Do the actual file changes you need:

profileFolder = xbmc.translatePath(ADDON.getAddonInfo('profile')).decode('utf-8')
try:
    oldFilePath = os.path.join(profileFolder, 'settings.xml')
    if xbmcvfs.exists(oldFilePath):
        xbmcvfs.delete(oldFilePath)
except:
    pass

# 2) Remove itself from the add-on folder, and overwrite 'addon.xml' to remove the extension point
# that ran this service at Kodi startups.s

addonRootFolder = xbmc.translatePath(ADDON.getAddonInfo('path')).decode('utf-8')
SERVICE_FILENAME = 'CleanupService.py'

try:
    serviceScriptPath = os.path.join(addonRootFolder, SERVICE_FILENAME)
    xbmcvfs.delete(serviceScriptPath)

    addonXMLPath = os.path.join(addonRootFolder, 'addon.xml')
    with open(addonXMLPath, 'r+') as xmlFile:
        originalLines = xmlFile.readlines()
        xmlFile.seek(0)
        for line in originalLines:
            if SERVICE_FILENAME not in line: # Ignore the line with your service entry, accept all others.
                xmlFile.write(line)
        xmlFile.truncate()
    # Now 'addon.xml' doesn't have the service extension point anymore.
except:
    pass
