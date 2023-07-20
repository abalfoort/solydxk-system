#!/usr/bin/env python3

import re
from os.path import basename, exists, join
from utils import shell_exec, getoutput, get_uuid, \
                  get_filesystem, get_device_from_uuid, \
                  get_package_version, compare_package_versions, \
                  VersionComparison


def clear_partition(device):
    unmount_partition(device)
    enc_key = '-pbkdf2'
    openssl_version = get_package_version('openssl')
    if compare_package_versions(openssl_version, '1.1.1') == VersionComparison.SMALLER:
        # deprecated key derivation in openssl 1.1.1+
        enc_key = '-aes-256-ctr'
    # Check "man openssl-enc" for options
    shell_exec(f"head -c 5M /dev/zero | openssl enc {enc_key} -pass pass:\"$(dd if=/dev/urandom" 
               f" bs=128 count=1 2>/dev/null | base64)\" -nosalt > {device}")


def encrypt_partition(device, passphrase, luks_version=2):
    if unmount_partition(device):
        # Cannot use echo to pass the passphrase to cryptsetup because that adds a carriadge return
        # Note: use LUKS1 for boot partitions because grub does not support LUKS2, yet:
        # https://git.savannah.gnu.org/cgit/grub.git/commit/?id=365e0cc3e7e44151c14dd29514c2f870b49f9755

        luks = '--type luks1'
        if luks_version == 2:
            luks = '--type luks2 --pbkdf argon2id'
        shell_exec(f"printf \"{passphrase}\" | cryptsetup {luks} "
                   "--cipher aes-xts-plain64 --key-size 512 --hash sha512 "
                   f"--use-random --iter-time 5000 luksFormat {device}")
        mapped_device, filesystem = connect_block_device(device, passphrase)
        return mapped_device
    return ''


def unmount_partition(device):
    shell_exec(f"umount -f {device}")
    if is_connected(device):
        shell_exec(f"cryptsetup close {device} 2>/dev/null")
    ret = getoutput(f"grep '{device} ' /proc/mounts")[0]
    if not device in ret:
        return True
    return False


def connect_block_device(device, passphrase):
    if exists(device):
        mapped_name = basename(device)
        shell_exec(f"printf \"{passphrase}\" | cryptsetup open --type luks {device} {mapped_name}")
        # Collect info to return
        mapped_device = join('/dev/mapper', mapped_name)
        if exists(mapped_device):
            filesystem = get_filesystem(mapped_device)
            return (mapped_device, filesystem)
    return ('', '')

def is_connected(device):
    mapped_name = basename(device)
    if exists(join("/dev/mapper", mapped_name)):
        return True
    return False


def is_encrypted(device):
    if "crypt" in get_filesystem(device).lower() or '/dev/mapper' in device:
        return True
    return False


def get_status(device):
    status_dict = {'offset': '', 'mode': '', 'device': '', 'cipher': '', 'keysize': '',
                   'filesystem': '', 'active': '', 'type': '', 'size': ''}
    mapped_name = basename(device)
    status_info = getoutput(f"env LANG=C cryptsetup status {mapped_name}")
    for line in status_info:
        parts = line.split(':')
        if len(parts) == 2:
            status_dict[parts[0].strip()] = parts[1].strip()
        elif " active" in line:
            parts = line.split(' ')
            status_dict['active'] = parts[0]
            status_dict['filesystem'] = get_filesystem(parts[0])

    # No info has been retrieved: save minimum
    if status_dict['device'] == '':
        status_dict['device'] = device
    if status_dict['active'] == '' and is_encrypted(device):
        mapped_name = basename(device)
        status_dict['active'] = f"/dev/mapper/{mapped_name}"

    if status_dict['type'] != '':
        print((f"Encryption: mapped drive status = {status_dict}"))
    return status_dict


def create_keyfile(keyfile_path, device, passphrase):
    # Note: do this outside the chroot.
    # https://www.martineve.com/2012/11/02/luks-encrypting-multiple-partitions-on-debianubuntu-with-a-single-passphrase/
    if not exists(keyfile_path):
        shell_exec(f"dd if=/dev/urandom of={keyfile_path} bs=512 count=8 iflag=fullblock")
        shell_exec(f"chmod 000 {keyfile_path}")
    # Remove any keys for this device first
    shell_exec(f"printf \"{passphrase}\" | cryptsetup luksRemoveKey {device} {keyfile_path}")
    # Now add the new key for this device
    shell_exec(f"printf \"{passphrase}\" | cryptsetup luksAddKey {device} {keyfile_path}")


def write_crypttab(device, fs_type, crypttab_path=None, keyfile_path=None, remove_device=False):
    if crypttab_path is None or not '/' in crypttab_path:
        crypttab_path = '/etc/crypttab'
    device = device.replace('/mapper', '')

    if not exists(crypttab_path):
        with open(file=crypttab_path, mode='w', encoding='utf-8') as crypttab_fle:
            crypttab_fle.write('# <target name>\t<source device>\t<key file>\t<options>\n')

    if keyfile_path is None or keyfile_path == '':
        keyfile_path = 'none'
    crypttab_uuid = f"UUID={get_uuid(device)}"
    new_line = ''
    if not remove_device:
        swap = ''
        if fs_type == 'swap':
            swap = 'swap,'
        new_line = f"{basename(device)} {crypttab_uuid} {keyfile_path} {swap}luks,timeout=60\n"

    # Create new crypttab contents
    cont = ''
    with open(file=crypttab_path, mode='r', encoding='utf-8') as crypttab_fle:
        cont = crypttab_fle.read()
    regexp = rf".*\s{crypttab_uuid}\s.*"
    match = re.search(regexp, cont)
    if match:
        cont = re.sub(regexp, new_line, cont)
    else:
        if not remove_device:
            cont += new_line

    # Save the new crypttab
    with open(file=crypttab_path, mode='w', encoding='utf-8') as crypttab_fle:
        crypttab_fle.write(cont)


# Returns dictionary {device: {target_name, uuid, key_file}}
def get_crypttab_info(crypttab_path):
    crypttab_info = {}
    if exists(crypttab_path):
        with open(file=crypttab_path, mode='r', encoding='utf-8') as crypttab_fle:
            for line in crypttab_fle.readlines():
                line = line.strip()
                line_data = line.split()
                uuid = line_data[1].split('=')[0]
                device = get_device_from_uuid(uuid)
                if device != '':
                    key_file = line_data[2]
                    if key_file == 'none':
                        key_file = ''
                    crypttab_info[device] = {'target_name': line_data[0],
                                             'uuid': uuid,
                                             'key_file': key_file}
    return crypttab_info

def cleanup_passphrase(passphrase):
    # Only ASCII characters allowed, excluding white spaces
    clean_passphrase = ''
    for char in passphrase:
        c_code = ord(char)
        if (c_code > 32 < 95) or \
           (c_code > 96 < 127):
            clean_passphrase += char

    return clean_passphrase
