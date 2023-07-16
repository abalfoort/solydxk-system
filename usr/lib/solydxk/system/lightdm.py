#!/usr/bin/env python3

import os
import re
from glob import glob
from utils import replace_pattern_in_file

GREETER_CONF = '/etc/lightdm/lightdm-gtk-greeter.conf'

class LightDM():
    def __init__(self, logger_object=None):
        self.log = logger_object

    def _lightdm_default_value(self, pattern, group_nr=0):
        if not os.path.exists(GREETER_CONF):
            self.write_log(f"LightDM configuration file not found: {GREETER_CONF}", 'warning')
            return None

        lines = []
        with open(file=GREETER_CONF, mode='r', encoding='utf-8') as lightdm_fle:
            lines = lightdm_fle.read().splitlines()
        for line in lines:
            # Search text for resolution
            match = re.search(pattern, line)
            if match:
                return match.group(group_nr).strip()
        return None

    def current_theme(self):
        return self._lightdm_default_value(r'^theme-name\s*=(.*)', 1)

    def current_background(self):
        return self._lightdm_default_value(r'^background\s*=(.*)', 1)

    def save(self, theme_name):
        if not os.path.exists(GREETER_CONF):
            self.write_log(f"LightDM configuration file not found: {GREETER_CONF}", 'warning')
            return

        # Search for background.* image
        backgrounds = glob(fr'/usr/share/desktop-base/{theme_name}*/login/background.*')
        if backgrounds:
            breeze_theme = 'Breeze' if 'light' in theme_name else 'Breeze-Dark'
            # Save found background with theme
            replace_pattern_in_file(r'^background\s*=.*', f'background={backgrounds[0]}',
                                    GREETER_CONF)
            replace_pattern_in_file(r'^theme-name\s*=.*', f'theme-name={breeze_theme}',
                                    GREETER_CONF)
            self.write_log(f'LightDM background set: {backgrounds[0]}')

    def write_log(self, message, level='debug'):
        if self.log:
            self.log.write(message, 'LightDM', level)
