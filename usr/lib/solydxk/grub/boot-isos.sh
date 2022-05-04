#! /bin/bash
# boot-isos.sh  2.4.0  2020-07-10

[ "$1" == "test" ] && T1=true
[ "$2" ] && ISODIR="$2" || ISODIR='boot-isos'

# On journaling filesystems, plain 'mount' can never be truly read-only, so
# grub-mount - which is - should be used in preference, if it's available.
MOUNT=$(which grub-mount) || MOUNT=mount

function check_partition {
	PART=$1		# Partition (e.g. /dev/sda1)
	UUID=$2		# UUID of this partition
	MPNT=$3		# Current mount point or empty if not mounted

	[ $T1 ] && echo "Checking $PART . . ." >&2

	# Mount the partition if it is not mounted already
	if [ "$MPNT" ]; then
		[ $T1 ] && echo "- already mounted on $MPNT" >&2
	else
		MPNT="/mnt/${PART:7}"
		[ $T1 ] && echo "- mounting on $MPNT" >&2
		mkdir -p $MPNT
		$MOUNT $PART $MPNT
	fi

	# SolydXK - add live iso menu entries if isos were found in given partition
	ISOPATH="$MPNT/$ISODIR"
	[ $T1 ] && echo "- checking for ISOs in $ISOPATH . . ." >&2
	if [ "$(ls -A $ISOPATH/*.iso 2>/dev/null)" ]; then
		# Get the partition scheme ('msdos' or 'gpt')
		PTS=$(cut -d: -f6 <(grep -F ${PART:0:8} <(parted -m ${PART:0:8} print)))
		# Get boot parameters
		BOOTPRMS=""
		if [ -f /etc/default/grub ]; then
			. /etc/default/grub
			BOOTPRMS="$GRUB_CMDLINE_LINUX_DEFAULT"
		fi
		# Add an empty line
		cat <<-EOT
		 	menuentry ' ' {
		 		true
		 	}
		EOT

		ISOMOUNT=/mnt/boot-isos-temp-mount
		mkdir -p $ISOMOUNT

		# Loop through the ISOs
		for ISO in $ISOPATH/*.iso; do

			# Find the full names of the kernel files
			$MOUNT $ISO $ISOMOUNT 2>/dev/null
			VMLINUZ=$(echo $ISOMOUNT/live/vmlinuz*)
			INITRD=$(echo $ISOMOUNT/live/initrd.img*)
			umount $ISOMOUNT 2>/dev/null

			if [ "${VMLINUZ: -1}" != "*" ]; then
				ISONAME=${ISO##*/}
				cat <<-EOT
				 	menuentry 'Live: $ISONAME' {
				 		insmod part_$PTS
				 		insmod loopback
				 		search --no-floppy --fs-uuid --set=isopart $UUID
				 		loopback loop (\$isopart)/$ISODIR/$ISONAME
				 		linux (loop)/live/${VMLINUZ##*/} boot=live findiso=/$ISODIR/$ISONAME noprompt noeject noswap config $BOOTPRMS
				 		initrd (loop)/live/${INITRD##*/}
				 	}
				EOT
			else
				[ $T1 ] && echo "- failed to find kernel files in $ISO" >&2
			fi
		done

		rmdir $ISOMOUNT
	fi

	# Unmount the device if it was mounted by this script
	if [ ! "$3" ]; then
		umount $MPNT 2>/dev/null
		rmdir $MPNT
	fi
}

# Search for isos on all available partitions
while read -r BLK; do
	NM=$(echo $BLK | awk '{print $1}')
	TP=$(echo $BLK | awk '{print $2}')
	FS=$(echo $BLK | awk '{print $3}')
	ID=$(echo $BLK | awk '{print $4}')
	MP=$(echo $BLK | awk '{print $5}')
	# only look at partitions with a filesystem (i.e. ignore extended and
	# unformatted (BIOS boot) partitions) which are not root or swap (can't use
	# MP for that, as that might miss swap partitions on other disks)
	if [ ! -z $FS ] && [[ 'part crypt' == *$TP* ]] && [[ 'swap crypto_LUKS' != *$FS* ]] && [ "$MP" != "/" ]; then
		check_partition "$NM" "$ID" "$MP"
	fi
done < <(lsblk -lpno NAME,TYPE,FSTYPE,UUID,MOUNTPOINT)
