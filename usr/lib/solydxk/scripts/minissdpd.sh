#!/bin/bash

MINISSDPD='/etc/default/minissdpd'
VAR='MiniSSDPd_INTERFACE_ADDRESS'

if [ -f "$MINISSDPD" ]; then
    INTERFACES=$(ip addr list | grep -E 'BROADCAST.*UP' | awk -F': ' '/^[0-9]/ {print $2}')
    for I in $INTERFACES; do
        [ -z "$S" ] && S="$I" || S="$S $I"
    done

    if [ ! -z "$S" ]; then
        if grep -q "\"$S\"" "$MINISSDPD"; then
            echo "$MINISSDPD already configured: $VAR=\"$S\""
        else
            echo "Configure $MINISSDPD: $VAR=\"$S\""
            sed -i "s/$VAR=.*/$VAR=\"$S\"/" $MINISSDPD
        fi
    fi
fi

exit 0
