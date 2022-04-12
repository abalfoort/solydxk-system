#!/usr/bin/env python3

import re
import os
import threading
from utils import shell_exec, replace_pattern_in_file

# i18n: http://docs.python.org/3/library/gettext.html
import gettext
_ = gettext.translation('solydxk-system', fallback=True).gettext


# Handles general plymouth functions
class Grub():
    def __init__(self, loggerObject=None):
        self.log = loggerObject

    # Get the bootloader
    def getConfig(self):
        grubPath = '/etc/default/grub'
        burgPath = '/etc/default/burg'
        if os.path.isfile(grubPath):  # Grub
            return grubPath
        elif os.path.isfile(burgPath):  # Burg
            return burgPath
        else:
            return None

    # Get current Grub resolution
    def getCurrentResolution(self):
        res = None
        boot = self.getConfig()
        if boot:
            lines = []
            with open(boot, 'r') as f:
                lines = f.read().splitlines()
            for line in lines:
                # Search text for resolution
                matchObj = re.search(r'^GRUB_GFXMODE\s*=[\s"]*([0-9]+x[0-9]+)', line)
                if matchObj:
                    if matchObj.group(1).strip() != "":
                        res = matchObj.group(1)
                        self.write_log("Current grub resolution: %(res)s" % { "res": res })
                    break
        else:
            self.write_log(_("Neither grub nor burg found"), 'warning')
        return res
        
    def write_log(self, message, level='debug'):
        if self.log:
            self.log.write(message, 'Grub', level)


class GrubSave(threading.Thread):
    def __init__(self, resolution, loggerObject):
        threading.Thread.__init__(self)
        self.log = loggerObject
        self.grub = Grub(self.log)
        self.resolution = resolution

    # Save given grub resolution
    def run(self):
        try:
            boot = self.grub.getConfig()

            if boot and self.resolution:
                replace_pattern_in_file(r'^#?GRUB_GFXMODE\s*=.*', 'GRUB_GFXMODE={}'.format(self.resolution), boot)
                # Update grub and initram
                if 'grub' in boot:
                    shell_exec('update-grub')
                else:
                    shell_exec('update-burg')
            else:
                self.write_log(_("Neither grub nor burg found"), 'error')

        except Exception as detail:
            self.write_log(detail, 'exception')
            
    def write_log(self, message, level='debug'):
        if self.log:
            self.log.write(message, 'GrubSave', level)
