#!/usr/bin/env python
"""
Main API Control
================

Using Flask-RESTful, this script hosts the resources for the full frontend API
"""

#########
# Setup #
#########

# Imports
from datetime import datetime, timedelta
import os
import pytz
from sqlite3 import dbapi2 as sql
import traceback

from flask import Flask, request, make_response
from flask_restful import Resource, Api
from mesosim.chase.actions import create_hazard_registry, shuffle_new_hazard
from mesosim.chase.team import Team
from mesosim.chase.vehicle import Vehicle
from mesosim.core.config import Config
from mesosim.core.timing import arc_time_from_cur, std_fmt
from mesosim.core.utils import direction_angle_to_str, money_format, move_lat_lon
from mesosim.lsr import scale_raw_lsr_to_cur_time, gr_lsr_placefile_entry_from_tuple
import numpy as np


# Constants
app = Flask(__name__)
api = Api(app)

lsr_db_file = "/home/jthielen/lsr.db"
main_db_file = "/home/jthielen/main.db"
team_db_dir = '/home/jthielen/teams/'

lsr_asset_url = 'https://chase.iawx.info/assets/'

config = Config(main_db_file)
hazard_registry = create_hazard_registry(config)

# Shared
def get_team(team_id):
    return Team(
        team_db_dir + team_id + '.db',
        hazard_registry=hazard_registry,
        config=config
    )


def get_vehicle(vehicle_id):
    return Vehicle(vehicle_id, config)


def vehicle_stats(vehicle):
    if vehicle is None:
        return {
            "vehicle_type": None,
            "print_name": None,
            "top_speed": None,
            "mpg": None,
            "fuel_cap": None,
            "traction_rating": None
        }
    else:
        return {
            "vehicle_type": vehicle.vehicle_type,
            "print_name": vehicle.print_name,
            "top_speed": vehicle.top_speed,
            "mpg": vehicle.mpg,
            "fuel_cap": vehicle.fuel_cap,
            "traction_rating": vehicle.traction_rating
        }


# Recreate the file header and footer texts for use in placefiles.
def file_headertext(team_name_str, preface=""):
    return (
        'RefreshSeconds: 10'
        '\nThreshold: 999'
        f'\nTitle: {preface}Location of {team_name_str}'
        '\nFont: 1, 11, 0, "Courier New"'
        '\nIconFile: 1, 22, 22, 11, 11, "http://www.spotternetwork.org/icon/spotternet.png"'
        '\nIconFile: 2, 15, 25,  8, 25, "http://www.spotternetwork.org/icon/arrows.png"'
        '\nIconFile: 3, 22, 22, 11, 11, "http://www.spotternetwork.org/icon/sn_reports.png"'
        '\nIconFile: 4, 22, 22, 11, 11, "http://www.spotternetwork.org/icon/sn_reports_30.png"'
        '\nIconFile: 5, 22, 22, 11, 11, "http://www.spotternetwork.org/icon/sn_reports_60.png"'
        '\nIconFile: 6, 22, 22, 11, 11, "http://www.spotternetwork.org/icon/spotternet_new.png"\n\n'
    )

def file_footertext(team_name):
    return '\nText: 15, 10, 1, "%s"\nEnd:\n' % (team_name,)

def file_footerend():
    return '\nEnd:\n'

def list_current_teams():
    return [
        team_db_name[:-3] for team_db_name in os.listdir(team_db_dir)
        if team_db_name[-3:] == ".db"
    ]

#########
# Teams #
#########

