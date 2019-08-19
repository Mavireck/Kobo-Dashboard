#!/bin/sh

# # Load wifi modules and enable wifi.
# lsmod | grep -q sdio_wifi_pwr || insmod "/drivers/${PLATFORM}/wifi/sdio_wifi_pwr.ko"
# # Moar sleep!
# usleep 250000
# # WIFI_MODULE_PATH = /drivers/$PLATFORM/wifi/$WIFI_MODULE.ko
# lsmod | grep -q "${WIFI_MODULE}" || insmod "${WIFI_MODULE_PATH}"
# # Race-y as hell, don't try to optimize this!
# sleep 1

# ifconfig "${INTERFACE}" up
# [ "$WIFI_MODULE" != "8189fs" ] && [ "${WIFI_MODULE}" != "8192es" ] && wlarm_le -i "${INTERFACE}" up

# pidof wpa_supplicant >/dev/null \
#     || env -u LD_LIBRARY_PATH \
#         wpa_supplicant -D wext -s -i "${INTERFACE}" -O /var/run/wpa_supplicant -c /etc/wpa_supplicant/wpa_supplicant.conf -B



WIFI_TIMEOUT=0
while lsmod | grep -q sdio_wifi_pwr; do
    # If the Wifi hasn't been killed by Nickel within 5 seconds, assume it's not going to...
    if [ ${WIFI_TIMEOUT} -ge 20 ]; then
        return 0
    fi
    # Nickel hasn't killed Wifi yet. We sleep for a bit (250ms), then try again
    usleep 250000
    WIFI_TIMEOUT=$(( WIFI_TIMEOUT + 1 ))
done

# Load wifi modules and enable wifi.
lsmod | grep -q sdio_wifi_pwr || insmod "/drivers/${PLATFORM}/wifi/sdio_wifi_pwr.ko"
# Moar sleep!
usleep 250000
# WIFI_MODULE_PATH = /drivers/$PLATFORM/wifi/$WIFI_MODULE.ko
lsmod | grep -q "${WIFI_MODULE}" || insmod "${WIFI_MODULE_PATH}"
# Race-y as hell, don't try to optimize this!
sleep 1

ifconfig "${INTERFACE}" up
[ "$WIFI_MODULE" != "8189fs" ] && [ "${WIFI_MODULE}" != "8192es" ] && wlarm_le -i "${INTERFACE}" up

pidof wpa_supplicant >/dev/null \
    || env -u LD_LIBRARY_PATH \
        wpa_supplicant -D wext -s -i "${INTERFACE}" -O /var/run/wpa_supplicant -c /etc/wpa_supplicant/wpa_supplicant.conf -B

# Before obtaining an IP address via DHCP, we should determine whether wpa_supplicant connects successfully or not.
# We use the wpa_cli application to do this, checking 'wpa_state' for 'COMPLETED'. Some other states I've seen
# are DISCONNECTED, SCANNING and ASSOCIATING. There are probably others.
WIFI_TIMEOUT=0
while ! wpa_cli status | grep -q "wpa_state=COMPLETED"; do
    # If wpa_supplicant hasn't connected within 5 seconds, we couldn't connect to the Wifi network
    if [ ${WIFI_TIMEOUT} -ge 20 ]; then
        # Disable the Wifi stuff we have enabled before exiting...
        disable_wifi
        return 1
    fi
    usleep 250000
    WIFI_TIMEOUT=$(( WIFI_TIMEOUT + 1 ))
done

# Release IP and shutdown udhcpc.
pkill -9 -f '/bin/sh /etc/udhcpc.d/default.script'
ifconfig "${INTERFACE}" 0.0.0.0

# Use udhcpc to obtain IP.
env -u LD_LIBRARY_PATH udhcpc -S -i "${INTERFACE}" -s /etc/udhcpc.d/default.script -t15 -T10 -A3 -b -q