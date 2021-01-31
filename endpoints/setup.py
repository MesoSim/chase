#!/home/jthielen/miniconda3/envs/chase/bin/python

"""
Chase Setup Endpoint
--------------------

Form submission for the setup of the chase team

...

! IMPORTANT !
Update the constants to their proper values, and update the shebang above to
your conda environment.

What this script does when run:

- Sets up the users DB
- initilizes first state
- sends output to browser (which will then redirect to the chase applet itself)

or, if location

- sets lat and lon and preps for start

"""

# Imports
import cgi
from datetime import datetime
import json
from ChaseLib.App import *
from ChaseLib.functions import *


# Constants
master_db_file = 'main.db'
team_db_dir = 'teams/'


# Input Handling
form = cgi.FieldStorage()
team_id = form.getvalue('team_id')
name = form.getvalue('name')
vehicle_type = form.getvalue('vehicle')
lat = form.getvalue('lat')
lon = form.getvalue('lon')

try:
    config = Config(master_db_file)
    message = ''
    budget_bonus = 0
    info_insert = 'INSERT INTO team_info (team_setting, team_value) VALUES (?,?)'
    if lat is None:
        # this is an initial setup

        # search for team name in the database for easter egg
        config.cur.execute('SELECT * FROM name_easter_eggs WHERE input_name = ?', [name])
        search_result = config.cur.fetchall()

        if len(search_result) > 0:
            name = search_result[0][1]
            message = search_result[0][2]
            if search_result[0][3] is not None and len(search_result[0][3]) > 0:
                vehicle_type = search_result[0][3]
            if search_result[0][4] is not None and float(search_result[0][4]) > 0:
                budget_bonus = float(search_result[0][4])

        # Handle vehicle-specific setup
        vehicle = Vehicle(vehicle_type, config)
        budget = budget_bonus + config.starting_budget
        fuel_level = (1 + np.random.random()) * 0.5 * vehicle.fuel_cap

        # create the team db
        con = sql.connect(team_db_dir + team_id + '.db')
        cur = con.cursor()
        cur.execute('CREATE TABLE team_info (team_setting varchar, team_value varchar)')
        cur.execute('CREATE TABLE team_history (timestamp varchar, latitude decimal, '
                    'longitude decimal, speed decimal, direction decimal, '
                    'status_color varchar, status_text varchar, balance decimal, '
                    'points decimal, fuel_level decimal, active_hazard varchar)')
        cur.execute('CREATE TABLE action_queue (action_id varchar, message varchar, '
                    'activation_type varchar, activation_amount varchar, '
                    'action_taken varchar)')
        cur.execute(info_insert, ['name', name])
        cur.execute(info_insert, ['id', team_id])
        cur.execute(info_insert, ['vehicle', vehicle_type])
        cur.execute(info_insert, ['balance', budget])
        cur.execute(info_insert, ['fuel_level', fuel_level])
        cur.execute(info_insert, ['points', 0])
        cur.execute(info_insert, ['hazard_exp_time', None])
        cur.execute(info_insert, ['active_hazard', None])
        con.commit()

        # Build the output
        output = {
            'team_id': team_id,
            'name': name,
            'vehicle': vehicle.print_name,
            'budget': money_format(budget),
            'fuel_level': fuel_level,
            'message': message
        }

    else:
        # this is a location start
        con = sql.connect(team_db_dir + team_id + '.db')
        cur = con.cursor()
        cur.execute(info_insert, ['latitude', lat])
        cur.execute(info_insert, ['longitude', lon])
        cur.execute(info_insert, ['speed', 0])
        cur.execute(info_insert, ['direction', 0])
        cur.execute(info_insert, ['status_color', 'green'])
        cur.execute(info_insert, ['status_text', 'Chase On'])
        cur.execute(info_insert, ['timestamp',
                                  datetime.now(tz=pytz.UTC).strftime(db_time_fmt)])
        con.commit()

        # Build the output
        output = {
            'team_id': team_id,
            'success': True
        }

except Exception as exc:
    # Error Handling
    output = {'error': True, 'error_message': str(exc)}
finally:
    # Return output
    print('Content-type: application/json\r\n')
    print(json.dumps(output))
