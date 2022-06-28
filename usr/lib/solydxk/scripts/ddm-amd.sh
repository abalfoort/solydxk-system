#!/bin/bash

# ==============================================
# DDM AMD driver installation for Stretch
# ==============================================
# Based on: https://wiki.debian.org/AtiHowTo
# New supported cards (GCN): https://en.wikipedia.org/wiki/Graphics_Core_Next
# ==============================================

# URL to lkddb files
LKDDB="https://downloads.solydxk.com/lkddb"
# KV=$(uname -r)
# KV=${KV%.*}
# URL="https://downloads.solydxk.com/lkddb/lkddb-$KV.list"
# wget -O lkddb.list $URL
# AMDGPU=$(grep -oP '(?<=1002\s)[a-z0-9]*(?=\s.*CONFIG_DRM_AMDGPU)' lkddb.list)
# AMDRAD=$(grep -oP '(?<=1002\s)[a-z0-9]*(?=\s.*CONFIG_DRM_RADEON)' lkddb.list)

# AMDGPU supported code names
GCN1='Oland Cape Pitcairn Tahiti Hainan Curacao Trinidad Iceland Topaz Opal Venus Neptune'
GCN2='Bonaire Hawaii Samoa Tobago Malta Zealand Vesuvius Saturn Grenada Temash Kabini Kaveri Godavari Beema Mullins Carrizo-L'
GCN3='Tonga Fiji Antigua Carrizo Bristol Stoney Amethyst'
GCN4='Polaris Lexa Baffin Ellesmere Neo Scorpio'
GCN5='Vega Greenland Instinct Raven'
NGM='Navi'
SUPPORTEDCARDS="$GCN1 $GCN2 $GCN3 $GCN4 $GCN5 $NGM"

# Default value to use backports
BACKPORTS=false

# Old AMD packages
OLDAMD='xserver-xorg-video-ati xserver-xorg-video-radeon xserver-xorg-video-r128 xserver-xorg-video-mach64'

# New AMD
NEWAMD='xserver-xorg-video-amdgpu'

# Additional packages
ADDITIONALPCKS="linux-headers-$(uname -r) build-essential firmware-linux-nonfree"

# Purge these in any case
PURGEPCKS='fglrx* libgl1-fglrx-glx* amd-opencl-icd'

# Additional apt parameters
APTFORCE='--allow-downgrades --allow-remove-essential --allow-change-held-packages'

# Default value for testing
# Set TESTHWCARD to test the script with different AMD/ATI hardware.
TEST=false
#TESTHWCARD='Advanced Micro Devices, Inc. [AMD/ATI] Bonaire [FirePro W5100] [1002:6649]'
#TESTHWCARD='Advanced Micro Devices, Inc. [AMD/ATI] Tonga PRO [Radeon R9 285/380] [1002:6939]'
#TESTHWCARD='Advanced Micro Devices, Inc. [AMD/ATI] RV710 [Radeon HD 4350/4550] [1002:954f]'
#TESTHWCARD='Advanced Micro Devices, Inc. [AMD/ATI] Barts PRO [Radeon HD 6850] [1002:6739]'
#TESTHWCARD='Advanced Micro Devices, Inc. [AMD/ATI] Seymour [Radeon HD 6400M/7400M Series] [1002:6760]'
TESTHWCARD='Advanced Micro Devices, Inc. [AMD/ATI] Ellesmere [Radeon RX 470/480] [1002:67df]'

# Default to show supported hardware only
SHOW=false

# ==============================================
# End configuration
# ==============================================

# Log file for traceback
MAX_SIZE_KB=5120
LOG_SIZE_KB=0
LOG=/var/log/solydxk-system.log
LOG2=/var/log/solydxk-system.log.1
if [ -f $LOG ]; then
  LOG_SIZE_KB=$(($(stat -c%s $LOG) / 1024))
  if [ $LOG_SIZE_KB -gt $MAX_SIZE_KB ]; then
    mv -f $LOG $LOG2
  fi
fi

# ==============================================

