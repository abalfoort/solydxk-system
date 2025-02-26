#!/usr/bin/env python3 -OO
# -OO: Turn on basic optimizations.  Given twice, causes docstrings to be discarded.

import sys
import argparse
import traceback
from os.path import abspath, dirname
from utils import compare_package_versions, VersionComparison
from dialogs import ErrorDialog
from solydxk_system import SolydXKSystemSettings

# Make sure the right Gtk version is loaded
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject


# Handle arguments
parser = argparse.ArgumentParser(description="SolydXK System")
parser.add_argument('-n', '--nosplash', action="store_true", help='No startup splash.')
args, extra = parser.parse_known_args()
nosplash = args.nosplash

# i18n: http://docs.python.org/3/library/gettext.html
import gettext
_ = gettext.translation('solydxk-system', fallback=True).gettext

scriptDir = abspath(dirname(__file__))


def uncaught_excepthook(*args):
    sys.__excepthook__(*args)
    if not __debug__:
        details = '\n'.join(traceback.format_exception(*args)).replace('<', '').replace('>', '')
        title = _('Unexpected error')
        msg = _('SolydXK System Settings has failed with the following unexpected error. Please submit a bug report!')
        ErrorDialog(title, f"<b>{msg}</b>", f"<tt>{details}</tt>", None, True, 'solydxk')

    sys.exit(1)

sys.excepthook = uncaught_excepthook

if __name__ == '__main__':
    # Create an instance of our GTK application
    try:
        # Calling GObject.threads_init() is not needed for PyGObject 3.10.2 and up
        gtk_ver = (Gtk.get_major_version(), Gtk.get_minor_version(), Gtk.get_micro_version())
        version = '.'.join(map(str, gtk_ver))
        if compare_package_versions(version, '3.10.2') == VersionComparison.SMALLER:
            #print(("Call GObject.threads_init for PyGObject %s" % version))
            GObject.threads_init()

        no_splash = False
        if nosplash:
            no_splash = True
        SolydXKSystemSettings(nosplash=no_splash)
        Gtk.main()
    except KeyboardInterrupt:
        pass
