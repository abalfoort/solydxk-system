#!/usr/bin/env python3

import os
import re
import shutil
from glob import glob
from queue import Queue
# abspath, dirname, join, expanduser, exists, basename
from os.path import join, abspath, dirname, isdir, exists, basename
from threading import Thread
from localize import LocaleInfo, Localize
from udisks2 import Udisks2
from logger import Logger
from treeview import TreeViewHandler
from combobox import ComboBoxHandler
from utils import getoutput, ExecuteThreadedCommands, \
                  shell_exec, human_size, has_internet_connection, \
                  get_debian_name, in_virtual_box, get_apt_force, is_running_live, \
                  get_device_from_uuid, get_label, is_package_installed, \
                  get_logged_user, get_uuid, compare_package_versions, VersionComparison, \
                  get_current_resolution, get_resolutions, is_xfce_running, \
                  is_process_running, has_value_in_multi_array, get_current_aspect_ratio
from dialogs import MessageDialog, QuestionDialog, InputDialog, \
                    WarningDialog
from apt_sources import Apt
from encryption import is_encrypted, create_keyfile, write_crypttab, \
                       connect_block_device, cleanup_passphrase
from endecrypt_partitions import EnDecryptPartitions, ChangePassphrase
from plymouth import Plymouth
from grub import Grub
from splash import Splash
from lightdm import LightDM

# Make sure the right Gtk version is loaded
import gi
gi.require_version('Gtk', '3.0')
# from gi.repository import Gtk, GdkPixbuf, GObject, Pango, Gdk
from gi.repository import Gtk, GLib

# i18n: http://docs.python.org/3/library/gettext.html
import gettext
_ = gettext.translation('solydxk-system', fallback=True).gettext

TMPMOUNT = '/mnt/solydxk-system'