class TeamList(Resource):

    def get(self):
        return {
            "teams": list_current_teams() 
        }

    def post(self):
        team_id = request.form['team_id']
        team_name = request.form['team_name']
        pin = request.form['pin']
        if team_id in list_current_teams():
            # ERROR: Team exists already
            return {
                "error": True,
                "error_message": f"Team {team_id} already exists!"
            }, 409
        try:
            # New Team
            info_insert = 'INSERT INTO team_info (team_setting, team_value) VALUES (?,?)'

            # search for team name in the database for easter egg
            config.cur.execute(
                'SELECT * FROM name_easter_eggs WHERE input_name = ?',
                [team_name]
            )
            search_result = config.cur.fetchall()

            if len(search_result) > 0:
                # EASTER EGG FOUND!!
                team_name = search_result[0][1]
                message = search_result[0][2]
                if search_result[0][3] is not None and len(search_result[0][3]) > 0:
                    vehicle_type = search_result[0][3]
                if search_result[0][4] is not None and float(search_result[0][4]) > 0:
                    budget_bonus = float(search_result[0][4])
                
                # Handle vehicle-specific setup
                vehicle = Vehicle(vehicle_type, config)
                fuel_level = (1 + np.random.random()) * 0.5 * vehicle.fuel_cap
            else:
                budget_bonus = 0
                vehicle = None

            # Budget
            budget = budget_bonus + config.starting_budget
            
            # create the team db
            con = sql.connect(team_db_dir + team_id + '.db')
            cur = con.cursor()
            cur.execute('CREATE TABLE team_info (team_setting varchar, team_value varchar)')
            cur.execute('CREATE TABLE team_history (cur_timestamp varchar, '
                        'arc_timestamp varchar, latitude decimal, '
                        'longitude decimal, speed decimal, direction decimal, '
                        'status_color varchar, status_text varchar, balance decimal, '
                        'points decimal, fuel_level decimal, active_hazard varchar)')
            cur.execute('CREATE TABLE action_queue (action_id varchar, message varchar, '
                        'activation_type varchar, activation_amount varchar, '
                        'action_taken varchar)')
            cur.execute('CREATE TABLE hazard_queue (hazard_type varchar, '
                        'expiry_time varchar, message varchar, message_end varchar, '
                        'overridden_by varchar, speed_limit decimal, direction_lock varchar, '
                        'speed_lock varchar, status varchar)')
            cur.execute(info_insert, ['name', team_name])
            cur.execute(info_insert, ['id', team_id])
            cur.execute(info_insert, ['pin', pin])
            cur.execute(info_insert, ['balance', budget])
            cur.execute(info_insert, ['points', 0])
            cur.execute(info_insert, ['hazard_exp_time', None])
            cur.execute(info_insert, ['active_hazard', None])
            if vehicle is not None:
                cur.execute(info_insert, ['vehicle', vehicle_type])
                cur.execute(info_insert, ['fuel_level', fuel_level])
            con.commit()

            # Build the output
            output = {
                'team_id': team_id,
                'team_name': team_name,
                'easter_egg': False
            }
            if vehicle is not None:
                output['easter_egg'] = True
                output['vehicle'] = vehicle_type
                output['message'] = message
            return output
        except Exception as exc:
            return {
                "error": True,
                "error_message": str(exc)
            }, 400

api.add_resource(TeamList, '/team')

