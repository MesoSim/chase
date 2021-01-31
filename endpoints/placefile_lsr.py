#!/usr/bin/env python

"""
LSR Placefile Endpoint
----------------------

Provides the LSR placefile during the simulation.

...

! IMPORTANT !
Update the constants to their proper values, and update the shebang above to
your conda environment.

What this script does when run:

- Gets the LSRs during the valid time

"""

# Imports
import json
import pytz
import sys
from sqlite3 import dbapi2 as sql
from datetime import datetime, timedelta
from mesosim.core.config import Config
from mesosim.core.timing import arc_time_from_cur, std_fmt
from mesosim.lsr import (scale_raw_lsr_to_cur_time,
                          gr_lsr_placefile_entry_from_tuple)


# Constants

# Critical Files
lsr_db_file = "/home/jthielen/lsr.db"
main_db_file = "/home/jthielen/main.db"

# Assets
lsr_asset_url = 'https://chase.iawx.info/assets/'


# Output HTTP Header
print("Content-type: text/plain\r\n")

# Header
print("""\n
RefreshSeconds: 5
Threshold: 999
Title: Live Storm Reports (LSRs)
Font: 1, 11, 0, "Courier New"
IconFile: 1, 25, 25, 11, 11, "{url}Lsr_FunnelCloud_Icon.png"
IconFile: 2, 25, 32, 11, 11, "{url}Lsr_Hail_Icons.png"
IconFile: 3, 25, 25, 11, 11, "{url}Lsr_Tornado_Icon.png"
IconFile: 4, 25, 25, 11, 11, "{url}Lsr_TstmWndDmg_Icon.png"
""".format(url=lsr_asset_url))

# Get the master settings
try:
    config = Config(main_db_file)
    hours_valid = config.lsr_hours_valid  # LSR Validity (archive time)
    remark_wrap_length = int(config.get_config_value("lsr_remark_wrap_length"))  # Text Wrapping
except:
    # If failed, exit with empty
    sys.exit()

# Open database
try:
    lsr_con = sql.connect(lsr_db_file)
    lsr_cur = lsr_con.cursor()
except:
    # If failed, exit with empty
    sys.exit()

# Prep the time interval (arc time)
t1 = arc_time_from_cur(datetime.now(tz=pytz.UTC), timings=config.timings)
t0 = t1 - timedelta(hours=hours_valid)
t0, t1 = (t.strftime(std_fmt) for t in [t0, t1])

# Get the data
lsr_cur.execute("SELECT * FROM lsrs_raw WHERE valid BETWEEN ? AND ?", [t0, t1])
lsrs_raw = lsr_cur.fetchall()

# Scale the data to cur time
lsrs_scaled = scale_raw_lsr_to_cur_time(lsrs_raw, timings=config.timings)

# Output the LSRs
for lsr_tuple in lsrs_scaled:
    print(gr_lsr_placefile_entry_from_tuple(
        lsr_tuple,
        wrap_length=remark_wrap_length
    ))
    print()