class SolydXKSystemSettings():
    """class for the main window"""    
    def __init__(self, nosplash=False):
        # Load and install test data for the device manager
        self.test_devices = False

        # Get script and data paths
        self.script_dir = abspath(dirname(__file__))
        self.share_dir = self.script_dir.replace('lib', 'share')
        self.title = "SolydXK System Settings"

        # Show splash screen while loading
        if not nosplash:
            b_img = join(self.share_dir, 'images/splash-bgk.png')
            f_clr = '#243e4b'
            if is_xfce_running():
                b_img = join(self.share_dir, 'images/splash-bgx.png')
                f_clr = '#502800'
            splash = Splash(title=self.title, font='Roboto Slab 18',
                            font_weight='bold', font_color=f_clr, background_image=b_img)
            splash.start()

        # Init logging
        self.log_file = "/var/log/solydxk-system.log"
        self.log = Logger(self.log_file, addLogTime=True, maxSizeKB=5120)
        sep_line = '=' * 35
        self.log.write(sep_line, 'init')
        self.log.write(f'>>> Start {self.title} <<<', 'init')
        self.log.write(sep_line, 'init')

        # Load window and widgets
        self.builder = Gtk.Builder()
        self.builder.add_from_file(join(self.share_dir, 'solydxk_system.glade'))

        # Preferences window objects
        builder = self.builder.get_object
        self.window = builder("windowPref")
        self.window.set_title(self.title)
        self.nbPref = builder('nbPref')
        self.btnSaveBackports = builder('btnSaveBackports')
        self.btnSaveMirrors = builder('btnSaveMirrors')
        self.lblRepositories = builder('lblRepositories')
        self.tvMirrors = builder("tvMirrors")
        self.chkEnableBackports = builder("chkEnableBackports")
        self.btnRemoveHoldback = builder("btnRemoveHoldback")
        self.btnHoldback = builder("btnHoldback")
        self.tvHoldback = builder("tvHoldback")
        self.tvAvailable = builder("tvAvailable")
        self.tvLocale = builder("tvLocale")
        self.tvPartitions = builder("tvPartitions")
        self.lblLocaleUserInfo = builder("lblLocaleUserInfo")
        self.cmbTimezoneContinent = builder("cmbTimezoneContinent")
        self.cmbTimezone = builder("cmbTimezone")
        self.btnSaveLocale = builder("btnSaveLocale")
        self.lblEncryption = builder("lblEncryption")
        self.chkEnableEncryption = builder("chkEnableEncryption")
        self.boxEncryptionEnable = builder("boxEncryptionEnable")
        self.btnEncrypt = builder("btnEncrypt")
        self.btnDecrypt = builder("btnDecrypt")
        self.btnRefresh = builder("btnRefresh")
        self.btnChangePassphrase = builder("btnChangePassphrase")
        self.btnCreateKeyfile = builder("btnCreateKeyfile")
        self.progressbar = builder("progressbar")
        self.txtPassphrase1 = builder("txtPassphrase1")
        self.txtPassphrase2 = builder("txtPassphrase2")
        self.imgPassphraseCheck = builder("imgPassphraseCheck")
        self.tvCleanup = builder("tvCleanup")
        self.btnCleanup = builder("btnCleanup")
        self.btnSaveFstabMounts = builder("btnSaveFstabMounts")
        self.tvFstabMounts = builder("tvFstabMounts")
        self.tvDeviceDriver = builder("tvDeviceDriver")
        self.btnSaveDeviceDriver = builder("btnSaveDeviceDriver")
        self.btnHelpDeviceDriver = builder("btnHelpDeviceDriver")
        self.chkBackportsDeviceDriver = builder("chkBackportsDeviceDriver")
        self.swSplash = builder("swSplash")
        self.tvSplash = builder("tvSplash")
        self.swGrub = builder("swGrub")
        self.tvGrub = builder("tvGrub")
        self.btnSaveSplash = builder("btnSaveSplash")
        self.imgSplashPreview = builder("imgSplashPreview")
        self.cmbSplashResolution = builder("cmbSplashResolution")

        # GUI translations
        builder("btnLogDeviceDriver").set_label(_("View log"))
        self.btnSaveBackports.set_label(_("Save backports"))
        self.btnSaveMirrors.set_label(_("Save mirrors"))
        self.btnRemoveHoldback.set_label(_("Remove"))
        self.btnHoldback.set_label(_("Hold back"))
        self.lblRepositories.set_label(_("Repositories"))
        self.lblEncryption.set_label(_("Encryption"))
        builder("lblPassphrase").set_label(_("Passphrase (6+ chrs)"))
        self.btnEncrypt.set_label(_("Encrypt"))
        self.btnDecrypt.set_label(_("Decrypt"))
        self.btnChangePassphrase.set_label(_("Change passphrase"))
        self.btnCreateKeyfile.set_label(_("Manually create key file"))
        builder("lblLocalization").set_label(_("Localization"))
        builder("lblTimezone").set_label(_("Timezone"))
        builder("lblLocale").set_label(_("Locale"))
        self.chkEnableEncryption.set_label(_("Enable encryption: this will temporarily mount any not mounted partition."))
        builder("lblEncryptionInfo").set_label(_("Encrypt partitions and keep your data safe.\n"
                                            "Warning: backup your data before you continue!\n"
                                            "Note: you can Ctrl-left click to select multiple partitions."))
        builder("lblLocaleInfo").set_label(_("Configure your locales (one as default) and time zone.\n"
                                        "Note: make sure you have an internet connection to localize your software."))
        builder("lblBackportsInfo").set_label(_("Enable the Backports repository if you need a newer software version.\n"
                                           "Warning: installing software from the backports repository may de-stabalize your system.\n"
                                           "Use at your own risk!"))
        builder("lblMirrorsInfo").set_label(_("Select the fastest repository for your updates.\n"
                                         "Note: make sure you have an internet connection."))
        builder("lblHoldback").set_label(_("Hold back packages"))
        builder("lblHoldbackText").set_label(_("Held back packages"))
        builder("lblAvailableText").set_label(_("Available packages"))
        builder("lblHoldbackInfo").set_label(_("Hold back individual packages.\n"
                                          "Holding back a package will prevent this package from being updated."))
        self.btnSaveLocale.set_label(_("Save locale"))
        self.installed_title = _('Installed')
        self.locale_title = _('Locale')
        self.language_title = _('Language')
        self.default_title = _('Default')
        self.no_passphrase_msg = _("Please provide a passphrase (6+ characters).")
        self.mount_error = _("Could not mount {0}\nPlease mount {0} and refresh when done.")
        builder("lblCleanup").set_label(_("Cleanup"))
        builder("lblCleanupInfo").set_label(_("Remove unneeded packages\n"
                                          "Pre-selected packages are safe to remove (autoremove).\n"
                                          "Other packages: remove with caution!"))
        builder("lblCleanupText").set_label(_("Unneeded packages"))
        builder("lblFstabMounts").set_label(_("Fstab mounts"))
        builder("lblCurrentFstabMounts").set_label(_("Fstab mounts"))
        builder("lblFstabMountsInfo").set_label(_("Mount additional partitions on boot with Fstab.\n"
                                            "When added to Fstab, the partition will be mounted in /media."))
        self.btnSaveFstabMounts.set_label(_("Save Fstab mounts"))
        self.btnSaveDeviceDriver.set_label(_("Save drivers"))
        self.chkBackportsDeviceDriver.set_label(_("Use Backports"))
        builder("lblDeviceDriver").set_label(_("Device Driver"))
        builder("lblDeviceDriverInfo").set_label(_("Install drivers for supported hardware.\n"
                                          "Note: this will install the open drivers, NOT the proprietary drivers."))
        builder("lblSplash").set_label(_("Boot splash"))
        builder("lblSplashInfo").set_label(_("Select a theme for Plymouth and Grub."))
        builder("lblSplashText").set_label(_("Plymouth themes"))
        builder("lblGrubText").set_label(_("Grub themes"))
        self.btnSaveSplash.set_label(_("Save"))
        builder("lblSplashResolution").set_label(_("Resolution"))

        # Initiate the treeview handlers and connect the custom toggle events
        self.tvMirrorsHandler = TreeViewHandler(self.tvMirrors)
        self.tvMirrorsHandler.connect('checkbox-toggled', self.on_tvMirrors_toggle)
        self.tvHoldbackHandler = TreeViewHandler(self.tvHoldback)
        self.tvAvailableHandler = TreeViewHandler(self.tvAvailable)
        self.tvLocaleHandler = TreeViewHandler(self.tvLocale)
        self.tvLocaleHandler.connect('checkbox-toggled', self.on_tvLocale_toggled)
        self.tvPartitionsHandler = TreeViewHandler(self.tvPartitions)
        self.tvCleanupHandler = TreeViewHandler(self.tvCleanup)
        self.tvFstabMountsHandler = TreeViewHandler(self.tvFstabMounts)
        self.cmbTimezoneContinentHandler = ComboBoxHandler(self.cmbTimezoneContinent)
        self.cmbTimezoneHandler = ComboBoxHandler(self.cmbTimezone)
        self.tvDeviceDriverHandler = TreeViewHandler(self.tvDeviceDriver)
        self.tvDeviceDriverHandler.connect('checkbox-toggled', self.on_tvDeviceDriver_toggled)
        self.tvSplashHandler = TreeViewHandler(self.tvSplash)
        self.tvSplashHandler.connect('checkbox-toggled', self.on_tvSplashHandler_toggled)
        self.tvGrubHandler = TreeViewHandler(self.tvGrub)
        self.tvGrubHandler.connect('checkbox-toggled', self.on_tvGrubHandler_toggled)
        self.cmbSplashResolutionHandler = ComboBoxHandler(self.cmbSplashResolution)

        # Initialize
        self.queue = Queue(-1)
        self.threads = {}
        self.exclude_suites = ['backports', 'security', 'updates']
        self.current_debian_repo = ''
        self.holdback = []
        self.available = []
        self.locales = []
        self.new_default_locale = ''
        self.partitions = []
        self.my_partitions = []
        self.my_passphrase = ''
        self.html_dir = join(self.share_dir, 'html')
        self.help_file = join(self.language_dir(), 'help.html')
        self.helpdd_file = join(self.language_dir(), 'helpdd.html')
        self.udisks2 = Udisks2()
        self.keyfile_path = None
        self.debian_name = get_debian_name()
        self.encrypt_col_types = ['GdkPixbuf.Pixbuf', 'str', 'str', 'str', 'str', 'str', 'str']
        self.encrypt_list_header = [['', _('Partition'), _('Label'), _('File system'),
                                     _('Total size'), _('Free size'), _('Mount point')]]
        self.endecrypt_success = True
        self.encrypt = False
        self.failed_mount_devices = []
        self.boot_partition = None
        self.changed_devices = []
        self.hardware = []
        self.plymouth = Plymouth(self.log)
        self.current_plymouth_theme = self.plymouth.current_theme()
        self.installed_plymouth_themes = self.plymouth.installed_themes()
        self.grub = Grub(self.log)
        self.lightdm = LightDM(self.log)

        # Collect data and disable tabs when running live:
        # Device Driver, Fstab mounts, Localization, Hold back packages, Cleanup
        self.apt = Apt()
        self.live = is_running_live()
        self.active_mirrors = self.apt.get_mirror_data(exclude_mirrors=self.exclude_suites)
        self.dead_mirrors = self.apt.get_mirror_data(get_dead_mirrors=True)
        self.mirrors = self.list_mirrors()
        self.fill_treeview_mirrors()
        self.boxEncryptionEnable.set_sensitive(False)
        if self.live:
            self.nbPref.get_nth_page(0).set_visible(False)
            self.nbPref.get_nth_page(2).set_visible(False)
            self.nbPref.get_nth_page(3).set_visible(False)
            self.nbPref.get_nth_page(5).set_visible(False)
            self.nbPref.get_nth_page(6).set_visible(False)
            self.nbPref.get_nth_page(7).set_visible(False)
        else:
            self.backports = self.apt.get_backports()
            self.locale_info = LocaleInfo()
            # holdback before cleanup: held back packages needed for cleanup list
            self.fill_treeview_holdback()
            self.fill_treeview_cleanup()
            self.fill_treeview_device_driver()
            self.fill_treeview_available()
            self.fill_cmb_timezone_continent()
            self.fill_treeview_locale()
            if self.backports:
                self.chkEnableBackports.set_active(True)
            else:
                self.chkBackportsDeviceDriver.set_sensitive(False)
            if not self.installed_plymouth_themes and not self.grub.installed_themes:
                self.nbPref.get_nth_page(7).set_visible(False)
            else:
                self.fill_treeview_installed_grub()
                self.fill_treeview_installed_plymouth()
                self.fill_cmb_splash_resolution()

        # Disable this for later implementation
        self.btnCreateKeyfile.set_visible(False)

        # Connect the signals and show the window
        self.builder.connect_signals(self)
        self.window.show()

        # Destroy splash screen
        if not nosplash:
            splash.destroy()

        # In case of encrypted partitions, we can only list partitions when the splash is done
        if not self.live:
            self.fill_treeview_fstab_partitions()

    # ===============================================
    # Main window functions
    # ===============================================

    def on_btnSaveBackports_clicked(self, widget):
        self.save_backports()

    def on_btnSaveMirrors_clicked(self, widget):
        self.save_mirrors()

    def on_btnCancel_clicked(self, widget):
        self.window.destroy()

    def on_btnRemoveHoldback_clicked(self, widget):
        self.remove_holdback()

    def on_btnHoldback_clicked(self, widget):
        self.add_holdback()

    def on_cmbTimezoneContinent_changed(self, widget):
        self.fill_cmb_timezone(self.cmbTimezoneContinentHandler.getValue())

    def on_btnSaveLocale_clicked(self, widget):
        self.save_locale()

    def on_btnRefreshFstab_clicked(self, widget):
        self.fill_treeview_fstab_partitions()

    def on_chkEnableEncryption_toggled(self, widget):
        active = widget.get_active()
        if active:
            self.fill_treeview_partition()
            self.save_my_partitions()
        else:
            self.temp_unmount_all()
            self.tvPartitionsHandler.fillTreeview(contentList=self.encrypt_list_header,
                                                  columnTypesList=self.encrypt_col_types,
                                                  firstItemIsColName=True,
                                                  multipleSelection=True)
        self.boxEncryptionEnable.set_sensitive(active)

    def on_btnEncrypt_clicked(self, widget):
        self.encrypt = True
        self.endecrypt()

    def on_btnDecrypt_clicked(self, widget):
        self.encrypt = False
        self.endecrypt()

    def on_btnChangePassphrase_clicked(self, widget):
        self.change_passphrase()

    def on_btnCreateKeyfile_clicked(self, widget):
        self.set_buttons_state(False)
        self.write_partition_configuration(True)
        self.set_buttons_state(True)

    def on_txtPassphrase1_changed(self, widget=None):
        self.check_passphrase()

    def on_txtPassphrase2_changed(self, widget=None):
        self.check_passphrase()

    def on_btnRefresh_clicked(self, widget):
        self.set_buttons_state(False)
        self.fill_treeview_partition()
        self.set_buttons_state(True)

    def on_btnHelp_clicked(self, widget):
        # Open the help file as the real user (not root)
        shell_exec(f"open-as-user \"{self.help_file}\"")

    def on_tvPartitions_selection_changed(self, widget):
        self.save_my_partitions()

    def on_btnCleanup_clicked(self, widget):
        self.remove_unneeded_packages()

    def on_btnSaveFstabMounts_clicked(self, widget):
        self.save_fstab_mounts()

    def on_btnSaveDeviceDriver_clicked(self, widget):
        self.install_device_drivers()

    def on_btnLogDeviceDriver_clicked(self, widget):
        shell_exec(f"open-as-user \"{self.log_file}\"")

    def on_btnHelpDeviceDriver_clicked(self, widget):
        shell_exec(f"open-as-user \"{self.helpdd_file}\"")

    def on_btnSaveSplash_clicked(self, widget):
        self.save()

    def on_chkEnableSplash_toggled(self, widget):
        self.swSplash.set_sensitive(widget.get_active())

    # ===============================================
    # Fstab mount functions
    # ===============================================

    def fill_treeview_fstab_partitions(self):
        fs_partitions = []

        # Add headers
        fs_partitions.append([_('Add'), _('Partition'), _('Label')])

        # Get available partitions
        self.fill_partitions(False)

        for partition in self.partitions:
            # Check if partition is listed in fstab
            in_fstab = '/etc/fstab' in partition['fstab_path']
            fs_partitions.append([in_fstab, partition['device'], partition['label']])

        column_types = ['bool', 'str', 'str']

        # Fill treeview
        self.tvFstabMountsHandler.fillTreeview(contentList=fs_partitions,
                                               columnTypesList=column_types,
                                               firstItemIsColName=True,
                                               fontSize=12000)

    def save_fstab_mounts(self):
        changed = False
        fix_virtualbox = False
        fstab_path = '/etc/fstab'
        crypttab_path = '/etc/crypttab'
        crypttab_keyfile_path = '/.lukskey'

        self.set_buttons_state(False)

        fstab_cont = []
        with open(file=fstab_path, mode='r', encoding='utf-8') as crypttab_fle:
            fstab_cont = crypttab_fle.readlines()

        # Loop through the partitions
        model = self.tvFstabMounts.get_model()
        itr = model.get_iter_first()
        while itr is not None:
            selected = model.get_value(itr, 0)
            device = model.get_value(itr, 1)
            label = model.get_value(itr, 2).strip()
            uuid = ''
            fs_type = ''
            fstab_mount = ''
            # Decide new mount point
            mount = join('/media', basename(device))
            if label:
                mount = join('/media', label.replace(' ', '_'))

            # Get additional information
            for partition in self.partitions:
                if partition['device'] == device:
                    uuid = partition['uuid']
                    fs_type = partition['fs_type']
                    fstab_mount = partition['fstab_mount']
                    encrypted = partition['encrypted']
                    passphrase = partition['passphrase']
                    break

            if selected and not fstab_mount:
                # Add information to fstab
                if (uuid or device) and fs_type:
                    # Create mount directory and mount
                    if not exists(mount):
                        os.makedirs(mount)

                    if exists(mount):
                        # Mount the device
                        shell_exec(f'mount {device} {mount}')
                        usr = get_logged_user()
                        if usr:
                            # Make current user owner of the mount
                            shell_exec(f'chown {usr}:{usr} {mount}')

                    # Create new line for fstab
                    uuid = f'UUID={uuid}' if uuid and not encrypted else device
                    fsck = 0 if fs_type in ('ntfs', 'swap', 'vfat') else 1 if mount == '/' else 2
                    opts = 'defaults,noatime' if 'ext' in fs_type else 'sw' if fs_type == 'swap' else 'defaults'
                    new_line = f'{uuid}\t{mount}\t{fs_type}\t{opts}\t0\t{fsck}\n'
                    fstab_cont.append(new_line)
                    changed = True
                    self.log.write(f'Add new line to {fstab_path}: {new_line}', 'save_fstab_mounts')

                    if encrypted:
                        fix_virtualbox = True

                        # Only add key file if you can safe to another encrypted partition.
                        add_key = False
                        for partition in self.partitions:
                            if partition['mount_point'] == '/' and partition['encrypted']:
                                add_key = True
                                break

                        enc_device = device.replace('/mapper', '')
                        if passphrase and add_key:
                            # Write keyfile
                            self.log.write(f'Add device to key file {crypttab_keyfile_path}: {enc_device}',
                                           'save_fstab_mounts', 'info')
                            create_keyfile(crypttab_keyfile_path, enc_device, passphrase)
                        else:
                            crypttab_keyfile_path = 'none'

                        # Write crypttab
                        self.log.write(f'Add device to crypttab {crypttab_path}: {enc_device}',
                                       'save_fstab_mounts', 'info')
                        write_crypttab(enc_device, fs_type, crypttab_path,
                                       crypttab_keyfile_path, not encrypted)
                else:
                    # We should not get here
                    msg = _(f"Could not add {device} to {fstab_path}: missing fs type.")
                    self.log.write(msg, 'save_fstab_mounts')
                    WarningDialog(self.btnSaveFstabMounts.get_label(), msg)
                    continue
            elif not selected and fstab_mount:
                # Remove partition line from fstab
                for i, line in enumerate(fstab_cont):
                    if (uuid in line or device in line) and \
                        mount in line:
                        self.log.write(f'Remove device from {fstab_path}: {device}',
                                       'save_fstab_mounts', 'info')
                        del fstab_cont[i]
                        changed = True
                        break
                # Remove partition from crypttab
                if encrypted and exists(crypttab_path):
                    enc_device = device.replace('/mapper', '')
                    enc_device_uuid = get_uuid(enc_device)
                    #print(("+++ {} exists for device {}".format(crypttab_path, enc_device)))
                    crypttab_cont = []
                    with open(file=crypttab_path, mode='r', encoding='utf-8') as crypttab_fle:
                        crypttab_cont = crypttab_fle.readlines()
                    #print(("   {}".format(''.join(crypttab_cont))))
                    for i, line in enumerate(crypttab_cont):
                        #print(("+++ '{}' or '{}' exists '{}'".format(enc_device, enc_device_uuid, line)))
                        if enc_device in line or enc_device_uuid in line:
                            self.log.write(f'Remove device from crypttab {crypttab_path}: {enc_device}',
                                           'save_fstab_mounts', 'info')
                            del crypttab_cont[i]
                            with open(file=crypttab_path, mode='w', encoding='utf-8') as crypttab_fle:
                                crypttab_fle.write(''.join(crypttab_cont))
                            break

            # Get the next in line
            itr = model.iter_next(itr)

        if fix_virtualbox:
            # Fix VirtualBox by disabling Plymouth
            if in_virtual_box():
                if exists(self.grub.grub_default) and exists(self.grub.grub_cfg):
                    self.log.write(f"Fix Grub in VirtualBox: {self.grub.grub_default} and {self.grub.grub_cfg}",
                                   'save_fstab_mounts', 'info')
                    shell_exec(f"sed -i 's/ *splash *//g' {self.grub.grub_default}")
                    shell_exec(f"sed -i 's/ *splash *//g' {self.grub.grub_cfg}")

        if changed:
            # Save fstab
            with open(file=fstab_path, mode='w', encoding='utf-8') as crypttab_fle:
                crypttab_fle.write(''.join(fstab_cont))

            # Log fstab and crypttab
            self.log.write(''.join(fstab_cont), 'save_fstab_mounts', 'info')
            if exists(crypttab_path):
                with open(file=crypttab_path, mode='r', encoding='utf-8') as crypttab_fle:
                    self.log.write(crypttab_fle.read(), 'save_fstab_mounts', 'info')

            # Show a message
            msg = _("Changes were made to fstab.\n"
                    "Please reboot your computer for these changes to take effect.")
            MessageDialog(self.btnSaveFstabMounts.get_label(), msg)
        else:
            msg = _("No changes were made to fstab.")
            MessageDialog(self.btnSaveFstabMounts.get_label(), msg)

        self.set_buttons_state(True)

    # ===============================================
    # Device Driver functions
    # ===============================================

    def install_device_drivers(self):
        # Save selected hardware
        arguments = []

        model = self.tvDeviceDriver.get_model()
        itr = model.get_iter_first()
        while itr is not None:
            action = 'no change'
            selected = model.get_value(itr, 0)
            device = model.get_value(itr, 2)
            manufacturer_id = ''

            # Check currently selected state with initial state
            # This decides whether we should install or purge the drivers
            for hardware in self.hardware[1:]:
                self.log.write(f'Device = {device} in {hardware[2]}', 'install_device_drivers')
                if device in hardware[2]:
                    hw_driver = hardware[3]
                    manufacturer_id = hardware[4]
                    if hardware[0] and not selected:
                        action = 'purge'
                    elif not hardware[0] and selected:
                        action = 'install'
                    break

            self.log.write(f'{action}: {device} ({manufacturer_id})', 'install_device_drivers')

            # Install/purge selected driver
            option = ''
            if action == 'install':
                option = '-i'
            elif action == 'purge':
                option = '-p'

            if option:
                driver = ''
                # Run the manufacturer specific bash script
                if manufacturer_id == '1002':
                    driver = 'amd'
                elif manufacturer_id == '10de':
                    driver = 'nvidia '
                    # If nvidia-detect needs a drivers from the backports repository
                    # and the user didn't select the backports check box,
                    # force the use of backports to install the appropriate drivers
                    if 'backports' in hw_driver and not self.chkBackports.get_active():
                        option = f"-b {option}"
                elif manufacturer_id == '14e4':
                    driver = 'broadcom '
                elif 'pae' in manufacturer_id:
                    driver = 'pae '
                if driver:
                    arguments.append(f"{option} {driver}")

            # Get the next in line
            itr = model.iter_next(itr)

        # Execute the command
        if arguments:
            if '-i' in arguments and not has_internet_connection:
                title = _("No internet connection")
                msg = _("You need an internet connection to install the additional software.\n"
                        "Please, connect to the internet and try again.")
                WarningDialog(title, msg)
            else:
                # Warn for use of Backports
                if self.chkBackportsDeviceDriver.get_active():
                    answer = QuestionDialog(self.chkBackportsDeviceDriver.get_label(),
                            _("You have selected to install drivers from the backports repository whenever they are available.\n\n"
                              "Although you can run more up to date software using the backports repository,\n"
                              "you introduce a greater risk of breakage doing so.\n\n"
                              "Are you sure you want to continue?"))
                    if not answer:
                        self.chkBackportsDeviceDriver.set_active(False)
                        return True
                    arguments.append('-b')

                # Testing
                if self.test_devices:
                    arguments.append('-t')

                command = f"ddm {' '.join(arguments)}"
                self.log.write(f'Command to execute: {command}', 'install_device_drivers')

                # Run driver installation in a thread and show progress
                name = 'driver'
                self.set_buttons_state(False)
                # Pass -g to let the ddm script know it is run from a GUI
                thread = ExecuteThreadedCommands(f'{command} -g', self.queue)
                self.threads[name] = thread
                thread.daemon = True
                thread.start()
                self.queue.join()
                GLib.timeout_add(250, self.check_thread, name)

    # This method is fired by the TreeView.checkbox-toggled event
    def on_tvDeviceDriver_toggled(self, obj, path, colNr, toggleValue):
        path = int(path)
        model = self.tvDeviceDriver.get_model()
        itr = model.get_iter(path)
        pae_selected = 'pae' in model[itr][2].lower()
        pae_booted = 'pae' in getoutput('uname -r')[0]

        if pae_selected and pae_booted and not toggleValue:
            title = _("Remove kernel")
            msg = _("You cannot remove a booted kernel.\nPlease, boot another kernel and try again.")
            self.log.write(msg, 'on_tvDeviceDriver_toggled')
            WarningDialog(title, msg)
            model[itr][0] = True

    def fill_hw(self, driver_name, hw_lst):
        # Expected lspci output plus drivers:
        # driver name [manufacturer id:device id] [driver-1 driver-2 etc]
        regexp = r'(.*)\[([0-9a-z]{4}):([0-9a-z]{4})\]\s+\[([0-9a-z\-]*)'
        for hardware in hw_lst:
            match = re.search(regexp, hardware)
            if match:
                #Check if driver is installed (check for multiple drivers)
                installed = False
                drivers = match.group(4).split(' ')
                for drv in drivers:
                    if is_package_installed(drv):
                        installed = True
                    else:
                        break
                # Save the information
                self.hardware.append([installed, join(self.share_dir,
                                    f'images/{driver_name}.png'), match.group(1),
                                    match.group(4), match.group(2), match.group(3)])

    def fill_treeview_device_driver(self):
        # Fill a list with supported hardware
        self.hardware = []
        self.hardware.append([_("Install"), '', _("Device"), 'driver', 'manid', 'deviceid'])

        # Use test data (check /usr/lib/solydxk/scripts/ddm-*.sh)
        tst = ''
        if self.test_devices:
            tst = '-t -f'

        # Fill with supported hardware
        self.fill_hw('amd', getoutput(f'ddm -i amd -s {tst}'))
        self.fill_hw('nvidia', getoutput(f'ddm -i nvidia -s {tst}'))
        self.fill_hw('broadcom', getoutput(f'ddm -i broadcom -s {tst}'))
        self.fill_hw('pae', getoutput(f'ddm -i pae -s {tst}'))

        print((self.hardware))

        # columns: checkbox, image (logo), device, driver
        column_types = ['bool', 'GdkPixbuf.Pixbuf', 'str']

        # Keep some info from the user
        show_hardware = []
        for hardware in self.hardware:
            show_hardware.append([hardware[0], hardware[1], hardware[2]])

        # Fill treeview
        self.tvDeviceDriverHandler.fillTreeview(contentList=show_hardware,
                                                columnTypesList=column_types,
                                                firstItemIsColName=True,
                                                fontSize=12000)

    # ===============================================
    # Encryption functions
    # ===============================================

    def save_my_partitions(self):
        # Get selected partition paths from tvPartitions
        self.my_partitions = []
        my_swap = []
        selected_rows = self.tvPartitionsHandler.getSelectedRows()
        for selected_row in selected_rows:
            device = selected_row[1][1]
            for partition in self.partitions:
                if partition['device'] == device:
                    if partition['fs_type'] == 'swap':
                        my_swap.append(partition)
                    else:
                        self.my_partitions.append(partition)
                        break

        # Make sure a swap partitions are done last
        # Need that in write_partition_configuration
        if my_swap:
            self.my_partitions.extend(my_swap)

    def endecrypt(self):
        name = 'endecrypt'
        action = self.btnDecrypt.get_label()

        # Check passphrase first
        if self.encrypt:
            action = self.btnEncrypt.get_label()
            if self.my_passphrase == '':
                # Message user for passphrase
                MessageDialog(action, self.no_passphrase_msg)
                return
        else:
            self.my_passphrase = ''

        if self.my_partitions:
            # Search for a backup directory
            backup_partition = self.backup_partition()
            if not backup_partition:
                print(("ERROR: no backup directory"))
                return

            for partition in self.my_partitions:
                is_swap = partition['fs_type'] == 'swap'
                if self.encrypt:
                    if partition['encrypted']:
                        if partition['mount_point']:
                            device = partition['device']
                            answer = QuestionDialog(_("Encrypted partition"),
                                                    _(f"The partition {device} is already encrypted.\n"
                                                      "Continuing will change the encryption key of this partition.\n\n"
                                                      "Do you want to continue?"))
                            if not answer:
                                return
                        elif not is_swap:
                            current_passphrase = self.passphrase_dialog(partition['device'])
                            if current_passphrase:
                                device, mount, filesystem = self.temp_mount(partition, current_passphrase)
                                if mount:
                                    partition['passphrase'] = current_passphrase
                                    partition['device'] = device
                                    partition['mount_point'] = mount
                                    partition['fs_type'] = filesystem
                                else:
                                    self.log.write(self.mount_error.format(partition['device']),
                                                   name, 'error')
                                    return
                else:
                    if not partition['encrypted']:
                        # Message the user that the partition is not encrypted
                        msg = _("The partition is not encrypted.\n"
                                "Please choose another partition to decrypt.")
                        self.log.write(msg, name, 'error')
                        return

                    # For safety reasons the encrypted partition needs to be mounted
                    if not partition['mount_point'] and not is_swap:
                        current_passphrase = self.passphrase_dialog(partition['device'])
                        if current_passphrase:
                            device, mount, filesystem = self.temp_mount(partition, current_passphrase)
                            if mount:
                                partition['passphrase'] = current_passphrase
                                partition['device'] = device
                                partition['mount_point'] = mount
                                partition['fs_type'] = filesystem
                            else:
                                self.log.write(self.mount_error.format(partition['device']),
                                               name, 'error')
                                return

                # Mount partition if not already mounted
                if not partition['mount_point'] and not is_swap:
                    device, mount, filesystem = self.temp_mount(partition, self.my_passphrase)
                    self.log.write(f"Mount (for creating backup) {device} to {mount}", name, 'info')
                    if mount:
                        partition['device'] = device
                        partition['mount_point'] = mount
                        partition['fs_type'] = filesystem
                    else:
                        self.log.write(self.mount_error.format(partition['device']), name, 'error')
                        return

            # Install cryptsetup if needed
            pck_list = ''
            if not is_package_installed('cryptsetup') or not is_package_installed('cryptsetup-run'):
                pck_list = 'cryptsetup'
            if not is_package_installed('cryptsetup-initramfs'):
                pck_list += ' cryptsetup-initramfs'
            if pck_list:
                cmd = f"apt-get {get_apt_force()} install {pck_list}"
                os.system(cmd)

            if (is_package_installed('cryptsetup') or is_package_installed('cryptsetup-run')) \
               and is_package_installed('cryptsetup-initramfs'):
                # Run encrypt/decrypt in separate thread
                self.set_buttons_state(False)
                thread = EnDecryptPartitions(self.my_partitions, backup_partition,
                                             self.encrypt, self.my_passphrase, self.queue, self.log)
                self.threads[name] = thread
                thread.daemon = True
                thread.start()
                self.queue.join()
                GLib.timeout_add(5, self.check_thread, name)
            else:
                # Show a warning message
                msg = _("Could not install cryptsetup/cryptsetup-initramfs.")
                self.log.write(msg, 'endecrypt')
                WarningDialog('endecrypt', msg)

    def change_passphrase(self):
        if len(self.my_partitions) == 0:
            return

        # Check passphrase first
        if not self.my_passphrase:
            # Message user for passphrase
            MessageDialog(self.btnChangePassphrase.get_label(), self.no_passphrase_msg)
            return

        for partition in self.my_partitions:
            if not partition['encrypted']:
                # Message the user that the partition is not encrypted
                device = partition['device']
                msg = _(f"{device} is not encrypted.\n"
                        "Please choose an encrypted partition.")
                MessageDialog(self.btnChangePassphrase.get_label(), msg)
                return

        # Run encrypt/decrypt in separate thread
        self.changed_devices = []
        name = 'changepassphrase'
        self.set_buttons_state(False)
        thread = ChangePassphrase(self.my_partitions, self.my_passphrase, self.queue, self.log)
        self.threads[name] = thread
        thread.daemon = True
        thread.start()
        self.queue.join()
        GLib.timeout_add(250, self.check_thread, name)

    def is_active_swap_partition(self, device):
        out = getoutput(f'grep "{device}" /proc/swaps')[0]
        if out:
            return True
        return False

    def fill_partitions(self, check_encryptable=True, include_flash=False):
        # Exclude these device paths
        exclude_devices = ['/dev/sr0', '/dev/sr1', '/dev/cdrom', '/dev/dvd',
                           '/dev/fd0', '/dev/mmcblk0boot0', '/dev/mmcblk0boot1', '/dev/mmcblk0rpmb']

        # List partition info
        self.my_partitions = []
        self.partitions = []
        tmp_partitions = []
        self.udisks2.fill_devices(include_flash=include_flash)
        for device_path in self.udisks2.devices:
            if device_path not in exclude_devices:
                device = self.udisks2.devices[device_path]
                # Exclude the root partition, home partition, boot partitions and swap
                if not '/boot' in device['mount_point'] and \
                   device['mount_point'] != '/' and \
                   device['mount_point'] != '/home' and \
                   not self.is_active_swap_partition(device_path):
                    tmp_partitions.append({'device': device_path,
                                                'old_device': device_path,
                                                'fs_type': device['fs_type'],
                                                'label': device['label'],
                                                'total_size': device['total_size'],
                                                'free_size': device['free_size'],
                                                'used_size': device['used_size'],
                                                'encrypted': is_encrypted(device_path),
                                                'passphrase': '',
                                                'mount_point': device['mount_point'],
                                                'old_mount_point': device['mount_point'],
                                                'uuid': device['uuid'],
                                                'old_uuid': device['uuid'],
                                                'removable': device['removable'],
                                                'has_grub': device['has_grub']
                                               })
        # Reset failed mount devices
        self.failed_mount_devices = []

        for partition in tmp_partitions:
            # Get fstab information
            fstab_path, fstab_device, fstab_mount, fstab_cont, crypttab_path, keyfile_path = self.partition_configuration_info(partition, tmp_partitions, check_encryptable)

            # Do not add encrypted partitions that failed to connect (bad passphrase)
            if 'crypt' in partition['fs_type']:
                continue

            partition['fstab_path'] = fstab_path
            partition['fstab_device'] = fstab_device
            partition['fstab_mount'] = fstab_mount
            partition['fstab_cont'] = fstab_cont
            partition['crypttab_path'] = crypttab_path
            partition['keyfile_path'] = keyfile_path

            # Only add swap and root if /boot is configured in fstab
            can_encrypt = False
            if fstab_mount == '/' or fstab_mount == 'swap':
                # Check for /boot partition in fstab_cont
                pattern = re.compile(r'.*\s/boot\s')
                lines = pattern.findall(fstab_cont)
                for line in lines:
                    if line[:1] != '#':
                        can_encrypt = True
                        break
            elif fstab_mount == '/boot':
                self.boot_partition = partition
            elif not '/boot' in fstab_mount:
                can_encrypt = True

            if can_encrypt:
                #print(">>> partition = %s" % str(partition))
                self.partitions.append(partition)

        # Sort the list with dictionaries
        self.partitions = sorted(self.partitions, key=lambda k: k['device'])

    def fill_treeview_partition(self):
        # Get available partitions
        self.fill_partitions(include_flash=True)

        # Create human readable list of partitions
        # Copy the header first by using list()
        hr_list = list(self.encrypt_list_header)
        for partition in self.partitions:
            if partition['encrypted']:
                if partition['removable']:
                    enc_img = join(self.share_dir, 'icons/encrypted-usb.png')
                else:
                    enc_img = join(self.share_dir, 'icons/encrypted.png')
            else:
                if partition['removable']:
                    enc_img = join(self.share_dir, 'icons/unencrypted-usb.png')
                else:
                    enc_img = join(self.share_dir, 'icons/unencrypted.png')
            total_size = human_size(partition['total_size'])
            free_size = ''
            if partition['free_size'] > 0:
                free_size = human_size(partition['free_size'])
            hr_list.append([enc_img, partition['device'], partition['label'], partition['fs_type'],
                            total_size, free_size, partition['mount_point']])

        # Fill treeview
        self.tvPartitionsHandler.fillTreeview(contentList=hr_list,
                                              columnTypesList=self.encrypt_col_types,
                                              firstItemIsColName=True,
                                              multipleSelection=True)

    def check_passphrase(self):
        self.my_passphrase = ''

        pf1 = cleanup_passphrase(self.txtPassphrase1.get_text())
        pf2 = cleanup_passphrase(self.txtPassphrase2.get_text())

        # Reset text fields with clean passphrase
        self.txtPassphrase1.set_text(pf1)
        self.txtPassphrase2.set_text(pf2)

        if pf1 == '' and pf2 == '':
            self.imgPassphraseCheck.hide()
        else:
            self.imgPassphraseCheck.show()
        if pf1 != pf2 or len(pf1) < 6:
            self.imgPassphraseCheck.set_from_icon_name('dialog-no', Gtk.IconSize.BUTTON)
        else:
            self.imgPassphraseCheck.set_from_icon_name('dialog-ok', Gtk.IconSize.BUTTON)
            self.my_passphrase = pf1

    def backup_partition(self):
        # Set a safe margin to have extra available on the backup partition
        safe_margin_kb = 10240

        # Search for mounted partition with enough space to backup the selected partition
        bak_str = _("Backup")
        system_partitions = ['/home', '/']
        bak_partition = ''
        used_size = 0

        # Get the combined used size of the selected partitions, except the swap partition
        for my_p in self.my_partitions:
            if my_p['fs_type'] != 'swap':
                used_size += my_p['used_size']

        # Add the safe margin
        used_size += safe_margin_kb

        # First check booted system partitions
        for my_p in self.my_partitions:
            if not bak_partition:
                for sys_partition in system_partitions:
                    if sys_partition != my_p['mount_point']:
                        sys_partition_stat = os.statvfs(sys_partition)
                        free_size = (sys_partition_stat.f_bavail *
                                     sys_partition_stat.f_frsize) / 1024
                        if free_size > used_size:
                            bak_partition = sys_partition
                            break

            # Check other mounted devices
            if not bak_partition:
                for partition in self.partitions:
                    if partition['device'] != my_p['device'] and \
                       partition['mount_point'] != '' and \
                       partition['free_size'] > used_size:
                        bak_partition = partition['mount_point']
                        break

        # If not enough space: exit with message
        if not bak_partition:
            size = human_size(used_size)
            msg = _(f"You need a backup partition with at least {size} free.\n"
                    "Mount a backup drive and hit the refresh button.")
            MessageDialog(bak_str, msg)

        return bak_partition

    def sort_fstab(self, fstab_path):
        # Sort the contents of fstab
        cont = ''
        sort_lst = []
        sorted_lst = []
        fstab_lines = []

        with open(file=fstab_path, mode='r', encoding='utf-8') as fstab_fle:
            fstab_lines = fstab_fle.readlines()

        for line in fstab_lines:
            line = line.strip()
            if line[0:1] == '#':
                line_added = False
                if not sorted_lst:
                    # First line in fstab is commented
                    sorted_lst.append(line)
                    line_added = True
                if sort_lst:
                    # Sort list on mount point
                    sort_lst = sorted(sort_lst, key=lambda x: x[1])
                for sort_line in sort_lst:
                    # Add sorted line to list
                    sorted_lst.append('\t'.join(sort_line))
                # Cleanup before next iteration
                sort_lst = []
                if not line_added:
                    # Add empty line for readability
                    sorted_lst.append('')
                    # Add comment
                    sorted_lst.append(line)
            else:
                # Add mount device line
                lst = line.split()
                if len(lst) == 6:
                    sort_lst.append(lst)

        # Add left overs
        if sort_lst:
            sort_lst = sorted(sort_lst, key=lambda x: x[1])
        for sort_line in sort_lst:
            sorted_lst.append('\t'.join(sort_line))

        # Create the sorted fstab contents
        if sorted_lst:
            cont = '\n'.join(sorted_lst) + '\n'

        return cont

    def partition_configuration_info(self, partition, partitions, check_encryptable):
        fstab_paths = ['/etc/fstab']

        # Search for fstab file if you're in a live session
        for partition in partitions:
            if not partition['mount_point'] \
               and partition['fs_type'] != 'swap' \
               and partition['device'] not in self.failed_mount_devices:

                current_passphrase = None
                mount = ''
                device = ''
                filesystem = ''

                if partition['encrypted'] and not partition['passphrase'] and not 'mapper' in partition['device']:
                    # This is an encrypted, not mounted partition.
                    # Ask the user for the passphrase
                    current_passphrase = self.passphrase_dialog(partition['device'])

                if check_encryptable:
                    # Mount the partition when working in encryption
                    device, mount, filesystem = self.temp_mount(partition, current_passphrase)
                    #print((">>>> p1 = %s" % str(p)))
                    #print(("     mount = %s" % mount))
                    if mount:
                        #print((">>>> Save %s: mount=%s, fs_type=%s" % (device, mount, filesystem)))
                        partition['mount_point'] = mount
                        # Get free_size from mapped path
                        total, free, used = self.udisks2.get_mount_size(mount)
                        partition['free_size'] = free
                        partition['used_size'] = used
                        # Get label
                        partition['label'] = get_label(device)

                        # Add fstab path
                        fstab_path = join(partition['mount_point'], 'etc/fstab')
                        if exists(fstab_path) and not fstab_path in fstab_paths:
                            fstab_paths.append(fstab_path)
                    else:
                        show_error = True
                        #print((">>>> Could not mount %s (%s)" % (p['device'], p['fs_type'])))
                        if partition['fs_type'] == 'swap' or partition['fs_type'] == '':
                            # Don't show error
                            show_error = False
                        self.log.write(self.mount_error.format(partition['device']),
                                       'get_partition_configuration_info', 'error', show_error)
                        if partition['device'] not in self.failed_mount_devices:
                            self.failed_mount_devices.append(partition['device'])

                elif current_passphrase is not None:
                    # Not in encryption: connect the block device but do not mount
                    device, filesystem = connect_block_device(partition['device'], current_passphrase)

                    #print((">>>> p2 = %s" % str(p)))
                    #print(("     device = %s" % device))
                    if device:
                        # Save information
                        partition['fs_type'] = filesystem
                        partition['passphrase'] = current_passphrase
                        partition['device'] = device
                    else:
                        show_error = True
                        #print((">>>> Could not connect block device %s (%s)" % (p['device'], p['fs_type'])))
                        if partition['fs_type'] == 'swap' or partition['fs_type'] == '':
                            # Don't show error
                            show_error = False
                        self.log.write(self.mount_error.format(partition['device']),
                                       'get_partition_configuration_info', 'error', show_error)
                        if partition['device'] not in self.failed_mount_devices:
                            self.failed_mount_devices.append(partition['device'])

        if partition['device'] not in self.failed_mount_devices:
            # Check if given partition is listed in /etc/fstab
            for fstab_path in fstab_paths:
                fstab_cont = self.sort_fstab(fstab_path)
                fstab_mount = ''

                fstab_device = partition['old_device'].replace('/dev/mapper', '/dev')
                if not 'mapper' in fstab_device:
                    fstab_device = fstab_device.replace('/dev', '/dev/mapper')

                regexp = rf"^\s*(UUID={partition['old_uuid']}|{partition['old_device']}|{fstab_device})\s+(\S+)"
                #print(("++++ regexp = %s" % regexp))
                match = re.search(regexp, fstab_cont, re.M)
                if match:
                    fstab_device = match.group(1)
                    fstab_mount = match.group(2)
                if fstab_mount:
                    # Set fs_type for swap partitions
                    if fstab_mount == 'swap':
                        partition['fs_type'] = 'swap'

                    # Get encryption information
                    crypttab_path = ''
                    keyfile_path = ''
                    #print(("**** crypttab partition: %s" % str(partition)))
                    if partition['encrypted']:
                        crypttab_path = fstab_path.replace('fstab', 'crypttab')
                        #print(("++++ crypttab_path=%s" % crypttab_path))
                        if exists(crypttab_path):
                            lines = []
                            with open(file=crypttab_path, mode='r', 
                                      encoding='utf-8') as crypttab_fle:
                                lines = crypttab_fle.readlines()
                            for line in lines:
                                line = line.strip()
                                line_data = line.split()
                                #print(("++++ lineData=%s" % str(lineData)))

                                if len(line_data) <= 1:
                                    continue

                                match = re.search(r'[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12}',
                                                  line_data[1])
                                if match:
                                    crypttab_uuid = match.group(0)
                                    #print(("++++ crypttab_uuid=%s" % crypttab_uuid))
                                    device = get_device_from_uuid(crypttab_uuid)
                                    #print(("++++ device=%s, partition['device']=%s" % (device, partition['device'])))
                                    if basename(device) == basename(partition['device']):
                                        # Get crypttab data
                                        crypttab_keyfile_path = line_data[2]
                                        if crypttab_keyfile_path == 'none':
                                            crypttab_keyfile_path = ''
                                        if crypttab_keyfile_path:
                                            # Search the keyfile path
                                            crypttab_keyfile_dir = dirname(crypttab_keyfile_path)
                                            esc_dir = crypttab_keyfile_dir.replace('/', r'\/')
                                            regexp = rf"([0-9a-z-/]+)\s+{esc_dir}\s+"
                                            #print(("++++ regexp = %s" % regexp))
                                            match = re.search(regexp, fstab_cont)
                                            if match:
                                                keyfile_device = match.group(1)
                                                if keyfile_device[:1] != '/':
                                                    keyfile_device = get_device_from_uuid(keyfile_device)
                                                #print(("++++ keyfile_device = %s" % keyfile_device))
                                                #print(self.partitions)
                                                for partition in self.partitions:
                                                    #print(("    ++++ bn_device = %s, bn_keyfile_device = %s" % (basename(p['device']), basename(keyfile_device))))
                                                    if basename(partition['device']) == basename(keyfile_device):
                                                        keyfile_path = join(partition['mount_point'], crypttab_keyfile_path.lstrip('/'))
                                                        #print(("        ++++ keyfile_path = %s" % keyfile_path))
                                                        break
                                        break
                    return (fstab_path, fstab_device, fstab_mount, fstab_cont, crypttab_path, keyfile_path)

        # Nothing found
        return ('', '', '', '', '', '')

    def write_partition_configuration(self, keyfile_only=False):
        keyfile_path = ''
        crypttab_keyfile_path = None
        encrypt_info = []
        saved_fstabs = {}
        grub_partitions = []
        root_devices = []

        # Make sure to only write those partitions that are already in fstab
        for partition in self.my_partitions:
            # Get fstab path for this partition
            if not partition['fstab_path']:
                continue

            # Check if Grub has been installed on this partition
            if partition['has_grub']:
                grub_partitions.append(partition['device'].replace('/mapper', ''))

            # Save the boot devices for Grub update
            if partition['fstab_mount'] == '/':
                root_devices.append(partition['device'].replace('/mapper', ''))

            # Set uuid string if not mapped device
            device = partition['device']
            if not '/dev/mapper' in partition['device']:
                device = f"UUID={partition['uuid']}"

            # Check if fstab contents has changed before
            try:
                fstab_cont = saved_fstabs[partition['fstab_path']]
            except:
                fstab_cont = partition['fstab_cont']

            # Rewrite this device in fstab
            fstab_cont = re.sub(partition['fstab_device'], device, fstab_cont)
            saved_fstabs[partition['fstab_path']] = fstab_cont

            # Save configuration information
            skip_keyfile_config = False
            if partition['encrypted'] and partition['fstab_mount']:
                # Get the keyfile path and the path it will have in the crypttab file
                if not keyfile_path and partition['fs_type'] != 'swap':
                    skip_keyfile_config = True
                    keyfile_path = join(partition['mount_point'], '.lukskey')
                    crypttab_keyfile_path = join(partition['fstab_mount'], '.lukskey')

            # Create a dictionary with the info
            info_dict = {}
            info_dict['device'] = partition['device']
            info_dict['fs_type'] = partition['fs_type']
            info_dict['fstab_path'] = partition['fstab_path']
            info_dict['keyfile_path'] = ''
            info_dict['crypttab_keyfile_path'] = ''
            info_dict['passphrase'] = partition['passphrase']
            if not skip_keyfile_config:
                self.log.write(f"Path to luks key file: {keyfile_path}",
                               'write_partition_configuration', 'info')
                self.log.write(f"Crypttab luks key file path: {crypttab_keyfile_path}",
                               'write_partition_configuration', 'info')
                info_dict['keyfile_path'] = keyfile_path
                info_dict['crypttab_keyfile_path'] = crypttab_keyfile_path

            # Append the dictionary to the list
            encrypt_info.append(info_dict)

            # Crypttab
            if not partition['encrypted'] and not keyfile_only:
                # Remove device from crypttab
                base_name = basename(partition['device'])
                self.log.write(f"Remove {base_name} from {partition['crypttab_path']}",
                               'write_partition_configuration', 'info')
                cmd = f"sed -i '/^{base_name} /d' {partition['crypttab_path']}"
                shell_exec(cmd)

                # Remove any references of a key file when the key file is on this decrypted and unsafe partition
                lukskey = join(partition['mount_point'], '.lukskey')
                if exists(lukskey):
                    self.log.write(f"Remove {lukskey} from unencrypted and unsafe {partition['device']}",
                                   'write_partition_configuration', 'info')
                    os.remove(lukskey)
                self.log.write(f"Remove {lukskey} references from {partition['crypttab_path']}",
                               'write_partition_configuration', 'info')
                cmd = f"sed -i 's#{lukskey}#none#g' {partition['crypttab_path']}"
                shell_exec(cmd)

            # Write the new content to the fstab files, the key files and crypttab files
            saved_fstab = ''
            sep_line = '=' * 10
            for enc_dict in encrypt_info:
                if not keyfile_only and saved_fstab != enc_dict['fstab_path']:
                    saved_fstab = enc_dict['fstab_path']
                    # Logging
                    self.log.write(f"{sep_line} blkid {sep_line}",
                                   'write_partition_configuration', 'info')
                    self.log.write('\n'.join(getoutput("blkid")),
                                   'write_partition_configuration', 'info')
                    self.log.write(f"{sep_line} {enc_dict['fstab_path']} {sep_line}",
                                   'write_partition_configuration', 'info')
                    self.log.write(saved_fstabs[enc_dict['fstab_path']],
                                   'write_partition_configuration', 'info')
                    self.log.write('=' * 25, 'write_partition_configuration', 'info')

                    # Fstab
                    with open(file=enc_dict['fstab_path'], mode='w', encoding='utf-8') as fstab_fle:
                        fstab_fle.write(saved_fstabs[enc_dict['fstab_path']])

                # Key file
                if enc_dict['keyfile_path']:
                    passphrase = self.my_passphrase
                    if keyfile_only and enc_dict['passphrase']:
                        passphrase = enc_dict['passphrase']
                    if passphrase:
                        create_keyfile(enc_dict['keyfile_path'],
                                       enc_dict['device'].replace('/mapper', ''),
                                       passphrase)

                #print(("++++ keyfile_only=%s" % str(keyfile_only)))
                if not keyfile_only:
                    # Crypttab
                    #print(("++++ Start write_crypttab"))
                    write_crypttab(enc_dict['device'].replace('/mapper', ''),
                                   enc_dict['fs_type'],
                                   partition['crypttab_path'],
                                   enc_dict['crypttab_keyfile_path'],
                                   not self.encrypt)

                    # Log crypttab
                    if exists(partition['crypttab_path']):
                        self.log.write(f"{sep_line} {partition['crypttab_path']} {sep_line}",
                                       'write_partition_configuration', 'info')
                        with open(file=partition['crypttab_path'],
                                  mode='r',
                                  encoding='utf-8') as fstab_fle:
                            self.log.write(fstab_fle.read(),
                                           'write_partition_configuration', 'info')
                        self.log.write('=' * 25, 'write_partition_configuration', 'info')

        # Get the grub path to fix VirtualBox by disabling Plymouth
        if in_virtual_box() and self.encrypt:
            grub_path = ''
            grubcfg_path = ''
            for partition in self.partitions:
                #print(("---- %s" % str(p)))
                if partition['fstab_mount'] == '/':
                    grub_path = join(partition['mount_point'], 'etc/default/grub')
                    grubcfg_path = join(partition['mount_point'], 'boot/grub/grub.cfg')
                    break
            if not self.boot_partition is None:
                mount = self.boot_partition['mount_point']
                if not mount:
                    self.log.write(f"Mount /boot partition {self.boot_partition['device']}",
                                   'write_partition_configuration', 'info')
                    device, mount, filesystem = self.temp_mount(partition, self.my_passphrase)
                if mount:
                    grubcfg_path = join(self.boot_partition['mount_point'], 'grub/grub.cfg')

            #print((">>> grub_path=%s, grubcfg_path=%s" % (grub_path, grubcfg_path)))
            if grub_path and grubcfg_path:
                self.log.write(f"Fix Grub in VirtualBox: {grub_path} and {grubcfg_path}",
                               'write_partition_configuration', 'info')
                shell_exec(f"sed -i 's/ *splash *//g' {grub_path}")
                shell_exec(f"sed -i 's/ *splash *//g' {grubcfg_path}")

        if not keyfile_only:
            passphrase = ''
            if self.encrypt:
                passphrase = self.my_passphrase
            # Restore Grub when encrypting a root device
            for grub_partition in grub_partitions:
                cmd = f"grub-install --force {grub_partition};exit"
                shell_exec(f"chroot-partition {grub_partition} \"{passphrase}\" \"{cmd}\"")
            for root_device in root_devices:
                if not grub_partitions:
                    cmd = f"grub-install --force {root_device.rstrip('0123456789')};"
                cmd += "update-initramfs -u;update-grub;exit"
                shell_exec(f"chroot-partition {root_device} \"{passphrase}\" \"{cmd}\"")

    # ===============================================
    # Localization functions
    # ===============================================

    def save_locale(self):
        # Collect information
        if has_internet_connection():
            # Check if FF and TB are running
            msg = _("Firefox and/or Thunderbird are running.\n"
                    "Please close these applications before you continue.")
            while is_process_running('firefox') \
                or is_process_running('firefox-esr') \
                or is_process_running('thunderbird'):
                WarningDialog(self.btnSaveLocale.get_label(), msg)

            locales = self.tvLocaleHandler.model_to_list()
            timezone = join(self.cmbTimezoneContinentHandler.getValue(),
                            self.cmbTimezoneHandler.getValue())

            # Run localization in a thread and show progress
            name = 'localize'
            self.set_buttons_state(False)
            thread = Localize(locales, timezone, self.queue)
            self.threads[name] = thread
            thread.daemon = True
            thread.start()
            # TODO: why is queue.join sometimes blocking the thread but not always?
            #self.queue.join()
            GLib.timeout_add(250, self.check_thread, name)
        else:
            title = self.title
            msg = _(f"{title} cannot download and install the software localization packages\n"
                    "Please repeat this process when you established an internet connection.")
            WarningDialog(self.btnSaveLocale.get_label(), msg)

    def fill_treeview_locale(self):
        self.locales = [[self.installed_title, self.locale_title,
                         self.language_title, self.default_title]]
        select_row = 0
        i = 0
        for loc in self.locale_info.locales:
            lan = self.locale_info.get_readable_language(loc)
            select = False
            default = False
            if loc in self.locale_info.available_locales:
                select = True
            if loc == self.locale_info.default_locale:
                default = True
                select_row = i
            self.locales.append([select, loc, lan, default])
            i += 1

        # Fill treeview
        col_type_lst = ['bool', 'str', 'str', 'bool']
        self.tvLocaleHandler.fillTreeview(self.locales, col_type_lst, select_row, 400, True)

    def fill_cmb_timezone_continent(self):
        self.cmbTimezoneContinentHandler.fillComboBox(self.locale_info.timezone_continents,
                                                      self.locale_info.current_timezone_continent)
        self.fill_cmb_timezone(self.cmbTimezoneContinentHandler.getValue())

    def fill_cmb_timezone(self, timezone_continent):
        timezones = self.locale_info.list_timezones(timezone_continent)
        self.cmbTimezoneHandler.fillComboBox(timezones,
                                             self.locale_info.current_timezone)

    def on_tvLocale_toggled(self, obj, path, col_nr, toggle_value):
        path = int(path)
        model = self.tvLocale.get_model()
        selected_iter = model.get_iter(path)
        if not toggle_value:
            model[selected_iter][3] = True
            return

        # Check that only one default locale can be selected
        # and that the locale should be selected for installation
        if col_nr == 3:
            installed = model.get_value(selected_iter, 0)
            if not installed:
                model[selected_iter][3] = False
                return False
            self.new_default_locale = model.get_value(selected_iter, 1)
            # Deselect any other default locale
            row_cnt = 0
            itr = model.get_iter_first()
            while itr is not None:
                if row_cnt != path:
                    model[itr][3] = False
                itr = model.iter_next(itr)
                row_cnt += 1

    # ===============================================
    # Hold back functions
    # ===============================================

    def fill_treeview_holdback(self):
        holdback_pcks = []
        self.holdback = getoutput("env LANG=C dpkg --get-selections | grep hold$ | awk '{print $1}'")
        for pck in self.holdback:
            if pck != '':
                holdback_pcks.append([False, pck.strip()])
        # Fill treeview
        col_type_lst = ['bool', 'str']
        self.tvHoldbackHandler.fillTreeview(holdback_pcks, col_type_lst, 0, 400, False)

    def fill_treeview_available(self):
        self.available = []
        lst = getoutput("env LANG=C dpkg --get-selections | grep install$ | awk '{print $1}'")
        for pck in lst:
            self.available.append([False, pck.strip()])
        # Fill treeview
        col_type_lst = ['bool', 'str']
        self.tvAvailableHandler.fillTreeview(self.available, col_type_lst, 0, 400, False)

    def add_holdback(self):
        packages = self.tvAvailableHandler.getToggledValues()
        for pck in packages:
            self.log.write(f"Hold back package: {pck}", 'add_holdback')
            shell_exec(f"echo '{pck} hold' | dpkg --set-selections")
        self.fill_treeview_holdback()
        self.fill_treeview_available()

    def remove_holdback(self):
        packages = self.tvHoldbackHandler.getToggledValues()
        for pck in packages:
            self.log.write(f"Remove hold back from: {pck}", 'remove_holdback')
            shell_exec(f"echo '{pck} install' | dpkg --set-selections")
        self.fill_treeview_holdback()
        self.fill_treeview_available()

    # ===============================================
    # Mirror functions
    # ===============================================

    def save_backports(self):
        sources_changed = False
        backports_name = f"{self.debian_name}-backports"

        if self.chkEnableBackports.get_active():
            self.backports = self.apt.get_backports(exclude_disabled=False)
            # Check which regular repository is enabled
            debian_domain = ''
            match = re.search(r"([a-z0-9\.]+)debian\.org", self.current_debian_repo)
            if match:
                debian_domain = f"{match.group(1)}debian.org"
            # Create backports line for sources.list
            if self.debian_name and debian_domain:
                for backport_source in self.backports:
                    if debian_domain in backport_source['source-entry'].uri:

                        # Enable disabled backports repo
                        self.apt.set_disable(apt_source=backport_source, disabled=False)
                        self.apt.save(self.backports)

                        self.log.write('Enable existing source: ' \
                                       f"{backport_source['source-entry'].uri}",
                                       'save_backport')
                        sources_changed = True
                        break
                if not sources_changed:
                    # Add new backports repo
                    new_apt_source = self.apt.new_apt_source(types=['deb'],
                                                             uri=f"https://{debian_domain}/debian/",
                                                             suites=[backports_name],
                                                             comps=self.apt.distro_comps['debian']
                                                             )
                    self.backports.append(new_apt_source)
                    self.apt.save(self.backports)

                    sources_changed = True
        else:
            # Comment the backports repository entry in sources.list
            self.backports = self.apt.get_backports()
            for backport_source in self.backports:
                if backports_name in backport_source['suites']:

                    # Disable the backports repo
                    self.apt.set_disable(apt_source=backport_source, disabled=True)
                    self.apt.save(self.backports)

                    self.log.write('Disable existing source: ' \
                                   f"{backport_source['source-entry'].uri}",
                                   'save_backport')
                    sources_changed = True

        # Update the apt cache
        if sources_changed:
            if has_internet_connection():
                # Run update in a thread and show progress
                name = 'updatebp'
                self.set_buttons_state(False)
                thread = ExecuteThreadedCommands("apt-get update", self.queue)
                self.threads[name] = thread
                thread.daemon = True
                thread.start()
                self.queue.join()
                GLib.timeout_add(250, self.check_thread, name)
            else:
                msg = _("Could not update the apt cache.\n"
                        "Please update the apt cache manually with: apt-get update")
                WarningDialog(self.btnSaveBackports.get_label(), msg)
        else:
            msg = _("Nothing to do.")
            MessageDialog(self.btnSaveBackports.get_label(), msg)

        # Make sure the current state is saved
        # and that the backports checkbox for devices is enabled/disabled
        self.backports = self.apt.get_backports()
        if self.backports:
            self.chkBackportsDeviceDriver.set_sensitive(True)
        else:
            self.chkBackportsDeviceDriver.set_sensitive(False)

    def fill_treeview_mirrors(self):
        # Fill mirror list
        if len(self.mirrors) > 1:
            # Fill treeview
            col_type_lst = ['bool', 'str', 'str', 'str']
            self.tvMirrorsHandler.fillTreeview(self.mirrors, col_type_lst, 0, 400, True)

            # TODO - We have no mirrors: hide the tab until we do
            #self.nbPref.get_nth_page(1).set_visible(False)
        else:
            self.nbPref.get_nth_page(1).set_visible(False)

    def save_mirrors(self):
        # Safe mirror settings
        replace_repos = []
        # Get user selected mirrors
        model = self.tvMirrors.get_model()
        itr = model.get_iter_first()
        while itr is not None:
            sel = model.get_value(itr, 0)
            if sel:
                repo = model.get_value(itr, 2)
                url = model.get_value(itr, 3).rstrip('/')
                not_changed = ''
                # Get currently selected data
                for mirror in self.mirrors:
                    if mirror[0] and mirror[2] == repo:
                        mirror[3] = mirror[3].rstrip('/')
                        if mirror[3] != url:
                            # Currently selected mirror
                            replace_repos.append([mirror[3], url])
                        else:
                            not_changed = url
                        break
                if (not has_value_in_multi_array(value=url, multi_array=replace_repos, index=1)
                    and url not in not_changed):
                    # Append the repository to the sources file
                    replace_repos.append(['', url])
            itr = model.iter_next(itr)

        if not replace_repos:
            # Check for dead mirrors
            model = self.tvMirrors.get_model()
            itr = model.get_iter_first()
            while itr is not None:
                sel = model.get_value(itr, 0)
                if sel:
                    repo = model.get_value(itr, 2)
                    url = model.get_value(itr, 3).rstrip('/')
                    # Get currently selected data
                    for mirror in self.dead_mirrors:
                        mirror[1] = mirror[1].rstrip('/')
                        mirror[2] = mirror[2].rstrip('/')
                        if mirror[1] == repo and mirror[2] != url:
                            # Currently selected mirror
                            replace_repos.append([mirror[2], url])
                            break
                itr = model.iter_next(itr)

        if replace_repos:
            # Replace the current repo with the new repo
            repo_replaced = False
            apt_sources = self.apt.get_apt_sources()

            for repo in replace_repos:
                for apt_source in apt_sources:
                    # Find the repo to be replaced
                    if repo[0] == apt_source['source-entry'].uri.rstrip('/'):
                        self.apt.set_uri(apt_source=apt_source, uri=repo[1])
                        repo_replaced = True

            if repo_replaced:
                self.apt.save(new_sources_list=apt_sources)
                if has_internet_connection():
                    # Run update in a thread and show progress
                    name = 'updatebp'
                    self.set_buttons_state(False)
                    thread = ExecuteThreadedCommands("apt-get update", self.queue)
                    self.threads[name] = thread
                    thread.daemon = True
                    thread.start()
                    self.queue.join()
                    GLib.timeout_add(250, self.check_thread, name)
                else:
                    msg = _("Could not update the apt cache.\n"
                            "Please update the apt cache manually with: apt-get update")
                    WarningDialog(self.btnSaveMirrors.get_label(), msg)

        else:
            msg = _("There are no repositories to save.")
            MessageDialog(self.lblRepositories.get_label(), msg)

    def list_mirrors(self):
        mirrors = [[_("Current"), _("Country"), _("Repository"), _("URL")]]
        for mirror in self.active_mirrors:
            if mirror:
                self.log.write(f"Mirror data: {' '.join(mirror)}", 'get_mirrors')
                is_current = self.apt.is_uri_in_sources(uri=mirror[2])
                # Save current debian repo in a variable
                if is_current and 'debian.org' in mirror[2]:
                    self.current_debian_repo = mirror[2]
                mirrors.append([is_current, mirror[0], mirror[1], mirror[2]])
        return mirrors

    def on_tvMirrors_toggle(self, obj, path, colNr, toggleValue):
        path = int(path)
        model = self.tvMirrors.get_model()
        selected_iter = model.get_iter(path)
        selected_repo = model.get_value(selected_iter, 2)

        row_cnt = 0
        itr = model.get_iter_first()
        while itr is not None:
            if row_cnt != path:
                repo = model.get_value(itr, 2)
                if repo == selected_repo:
                    model[itr][0] = False
            itr = model.iter_next(itr)
            row_cnt += 1

    # ===============================================
    # Cleanup functions
    # ===============================================

    def fill_treeview_cleanup(self):
        pck_data = []
        # Get list of packages from autoremove and obsolete
        for pck in self.autoremove_packages():
            if pck not in self.holdback:
                pck_data.append([True, pck])
        for pck in self.obsolete_packages():
            if (pck not in self.holdback and
                not any(pck in x for x in pck_data)):
                pck_data.append([False, pck])
        for pck in self.old_kernel_packages():
            if (pck not in self.holdback and
                not any(pck in x for x in pck_data)):
                pck_data.append([False, pck])
        # Fill treeview
        col_type_lst = ['bool', 'str']
        self.tvCleanupHandler.fillTreeview(pck_data, col_type_lst, 0, 400, False)

    def autoremove_packages(self):
        ret = []
        # Create approriate command
        # Use env LANG=C to ensure the output of dist-upgrade is always en_US
        cmd = "env LANG=C apt-get autoremove --assume-no | grep -E '^ '"
        lst = getoutput(cmd)

        # Loop through each line and fill the package lists
        for line in lst:
            packages = line.split()
            for package in packages:
                package = package.strip().replace('*', '')
                if package and package not in ret:
                    ret.append(package)
        return ret

    def obsolete_packages(self):
        obs_exec = 'deborphan'
        if not is_package_installed('deborphan'):
            # Alternative for deborphan
            if is_package_installed('aptitude'):
                obs_exec = "aptitude -F%p search '~o (~slibs|~soldlibs|~sintrospection) !~Rdepends:.*'"
            else:
                return []
        obs_pcks = getoutput(obs_exec)
        if len(obs_pcks) == 1 and obs_pcks[0] == '':
            obs_pcks = []
        return obs_pcks

    def old_kernel_packages(self):
        kernel_packages = []
        # Check booted kernel version
        regexp = r'[0-9][0-9\.\-]+[0-9]'
        cur_version = getoutput(f"uname -r | egrep -o '{regexp}'")[0]
        #cur_version = getoutput("ls -al / | grep -e '\svmlinuz\s' | egrep -o '%s'" % regexp)[0]
        # Get kernel packages not with cur_version
        cmd = f"dpkg-query -f '${{binary:Package}}\n' -W | grep -E 'linux-image-[0-9]|linux-headers-[0-9]' | grep -v '{cur_version}' | egrep -v '[a-z]-486|[a-z]-686|[a-z]-586'"
        packages = getoutput(cmd)
        # Check version number of found kernel packages
        for pck in packages:
            match = re.search(regexp, pck)
            if match:
                if compare_package_versions(match.group(0), cur_version) == VersionComparison.SMALLER:
                    # Add to the kernel_packages list
                    kernel_packages.append(pck)

        if kernel_packages:
            # Add kbuild packages
            del_string = '.0'
            try:
                kbuild_version = cur_version[:cur_version.index('-')]
            except:
                kbuild_version = cur_version
            while kbuild_version.endswith(del_string):
                kbuild_version = kbuild_version[:-len(del_string)]
            kbuild_packages = getoutput(f"dpkg-query -f '${{binary:Package}}\n' -W | grep linux-kbuild | grep -v '{kbuild_version}'")
            for pkg in kbuild_packages:
                if pkg:
                    kernel_packages.append(pkg)
        return kernel_packages

    def remove_unneeded_packages(self):
        force = get_apt_force()
        packages = []
        # Build list with selected packages
        model = self.tvCleanup.get_model()
        itr = model.get_iter_first()
        while itr is not None:
            if model.get_value(itr, 0):
                packages.append(model.get_value(itr, 1))
            itr = model.iter_next(itr)
        if packages:
            # Run cleanup in a thread and show progress
            name = 'cleanup'
            self.set_buttons_state(False)
            cmd = f"apt-get {force} clean; apt-get purge {force} {' '.join(packages)}"
            thread = ExecuteThreadedCommands(cmd, self.queue)
            self.threads[name] = thread
            thread.daemon = True
            thread.start()
            self.queue.join()
            GLib.timeout_add(250, self.check_thread, name)

    # ===============================================
    # Boot splash functions
    # ===============================================

    def fill_treeview_installed_plymouth(self):
        themes = [[False, 'None']]
        cursor = 0
        cnt = 0
        for theme in self.installed_plymouth_themes:
            current = False
            cnt += 1
            if self.current_plymouth_theme == theme:
                current = True
                cursor = cnt
            themes.append([current, theme])
        if cursor == 0:
            themes[0][0] = True

        col_type_lst = ['bool', 'str']
        self.tvSplashHandler.fillTreeview(themes, col_type_lst, cursor, 400, False)

    def fill_treeview_installed_grub(self):
        themes = [[False, 'None']]
        cursor = 0
        cnt = 0
        for theme in self.grub.installed_themes:
            current = False
            cnt += 1
            if self.grub.theme == theme:
                current = True
                cursor = cnt
            themes.append([current, self.grub.theme_name(theme)])
        if cursor == 0:
            themes[0][0] = True

        col_type_lst = ['bool', 'str']
        self.tvGrubHandler.fillTreeview(themes, col_type_lst, cursor, 400, False)

    def fill_cmb_splash_resolution(self):
        sel_res = '1024x768'
        cur_res = self.plymouth.current_resolution()
        if not cur_res:
            cur_res = get_current_resolution()
        resolutions = get_resolutions(use_vesa=True)
        for res in resolutions:
            try:
                if int(res.split('x')[0]) >= int(cur_res.split('x')[0]):
                    sel_res = res
                    break
            except:
                pass
        self.cmbSplashResolutionHandler.fillComboBox(resolutions, sel_res)

    def on_tvSplashHandler_toggled(self, obj, path, col_nr, toggle_value):
        path = int(path)
        model = self.tvSplash.get_model()
        selected_iter = model.get_iter(path)

        # Prevent de-selecting current theme
        if not toggle_value:
            model[selected_iter][0] = True
            return

        # De-select any other theme if needed
        row_cnt = 0
        itr = model.get_iter_first()
        while itr is not None:
            if row_cnt != path:
                model[itr][0] = False
            itr = model.iter_next(itr)
            row_cnt += 1

    def on_tvGrubHandler_toggled(self, obj, path, col_nr, toggle_value):
        path = int(path)
        model = self.tvGrub.get_model()
        selected_iter = model.get_iter(path)

        # Prevent de-selecting current theme
        if not toggle_value:
            model[selected_iter][0] = True
            return

        # De-select any other theme if needed
        row_cnt = 0
        itr = model.get_iter_first()
        while itr is not None:
            if row_cnt != path:
                model[itr][0] = False
            itr = model.iter_next(itr)
            row_cnt += 1

    def boot_splash_multi_threading(self):
        plymouth_theme = self.tvSplashHandler.getToggledValues()[0]
        grub_theme = self.tvGrubHandler.getToggledValues()[0]
        resolution = self.cmbSplashResolutionHandler.getValue()
        splash = str(plymouth_theme) != 'None'

        # Update alternatives
        desktop_themes = glob(fr'/usr/share/desktop-base/{grub_theme}*/')
        desktop_theme = ''
        if not desktop_themes:
            desktop_themes = glob(fr'/usr/share/desktop-base/{plymouth_theme}*/')
        if desktop_themes:
            desktop_theme = desktop_themes[0].rstrip("/")
            shell_exec(rf'update-alternatives --set desktop-theme {desktop_theme}')

        # Change Grub and Plymouth background images according to screen resolution
        ratio = get_current_aspect_ratio()
        # Grub
        src = f"{desktop_theme}/grub/grub-16x9.png"
        dst = f"/usr/share/grub/themes/{grub_theme}/bg.png"
        if ratio == '4:3':
            src = f"{desktop_theme}/grub/grub-4x3.png"
        if exists(src) and exists(dst):
            shutil.copyfile(src, dst)

        #Plymouth
        dst = f"/usr/share/plymouth/themes/{plymouth_theme}/bg.png"
        if exists(src) and exists(dst):
            shutil.copyfile(src, dst)

        self.grub.save(grub_theme, resolution, splash)
        self.plymouth.save(plymouth_theme)
        self.lightdm.save(plymouth_theme)

    def save(self):
        name = 'splash'
        self.set_buttons_state(False)
        thread = Thread(target=self.boot_splash_multi_threading)
        self.threads[name] = thread
        thread.daemon = True
        thread.start()
        GLib.timeout_add(250, self.check_thread, name)

    # ===============================================
    # General functions
    # ===============================================

    def check_thread(self, name):
        if self.threads[name].is_alive():
            if name in ['update', 'cleanup', 'driver', 'splash']:
                self.update_progress(0.1, True)
            if not self.queue.empty():
                ret = self.queue.get()
                self.queue.task_done()
                if ret:
                    self.log.write(f"Queue returns: {ret}", 'check_thread')
                    if name == 'localize':
                        if ret[0] > 0 and ret[1] > 0:
                            self.update_progress(1 / (ret[0] / ret[1]))
                        else:
                            self.update_progress(0)
                    elif name == 'endecrypt':
                        # Queue returns list: [fraction, error_code, partition_index, partition, message]
                        self.endecrypt_success = True
                        self.update_progress(ret[0])
                        if ret[1] > 0:
                            self.log.write(str(ret[4]), name, 'error')
                            self.endecrypt_success = False
                        if ret[2] is not None and ret[3] is not None:
                            # Replace old partition with new partition in my_partitions
                            self.my_partitions[ret[2]] = ret[3]
                    elif name == 'changepassphrase':
                        # Queue returns list: [fraction, error_code, partition_index, partition, message]
                        self.update_progress(ret[0])
                        if ret[1] > 0:
                            self.log.write(str(ret[4]), name, 'error')
                        if ret[2] is not None and ret[3] is not None:
                            # Replace old partition with new partition in my_partitions
                            self.my_partitions[ret[2]] = ret[3]
                            self.changed_devices.append(ret[3]['device'].replace('/mapper', ''))
            return True

        # Thread is done
        print((f"Thread {name} ended"))
        if not self.queue.empty():
            ret = self.queue.get()
            self.queue.task_done()
            if ret:
                self.log.write(f"Queue returns: {ret}", 'check_thread')
                if name == 'endecrypt':
                    # Queue returns list: [fraction, error_code, partition, message]
                    self.endecrypt_success = True
                    self.update_progress(ret[0])
                    if ret[1] > 0:
                        self.log.write(str(ret[4]), name, 'error')
                        self.endecrypt_success = False
                    if ret[2] is not None and ret[3] is not None:
                        # Replace old partition with new partition in my_partitions
                        self.my_partitions[ret[2]] = ret[3]
                elif name == 'changepassphrase':
                    # Queue returns list: [fraction, error_code, partition_index, partition, message]
                    self.update_progress(ret[0])
                    if ret[1] > 0:
                        self.log.write(str(ret[4]), name, 'error')
                    if ret[2] is not None and ret[3] is not None:
                        # Replace old partition with new partition in my_partitions
                        self.my_partitions[ret[2]] = ret[3]
                        self.changed_devices.append(ret[3]['device'].replace('/mapper', ''))
        del self.threads[name]

        if 'update' in name:
            self.mirrors = self.list_mirrors()
            self.fill_treeview_mirrors()
            self.update_progress(0)
            self.set_buttons_state(True)
        elif name == 'cleanup':
            self.fill_treeview_cleanup()
            self.update_progress(0)
            self.set_buttons_state(True)
        elif name in ['localize', 'splash']:
            msg = _("You need to reboot your system for the new settings to take affect.")
            MessageDialog(_("Reboot"), msg)
            self.update_progress(0)
            self.set_buttons_state(True)
        elif name == 'endecrypt':
            if self.endecrypt_success:
                # Write all needed configuration
                self.write_partition_configuration()

                # Ask to reboot
                answer = False
                if self.encrypt:
                    answer = QuestionDialog(_("Encryption done"),
                                            _("Encryption has finished.\n\n"
                                              "Do you want to restart your computer?"))
                else:
                    answer = QuestionDialog(_("Decryption done"),
                                            _("Decryption has finished.\n\n"
                                              "Do you want to restart your computer?"))
                if answer:
                    # Reboot
                    shell_exec('reboot')

            # Refresh
            self.update_progress(0)
            self.on_btnRefresh_clicked(None)
            self.set_buttons_state(True)
        elif name == 'changepassphrase':
            if self.changed_devices:
                devices = ', '.join(self.changed_devices)
                msg = _(f"Passphrase changed for {devices}.")
                MessageDialog(self.btnChangePassphrase.get_label(), msg)
            self.update_progress(0)
            self.set_buttons_state(True)
        else:
            self.update_progress(0)
            self.set_buttons_state(True)

        return False

    def set_buttons_state(self, enable):
        self.btnSaveBackports.set_sensitive(enable)
        self.btnSaveMirrors.set_sensitive(enable)
        self.btnEncrypt.set_sensitive(enable)
        self.btnDecrypt.set_sensitive(enable)
        self.btnRefresh.set_sensitive(enable)
        self.btnChangePassphrase.set_sensitive(enable)
        self.btnCreateKeyfile.set_sensitive(enable)
        self.btnSaveLocale.set_sensitive(enable)
        self.btnHoldback.set_sensitive(enable)
        self.btnRemoveHoldback.set_sensitive(enable)
        self.btnCleanup.set_sensitive(enable)
        self.btnSaveFstabMounts.set_sensitive(enable)
        self.btnSaveDeviceDriver.set_sensitive(enable)
        self.btnSaveSplash.set_sensitive(enable)

    def language_dir(self):
        # First test if full locale directory exists, e.g. html/pt_BR,
        # otherwise perhaps at least the language is there, e.g. html/pt
        # and if that doesn't work, try html/pt_PT
        lang = self.current_language()
        path = join(self.html_dir, lang)
        if not isdir(path):
            base_lang = lang.split('_')[0].lower()
            path = join(self.html_dir, base_lang)
            if not isdir(path):
                path = join(self.html_dir, f"{base_lang}_{base_lang.upper()}")
                if not isdir(path):
                    path = join(self.html_dir, 'en')
        return path

    def current_language(self):
        lang = os.environ.get('LANG', 'US').split('.')[0]
        if lang == '':
            lang = 'en'
        return lang

    def passphrase_dialog(self, device_path):
        passphrase_title = _("Partition passphrase")
        passphrase_text = _("Please, provide the current passphrase\n"
                            "for the encrypted partition")
        return InputDialog(title=passphrase_title,
                           text=f"{passphrase_text}:\n\n<b>{device_path}</b>",
                           is_password=True).show()

    def update_progress(self, step=-1, pulse=False, text=None):
        if step >= 0 and step <= 1:
            if pulse:
                self.progressbar.set_pulse_step(step)
                self.progressbar.pulse()
            else:
                self.progressbar.set_fraction(step)
        else:
            self.progressbar.pulse()
        if text is not None:
            self.progressbar.set_text(str(text))

    def temp_mount(self, partition, passphrase=None):
        mount_point =  join(TMPMOUNT, basename(partition['device']))
        return self.udisks2.mount_device(partition['old_device'],
                                         mount_point, None, None, passphrase)

    def temp_unmount_all(self):
        # Unmount temp mounts and remove
        tmp_mounts = getoutput(f"grep '{TMPMOUNT}' /proc/mounts | awk '{{print $1,$2}}'")
        for tmp_mount in tmp_mounts:
            try:
                device, mount = tmp_mount.split()
                try:
                    if self.udisks2.unmount_device(device):
                        self.log.write(f"Remove temporary mount point: {mount}",
                                       'temp_unmount_all', 'info')
                        os.rmdir(mount)
                    else:
                        self.log.write(f"Unable to remove temporary mount point: {mount}",
                                       'temp_unmount_all', 'warning')
                except Exception as exception:
                    self.log.write(f"ERROR: {exception}", 'temp_unmount_all')
            except:
                pass

    # Close the gui
    def on_windowPref_destroy(self, widget):
        self.temp_unmount_all()
        Gtk.main_quit()