class TeamResource(Resource):
    def get(self, team_id):
        return get_team(team_id).output_status_dict()

    def put(self, team_id):
        # (this is the chase.py replacement)
        # OUTPUT: team.output_status_dict() combined with messages
        try:
            pin = request.form['pin']
            speed = float(request.form['speed'])
            try:
                direction = float(request.form['direction'])
            except:
                direction = 0
            refuel = bool(request.form['refuel'])

            team = get_team(team_id)
            message_list = []

            if team.status['pin'] != pin:
                return {"error": True, "error_message": "invalid pin"}, 403

            # Sanitize input values
            if team.cannot_refuel:
                refuel = False

            if refuel or speed <= 0 or team.stopped or team.fuel_level <= 0:
                speed = 0
                direction = 0

            if speed > team.current_max_speed:
                speed = team.current_max_speed

            # Movement Updates
            current_time = datetime.now(tz=pytz.UTC)
            try:
                diff_time = (current_time - team.last_update_time).total_seconds()
            except:
                # If this gets messed up, default to usual ping
                diff_time = 10
            distance = speed * config.speed_factor * diff_time / 3600
            team.latitude, team.longitude = move_lat_lon(team.latitude, team.longitude, distance, direction)
            team.speed = speed
            team.direction = direction

            # Gas management
            if refuel:
                if team.fuel_level <= 0:
                    team.balance -= config.aaa_fee
                    message_list.append(
                        "You have been charged " + money_format(config.aaa_fee) + " to get someone "
                        "to fill your vehicle up."
                    )
                fuel_amt = min(diff_time * config.fill_rate,
                            team.vehicle.fuel_cap - team.fuel_level)
                team.fuel_level += fuel_amt
                team.balance -= fuel_amt * config.gas_price
                done_refueling = (team.fuel_level >= team.vehicle.fuel_cap - .01)
            else:
                fuel_amt = distance / team.vehicle.calculate_mpg(speed)
                team.fuel_level -= fuel_amt * config.get_config_value("fuel_factor")
                if team.fuel_level < 0:
                    team.fuel_level = 0
                    message_list.append(datetime.now(tz=pytz.UTC).strftime('%H%MZ') +
                                        ': You are running on fumes! Better call for help.')

            # Current hazard/hazard expiry
            if (
                team.active_hazard is not None
                and team.active_hazard.expiry_time <= datetime.now(tz=pytz.UTC)
            ):
                message_list.append(team.active_hazard.generate_expiry_message())
                team.clear_active_hazard()

            # Check queue for action items (either instant action or a hazard to queue)
            queued_hazard = None
            if team.has_action_queue_items:
                for action in team.get_action_queue(hazard_registry):
                    if not action.is_hazard:
                        if action.is_adjustment:
                            team.apply_action(action)
                        message_list.append(action.generate_message())
                        team.dismiss_action(action)
                    elif action.is_hazard and queued_hazard is None:
                        queued_hazard = action

            # If no hazard queued, shuffle in a chance of a random hazard
            if queued_hazard is None:
                queued_hazard = shuffle_new_hazard(team, diff_time, hazard_registry, config)

            # Apply the queued hazard if it overrides a current hazard (otherwise ignore)
            if (
                queued_hazard is not None
                and (team.active_hazard is None or team.active_hazard.overridden_by(queued_hazard))
            ):
                team.apply_hazard(queued_hazard)  # actually make it take effect
                message_list.append(queued_hazard.generate_message())
                team.dismiss_action(queued_hazard)  # in case it was from DB

            team.write_status()

            output = team.output_status_dict()
            output['messages'] = message_list

            return output
        except Exception as exc:
            return {"error": True, "error_message": str(exc), "traceback": traceback.format_exc()}, 500

api.add_resource(TeamResource, '/team/<team_id>')

class TeamLocation(Resource):
    def get(self, team_id):
        team = get_team(team_id)
        return {
            "lat": team.latitude,
            "lon": team.longitude
        }

    def put(self, team_id):
        team = get_team(team_id)

        if 'pin' in request.form and team.status['pin'] != request.form['pin']:
            return {"error": True, "error_message": "invalid pin"}, 403
        elif 'auth' in request.form and config.get_config_value('auth') != request.form['auth']:
            return {"error": True, "error_message": "invalid auth"}, 403
        elif 'pin' not in request.form and 'auth' not in request.form:
            return {"error": True, "error_message": "need authorization"}, 403

        team.latitude = float(request.form['lat'])
        team.longitude = float(request.form['lon'])
        team.speed = 0
        team.direction = 0

        team.write_status()

        return {
            "success": True,
            "lat": team.latitude,
            "lon": team.longitude
        }

api.add_resource(TeamLocation, '/team/<team_id>/location')

class TeamVehicle(Resource):
    def get(self, team_id):
        team = get_team(team_id)
        return vehicle_stats(team.vehicle)

    def put(self, team_id):
        team = get_team(team_id)

        if 'pin' in request.form and team.status['pin'] != request.form['pin']:
            return {"error": True, "error_message": "invalid pin"}, 403
        elif 'auth' in request.form and config.get_config_value('auth') != request.form['auth']:
            return {"error": True, "error_message": "invalid auth"}, 403
        elif 'pin' not in request.form and 'auth' not in request.form:
            return {"error": True, "error_message": "need authorization"}, 403
        
        team.status["vehicle"] = request.form['vehicle_type']

        # Handle vehicle-specific setup
        vehicle = Vehicle(team.status["vehicle"], config)
        fuel_level = (1 + np.random.random()) * 0.5 * vehicle.fuel_cap
        team.fuel_level = fuel_level

        team.write_status()

        return {
            "success": True,
            "vehicle": vehicle_stats(get_vehicle(request.form['vehicle_type']))
        }

