#! /bin/sh


# Start from our working directory
cd "${0%/*}" || exit 1


# Siphon a few things from nickel's environment
eval "$(xargs -n 1 -0 <"/proc/$(pidof nickel)/environ" | grep -e DBUS_SESSION_BUS_ADDRESS -e NICKEL_HOME -e WIFI_MODULE -e LANG -e WIFI_MODULE_PATH -e INTERFACE 2>/dev/null)"
export DBUS_SESSION_BUS_ADDRESS NICKEL_HOME WIFI_MODULE LANG WIFI_MODULE_PATH INTERFACE
# Flush the disks: might help avoid damaging nickel's DB...
sync
# Stop kobo software because it's running
killall nickel hindenburg sickel fickel fmon > /dev/null 2>&1

# ./nickel_dash.sh &
cd /mnt/onboard/.adds/mavireck/Kobo-Dashboard
python dashboard.py