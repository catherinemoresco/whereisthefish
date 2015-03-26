#!/bin/sh
exec /usr/bin/Xvfb :0 -screen 0 480x432x24 -ac +extension GLX +render -noreset >>/var/log/xvfb.log 2>&1