api.add_resource(TeamVehicle, '/team/<team_id>/vehicle')

class TeamPoints(Resource):
    def get(self, team_id):
        team = get_team(team_id)
        return {
            "points": team.points
        }

    def put(self, team_id):
        team = get_team(team_id)

        if 'pin' in request.form and team.status['pin'] != request.form['pin']:
            return {"error": True, "error_message": "invalid pin"}, 403
        elif 'auth' in request.form and config.get_config_value('auth') != request.form['auth']:
            return {"error": True, "error_message": "invalid auth"}, 403
        elif 'pin' not in request.form and 'auth' not in request.form:
            return {"error": True, "error_message": "need authorization"}, 403

        team.points += int(request.form['points'])

        team.write_status()

        return {
            "success": True,
            "points": team.points
        }

api.add_resource(TeamPoints, '/team/<team_id>/points')

class TeamBalance(Resource):
    def get(self, team_id):
        team = get_team(team_id)
        return {
            "balance": team.balance,
            "money_formatted": money_format(team.balance)
        }

    def put(self, team_id):
        team = get_team(team_id)

        if 'pin' in request.form and team.status['pin'] != request.form['pin']:
            return {"error": True, "error_message": "invalid pin"}, 403
        elif 'auth' in request.form and config.get_config_value('auth') != request.form['auth']:
            return {"error": True, "error_message": "invalid auth"}, 403
        elif 'pin' not in request.form and 'auth' not in request.form:
            return {"error": True, "error_message": "need authorization"}, 403

        team.balance += float(request.form['balance'])

        team.write_status()

        return {
            "success": True,
            "balance": team.balance,
            "money_formatted": money_format(team.balance)
        }

api.add_resource(TeamBalance, '/team/<team_id>/balance')

class TeamVerify(Resource):
    def put(self, team_id):
        team = get_team(team_id)

        if team.status['pin'] != request.form['pin']:
            return {"error": True, "error_message": "invalid pin"}, 403
        
        if team.vehicle is None:
            return {
                "team_name": team.name,
                "needs_setup": True,
                "setup_step": "vehicle-selection"
            }
        elif team.latitude is None:
            return {
                "team_name": team.name,
                "needs_setup": True,
                "setup_step": "location-selection"
            }
        else:
            return {
                "team_name": team.name,
                "needs_setup": False,
                "setup_step": ""
            }

api.add_resource(TeamVerify, '/team/<team_id>/verify')

##############
# Placefiles #
##############

class PlacefileLsrContent(Resource):
    def get(self):
        url = lsr_asset_url
        output = "\n\n"
        output += "RefreshSeconds: 5\n"
        output += "Threshold: 999\n"
        output += "Title: Live Storm Reports (LSRs)\n"
        output += 'Font: 1, 11, 0, "Courier New"\n'
        output += f'IconFile: 1, 25, 25, 11, 11, "{url}Lsr_FunnelCloud_Icon.png"\n'
        output += f'IconFile: 2, 25, 32, 11, 11, "{url}Lsr_Hail_Icons.png"\n'
        output += f'IconFile: 3, 25, 25, 11, 11, "{url}Lsr_Tornado_Icon.png"\n'
        output += f'IconFile: 4, 25, 25, 11, 11, "{url}Lsr_TstmWndDmg_Icon.png"\n\n'

        hours_valid = config.lsr_hours_valid  # LSR Validity (archive time)
        remark_wrap_length = int(config.get_config_value("lsr_remark_wrap_length"))  # Text Wrapping

        try:
            lsr_con = sql.connect(lsr_db_file)
            lsr_cur = lsr_con.cursor()
            
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
                output += gr_lsr_placefile_entry_from_tuple(
                    lsr_tuple,
                    wrap_length=remark_wrap_length,
                    tz=pytz.timezone(config.get_config_value("pytz_timezone"))
                ) + '\n'
        except:
            # Just have the header matter if errors
            pass
        
        response = make_response(output)
        response.headers['content-type'] = 'text/plain'
        return response

api.add_resource(PlacefileLsrContent, '/placefile/lsr/content')