function get_backports_string() {
  PCK=$1
  local BPSTR=''
  BP=$(grep backports /etc/apt/sources.list /etc/apt/sources.list.d/*.list | grep debian | grep -v 'list:#' | awk '{print $3}')
  if [ "$BP" != '' ]; then
    BP=$(echo $BP | cut -d' ' -f 1)
    PCKCHK=$(apt-cache madison $PCK | grep "$BP")
    if [ "$PCKCHK" != '' ]; then
      BPSTR="-t $BP"
    fi
  fi
  echo $BPSTR
}

# ==============================================

function usage() {
  echo
  echo "Device Driver Manager Help for $(basename $0)"
  echo 
  echo 'The following options are allowed:'
  echo
  echo '-b           Use backported packages when available.'
  echo
  echo '-h           Show this help.'
  echo
  echo '-s           Show supported and available hardware.'
  echo
  echo '-t           For developers: simuluate driver installation.'
  echo '             Change TESTHWCARD in this script to select different hardware.'
  echo
}

# ==============================================
# ==============================================

# Get bash arguments
FORCE=false
while getopts ':bfhst' opt; do
  case $opt in
    b)
      # Backports
      BACKPORTS=true
      ;;
    f)
      FORCE=true
      ;;
    h)
      usage
      exit 0
      ;;
    s)
      # Show supported hardware
      SHOW=true
      ;;
    t)
      # Testing
      TEST=true
      ;;
    :)
      echo "Option -$OPTARG requires an argument."
      exit 2
      ;;
    *)
      # Unknown error
      echo "Unknown argument $@"
      exit 2
      ;;
  esac
done

# Run this script as root
if [ $UID -ne 0 ] && ! $SHOW; then
  sudo "$0" "$@"
  exit $?
fi

# Get distribution release
if [ -f /etc/debian_version ]; then
  DISTRIB_RELEASE=$(head -n 1 /etc/debian_version 2>/dev/null | sed 's/[a-zA-Z]/0/' | cut -d'.' -f 1)
fi

if [ -z $DISTRIB_RELEASE ]; then
  echo '[AMD] Cannot get the Debian version from /etc/debian_version.' | tee -a $LOG 2>/dev/null
  echo '[AMD] Please install the base-files package.' | tee -a $LOG 2>/dev/null
  exit 8
fi

# Non-numeric values means that it's testing (sid)
if [[ $DISTRIB_RELEASE =~ '^[0-9]+$' ]] ; then
  if [ $DISTRIB_RELEASE -lt 9 ]; then
    echo '[AMD] This script is for Debian Stretch and beyond.' | tee -a $LOG 2>/dev/null
    exit 0
  fi
fi

# Get AMD graphical cards
BCID='1002'
HWCARD=$(lspci -nn -d $BCID: | egrep -i ' 3d | display | vga ' | head -n 1)
# Cleanup
HWCARD="${HWCARD#*: }"
HWCARD="${HWCARD%(rev*}"
# Testing
if $TEST; then
  HWCARD=$TESTHWCARD
fi

if [ "$HWCARD" == '' ]; then
  if ! $SHOW; then
    echo '[AMD] No AMD/ATI card found.' | tee -a $LOG 2>/dev/null
  fi
  exit 0
fi

# Default to old packages
PCKS=$OLDAMD

# Check on device id
CODENAME=$(lsb_release -cs)
FILENAME="${CODENAME}_amdgpu.txt"
SAVEPATH="/tmp/$FILENAME"
# Download ID list from server if not already downloaded
if [ ! -f "$SAVEPATH" ]; then
    URL="$LKDDB/$FILENAME"
    echo "[AMD] Download card ID list from $URL." | tee -a $LOG 2>/dev/null
    wget -q -O "$SAVEPATH.0" "$URL"
    if [ -f "$SAVEPATH.0" ]; then
        # Check that file is not empty
        if [ -s "$SAVEPATH.0" ]; then
            mv -f "$SAVEPATH.0" "$SAVEPATH"
        fi
    fi
fi
# Save the IDs in a variable
if [ -f "$SAVEPATH" ]; then
    SUPPORTEDIDS=$(cat $SAVEPATH)
fi
# Check if card ID is found in ID list
CARDFOUND=false
if [ "$SUPPORTEDIDS" != '' ]; then
    DEVICEID=$(echo "$HWCARD" | grep -oP '(?<=:)[a-z0-9]*(?=\])')
    for SID in $SUPPORTEDIDS; do
        if [ "$SID" == "$DEVICEID" ]; then
            echo "[AMD] Card ID $DEVICEID found in $SAVEPATH." | tee -a $LOG 2>/dev/null
            PCKS=$NEWAMD
            CARDFOUND=true
            break
        fi
    done
fi

# Could not find card in ID list: fall back to card names
if ! $CARDFOUND; then
    # Turn on a case-insensitive matching
    shopt -s nocasematch
    for SCARD in $SUPPORTEDCARDS; do
        if [[ "$HWCARD" =~ "$SCARD" ]]; then
            echo "[AMD] Card name $SCARD found in $HWCARD." | tee -a $LOG 2>/dev/null
            PCKS=$NEWAMD
            break
        fi
    done
    # Turn off a case-insensitive matching
    shopt -u nocasematch
fi

# Show supported hardware only (include drivers)
if [ "$HWCARD" != '' ] && $SHOW; then
  echo "$HWCARD [$PCKS]"
  exit 0
fi

# If old driver is needed, make sure the new driver is not installed
if [ "$PCKS" == "$OLDAMD" ]; then
  PURGEPCKS="$NEWAMD $PURGEPCKS"
fi

# Add additional packages
PCKS="$ADDITIONALPCKS $PCKS"

# Check if all these packages exist in the repository
if ! $TEST && ! $SHOW; then
  apt-get update
fi
for PCK in $PCKS; do
  PCKINFO=$(apt-cache show "$PCK" 2>/dev/null)
  if [ "$PCKINFO" == '' ]; then
    echo "[AMD] Unable to install $PCK: not in repository." | tee -a $LOG 2>/dev/null
    exit 7
  fi
done

# Start installing the packages
if $TEST && ! $FORCE; then
  echo "[AMD] - TEST - Install packages: $PCKS." | tee -a $LOG 2>/dev/null
  if [ "$PURGEPCKS" != '' ]; then
    echo "[AMD] - TEST - Purge packages: $PURGEPCKS." | tee -a $LOG 2>/dev/null
  fi
else
  for PCK in $PCKS; do
    # Backport?
    BP=''
    if $BACKPORTS; then
      BP=$(get_backports_string $PCK)
    fi
    echo "[AMD] Run command: apt-get install --reinstall $BP -y $APTFORCE $PCK." | tee -a $LOG 2>/dev/null
    apt-get install --reinstall $BP -y $APTFORCE $PCK 2>&1 | tee -a $LOG 2>/dev/null
  done
    
  # Purge packages if needed
  for PCK in $PURGEPCKS; do
    echo "[AMD] Run command: apt-get purge -y $APTFORCE $PCK" | tee -a $LOG 2>/dev/null
    apt-get purge -y $APTFORCE $PCK 2>&1 | tee -a $LOG 2>/dev/null
  done
    
  echo '[AMD] AMD driver installed.' | tee -a $LOG 2>/dev/null
fi
