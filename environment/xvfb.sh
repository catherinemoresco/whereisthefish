#!/bin/sh
exec /usr/bin/Xvfb :0 -screen 0 640x576x24 -ac +extension GLX +render -noreset >>/var/log/xvfb.log 2>&1