class PlacefileLsrLoad(Resource):
    def post(self):
        if config.get_config_value('auth') != request.form['auth']:
            return {"error": True, "error_message": "invalid auth"}, 403

        endpoint_args = {
            'start': request.form['start'],
            'end': request.form['end'],
            'wfos': request.form['wfos']
        }
        lsr_endpoint = (
            "http://mesonet.agron.iastate.edu/geojson/lsr.php"
            + "?sts={start}&ets={end}&wfos={wfos}".format(**endpoint_args)
        )

        lsr_request = requests.get(lsr_endpoint)
        lsrs = lsr_request.json()["features"]

        lsr_con = sql.connect(lsr_db_file)
        lsr_cur = lsr_con.cursor()
        lsr_cur.execute(
            "CREATE TABLE lsrs_raw (city char, county char, lat decimal, "
            + "lon decimal,magnitude char, remark char, source char, st char, "
            + "type char, typetext char, valid datetime, wfo char)"
        )
        lsr_con.commit()

        # Save the data
        print("Loading into local database...")

        query = (
            "INSERT INTO lsrs_raw (city, county, lat, lon, magnitude, remark, "
            + "source, st, type, typetext, valid, wfo) VALUES "
            + "(?,?,?,?,?,?,?,?,?,?,?,?)"
        )
        for lsr_row in lsrs:
            lsr = lsr_row["properties"]
            if type_to_icon(lsr["type"]):
                lsr_cur.execute(
                    query,
                    [
                        lsr["city"],
                        lsr["county"],
                        lsr["lat"],
                        lsr["lon"],
                        lsr["magnitude"],
                        lsr["remark"],
                        lsr["source"],
                        lsr["st"],
                        lsr["type"],
                        lsr["typetext"],
                        lsr["valid"],
                        lsr["wfo"],
                    ],
                )
        lsr_con.commit()

        return {"count": len(lsrs)}

api.add_resource(PlacefileLsrLoad, '/placefile/lsr/load')

class PlacefileAllTeamsCurrentContent(Resource):
    def get(self):
        
        output = file_headertext("All Teams", preface="Current ")

        for team_id in list_current_teams():

            try:
                team = get_team(team_id)
            except:
                continue

            if team.latitude is not None and team.speed is not None:
                output += f"Object: {team.latitude:.4f},{team.longitude:.4f}\n"
                if team.speed > 0:
                    output += f"Icon: 0,0,{team.direction:3d},2,15,\n"
                    direction = team.direction
                    heading_row = f"Heading: {direction_angle_to_str(team.direction)}\\n"
                else:
                    direction = 0
                    heading_row = ""
                if team.status_color is None:
                    color_code = 2
                else:
                    color_code = {"green": 2, "yellow": 6, "red": 10}[team.status_color]
                output += (
                    f'Icon: 0,0,{direction:3d},6,{color_code}, "Team: {team.name}\\n'
                    f'{team.last_update.strftime("%Y-%m-%d %H:%M:%S")} UTC\\n'
                    f'Car type: {team.vehicle.print_name}\\n'
                    f'Speed: {team.speed:.1f} mph\\n{heading_row}'
                    f'Fuel Remaining: {team.fuel_level:.2f} gallons\\n'
                    f'{team.status_text}"'
                )
                output += file_footerend()
                output += "\n\n"

        response = make_response(output)
        response.headers['content-type'] = 'text/plain'
        return response

api.add_resource(PlacefileAllTeamsCurrentContent, '/placefile/team/current/content')

