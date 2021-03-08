#!/usr/bin/env python

"""
Chase Status Endpoint
--------------------

Quick dump of current team status

...

! IMPORTANT !
Update the constants to their proper values, and update the shebang above to
your conda environment.

What this script does when run:

- dumps the current team's status output without changes

"""

# Imports
import cgi
import json
from mesosim.chase.actions import create_hazard_registry
from mesosim.chase.team import Team
from mesosim.core.config import Config


# Constants
master_db_file = '/home/jthielen/main.db'
team_db_dir = '/home/jthielen/teams/'

# Wrap full process to safely catch errors
config = None
team = None
try:
    # Establish core config
    config = Config(master_db_file)

    # Establish the list of hazards
    hazard_registry = create_hazard_registry(config)

    # Input Handling
    form = cgi.FieldStorage()
    team_id = form.getvalue('team_id')

    # Set Up Team
    team = Team(team_db_dir + team_id + '.db', hazard_registry=hazard_registry, config=config)

    output = team.output_status_dict()

except Exception as exc:
    # Error Handling
    output = {'error': True, 'error_message': str(exc)}
finally:
    # Return output
    print('Content-type: application/json\r\n')
    print(json.dumps(output))