class PlacefileAllTeamsTracksContent(Resource):
    def get(self):

        output = file_headertext("All Teams", preface="Tracked ")

        for team_id in list_current_teams():
            try:
                team = get_team(team_id)
            except:
                continue

            try: 
                team.cur.execute(
                    "SELECT cur_timestamp, latitude, longitude, speed, direction, status_color, "
                    "status_text, fuel_level"
                    "FROM team_history ORDER BY cur_timestamp DESC LIMIT 10"
                )
                history_rows = team.cur.fetchall()
            except:
                history_rows = []
            for i, row in enumerate(history_rows):
                start_time = row[0]
                if i == len(history_rows) - 1:
                    end_time = (datetime.now(tz=pytz.UTC) + timedelta(seconds=30)).strftime(std_fmt)
                    arrow_icon = f"Icon: 0,0,{row[4]:3d},2,15,\n"
                else:
                    end_time = history_rows[i + 1][0]
                    arrow_icon = ""
                output += f"Object: {row[1]:.4f},{row[2]:.4f}\n"
                if row[3] > 0:
                    output += arrow_icon
                    direction = row[4]
                    heading_row = f"Heading: {direction_angle_to_str(row[4])}\\n"
                else:
                    direction = 0
                    heading_row = ""
                if row[5] is None:
                    color_code = 2
                else:
                    color_code = {"green": 2, "yellow": 6, "red": 10}[row[5]]
                if arrow_icon:
                    output += (
                        f'Icon: 0,0,{direction:3d},6,{color_code}, "Team: {team.name}\\n'
                        f'{start_time}\\n'
                        f'Car type: {team.vehicle.print_name}\\n'
                        f'Speed: {row[3]:.1f} mph\\n{heading_row}'
                        f'Fuel Remaining: {row[7]:.2f} gallons\\n'
                        f'{row[6]}"'
                    )
                else:
                    output += f'Icon: 0,0,{direction:3d},6,{color_code},\n'
                output += file_footertext(team.name)
                output += '\n\n'

        response = make_response(output)
        response.headers['content-type'] = 'text/plain'
        return response

api.add_resource(PlacefileAllTeamsTracksContent, '/placefile/team/tracks/content')

class PlacefileAllTeamsHistoryContent(Resource):
    def get(self):
        output = file_headertext("All Teams", preface="History of ")

        for team_id in list_current_teams():

            try:
                team = get_team(team_id)
            except:
                continue

            try:
                team.cur.execute(
                    "SELECT cur_timestamp, latitude, longitude, speed, direction, status_color, "
                    "status_text, fuel_level"
                    "FROM team_history ORDER BY cur_timestamp"
                )
                history_rows = team.cur.fetchall()
            except:
                history_rows = []
            for i, row in enumerate(history_rows):
                start_time = row[0]
                if i == len(history_rows) - 1:
                    end_time = (datetime.now(tz=pytz.UTC) + timedelta(seconds=30)).strftime(std_fmt)
                else:
                    end_time = history_rows[i + 1][0]
                output += f"TimeRange: {start_time} {end_time}\n"
                output += f"Object: {row[1]:.4f},{row[2]:.4f}\n"
                if row[3] > 0:
                    output += f"Icon: 0,0,{row[4]:3d},2,15,\n"
                    direction = row[4]
                    heading_row = f"Heading: {direction_angle_to_str(row[4])}\\n"
                else:
                    direction = 0
                    heading_row = ""
                try:
                    color_code = {"green": 2, "yellow": 6, "red": 10}[row[5]]
                except:
                    color_code = 2
                output += (
                    f'Icon: 0,0,{direction:3d},6,{color_code}, "Team: {team.name}\\n'
                    f'{start_time}\\n'
                    f'Car type: {team.vehicle.print_name}\\n'
                    f'Speed: {row[3]:.1f} mph\\n{heading_row}'
                    f'Fuel Remaining: {row[7]:.2f} gallons\\n'
                    f'{row[6]}"'
                )
                output += file_footertext(team.name)
                output += '\n\n'
        
        response = make_response(output)
        response.headers['content-type'] = 'text/plain'
        return response

api.add_resource(PlacefileAllTeamsHistoryContent, '/placefile/team/history/content')

class PlacefileSingleTeamCurrentContent(Resource):
    def get(self, team_id):
        if team_id in list_current_teams():
            team = get_team(team_id)
        else:
            return "", 404

        output = file_headertext(team.name, preface="Current ")
        
        if team.latitude is not None and team.speed is not None:
            output += f"Object: {team.latitude:.4f},{team.longitude:.4f}\n"
            if team.speed > 0:
                output += f"Icon: 0,0,{team.direction:3d},2,15,\n"
                direction = team.direction
                heading_row = f"Heading: {direction_angle_to_str(team.direction)}\\n"
            else:
                direction = 0
                heading_row = ""
            if team.status_color is None:
                color_code = 2
            else:
                color_code = {"green": 2, "yellow": 6, "red": 10}[team.status_color]
            output += (
                f'Icon: 0,0,{direction:3d},6,{color_code}, "Team: {team.name}\\n'
                f'{team.last_update.strftime("%Y-%m-%d %H:%M:%S")} UTC\\n'
                f'Car type: {team.vehicle.print_name}\\n'
                f'Speed: {team.speed:.1f} mph\\n{heading_row}'
                f'Fuel Remaining: {team.fuel_level:.2f} gallons\\n'
                f'{team.status_text}"'
            )
            output += file_footertext(team.name)

        response = make_response(output)
        response.headers['content-type'] = 'text/plain'
        return response

api.add_resource(PlacefileSingleTeamCurrentContent, '/placefile/team/<team_id>/current/content')

class PlacefileSingleTeamTracksContent(Resource):
    def get(self, team_id):
        if team_id in list_current_teams():
            team = get_team(team_id)
        else:
            return "", 404

        output = file_headertext(team.name, preface="Tracked ")

        try:
            team.cur.execute(
                "SELECT cur_timestamp, latitude, longitude, speed, direction, status_color, "
                "status_text, fuel_level"
                "FROM team_history ORDER BY cur_timestamp DESC LIMIT 10"
            )
            history_rows = team.cur.fetchall()
        except:
            history_rows = []
        
        for i, row in enumerate(history_rows):
            start_time = row[0]
            if i == len(history_rows) - 1:
                end_time = (datetime.now(tz=pytz.UTC) + timedelta(seconds=30)).strftime(std_fmt)
                arrow_icon = f"Icon: 0,0,{row[4]:3d},2,15,\n"
            else:
                end_time = history_rows[i + 1][0]
                arrow_icon = ""
            output += f"Object: {row[1]:.4f},{row[2]:.4f}\n"
            if row[3] > 0:
                output += arrow_icon
                direction = row[4]
                heading_row = f"Heading: {direction_angle_to_str(row[4])}\\n"
            else:
                direction = 0
                heading_row = ""
            if row[5] is None:
                color_code = 2
            else:
                color_code = {"green": 2, "yellow": 6, "red": 10}[row[5]]
            if arrow_icon:
                output += (
                    f'Icon: 0,0,{direction:3d},6,{color_code}, "Team: {team.name}\\n'
                    f'{start_time}\\n'
                    f'Car type: {team.vehicle.print_name}\\n'
                    f'Speed: {row[3]:.1f} mph\\n{heading_row}'
                    f'Fuel Remaining: {row[7]:.2f} gallons\\n'
                    f'{row[6]}"'
                )
            else:
                output += f'Icon: 0,0,{direction:3d},6,{color_code},\n'
            output += file_footertext(team.name)
            output += '\n\n'

        response = make_response(output)
        response.headers['content-type'] = 'text/plain'
        return response

api.add_resource(PlacefileSingleTeamTracksContent, '/placefile/team/<team_id>/tracks/content')

class PlacefileSingleTeamHistoryContent(Resource):
    def get(self, team_id):
        if team_id in list_current_teams():
            team = get_team(team_id)
        else:
            return "", 404

        output = file_headertext(team.name, preface="History of ")

        try:
            team.cur.execute(
                "SELECT cur_timestamp, latitude, longitude, speed, direction, status_color, "
                "status_text, fuel_level"
                "FROM team_history ORDER BY cur_timestamp"
            )
            history_rows = team.cur.fetchall()
        except:
            history_rows = []
        for i, row in enumerate(history_rows):
            start_time = row[0]
            if i == len(history_rows) - 1:
                end_time = (datetime.now(tz=pytz.UTC) + timedelta(seconds=30)).strftime(std_fmt)
            else:
                end_time = history_rows[i + 1][0]
            output += f"TimeRange: {start_time} {end_time}\n"
            output += f"Object: {row[1]:.4f},{row[2]:.4f}\n"
            if row[3] > 0:
                output += f"Icon: 0,0,{row[4]:3d},2,15,\n"
                direction = row[4]
                heading_row = f"Heading: {direction_angle_to_str(row[4])}\\n"
            else:
                direction = 0
                heading_row = ""
            if row[5] is None:
                color_code = 2
            else:
                color_code = {"green": 2, "yellow": 6, "red": 10}[row[5]]
            output += (
                f'Icon: 0,0,{direction:3d},6,{color_code}, "Team: {team.name}\\n'
                f'{start_time}\\n'
                f'Car type: {team.vehicle.print_name}\\n'
                f'Speed: {row[3]:.1f} mph\\n{heading_row}'
                f'Fuel Remaining: {row[7]:.2f} gallons\\n'
                f'{row[6]}"'
            )
            output += file_footertext(team.name)
            output += '\n\n'

        response = make_response(output)
        response.headers['content-type'] = 'text/plain'
        return response

api.add_resource(PlacefileSingleTeamHistoryContent, '/placefile/team/<team_id>/history/content')

############
# Vehicles #
############

class VehicleList(Resource):
    def get(self):
        config.cur.execute("SELECT vehicle_type FROM vehicles WHERE shown_in_list = 1")
        return {'vehicles': [
            vehicle_stats(get_vehicle(r[0])) for r in config.cur.fetchall()
        ]}

api.add_resource(VehicleList, '/vehicle')

class VehicleResource(Resource):
    def get(self, vehicle_id):
        return vehicle_stats(get_vehicle(vehicle_id))

api.add_resource(VehicleResource, '/vehicle/<vehicle_id>')

#########
# Admin #
#########

class SimTimings(Resource):
    def get(self):
        return {field: config.get_config_value(field) for field in (
            "simulation_running",
            "arc_start_time",
            "cur_start_time",
            "speed_factor"
        )}

    def put(self):
        if config.get_config_value('auth') != request.form['auth']:
            return {"error": True, "error_message": "invalid auth"}, 403

        for allowed_field in ('simulation_running', 'arc_start_time', 'cur_start_time', 'speed_factor'):
            if allowed_field in request.form:
                config.cur.execute(
                    "UPDATE config SET config_value = ? WHERE config_setting = ?",
                    [request.form[allowed_field], allowed_field]
                )
                config.con.commit()
        return {"success": True}

api.add_resource(SimTimings, '/simulation/timings')

class SimRunning(Resource):
    def get(self):
        running = int(config.get_config_value("simulation_running"))

        if running:
            return {"running": 1}
        else:
            return {"running": 0}

api.add_resource(SimRunning, '/simulation/running')

class SimConfig(Resource):
    def put(self):
        if config.get_config_value('auth') != request.form['auth']:
            return {"error": True, "error_message": "invalid auth"}, 403

        updated = []
        for allowed_field in (
            'simulation_running',
            'gas_price',
            'fill_rate',
            'min_town_distance_search',
            'min_town_distance_refuel',
            'min_town_population',
            'speed_limit',
            'lsr_hours_valid',
            'aaa_fee'
        ):
            if allowed_field in request.form:
                config.cur.execute(
                    "UPDATE config SET config_value = ? WHERE config_setting = ?",
                    [request.form[allowed_field], allowed_field]
                )
                config.con.commit()
                updated.append(allowed_field)
        return {"success": True, "updated": updated}

api.add_resource(SimConfig, '/simulation/config')

class SimHazardConfig(Resource):
    def put(self):
        if config.get_config_value('auth') != request.form['auth']:
            return {"error": True, "error_message": "invalid auth"}, 403

        updated = []
        for allowed_field in (
            'active_hazards',
            'speeding_max_chance',
            'speeding_ticket_amt',
            'dirt_road_prob',
            'cc_prob',
            'flat_tire_prob',
            'pay_for_flat_prob',
            'pay_for_flat_amt',
            'dead_end_prob',
            'flooded_road_prob'
        ):
            if allowed_field in request.form:
                config.cur.execute(
                    "UPDATE hazard_config SET hazard_value = ? WHERE hazard_setting = ?",
                    [request.form[allowed_field], allowed_field]
                )
                config.con.commit()
                updated.append(allowed_field)
        return {"success": True, "updated": updated}

api.add_resource(SimHazardConfig, '/simulation/hazard_config')

class TestResource(Resource):
    def get(self):
        return {"test": True, "time": datetime.now().strftime(std_fmt)}

api.add_resource(TestResource, '/test')

##########################

if __name__ == '__main__':
    app.run(debug=True)
