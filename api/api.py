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
import pytz
from sqlite3 import dbapi2 as sql

from flask import Flask, request, make_response
from flask_restful import Resource, Api
from mesosim.chase.actions import create_hazard_registry, shuffle_new_hazard
from mesosim.chase.team import Team
from mesosim.chase.vehicle import Vehicle
from mesosim.core.config import Config
from mesosim.core.timing import arc_time_from_cur, std_fmt
from mesosim.lsr import scale_raw_lsr_to_cur_time, gr_lsr_placefile_entry_from_tuple


# Constants
app = Flask(__name__)
api = Api(app)

lsr_db_file = "/home/jthielen/lsr.db"
main_db_file = "/home/jthielen/main.db"
team_db_dir = '/home/jthielen/teams/'

lsr_asset_url = 'https://chase.iawx.info/assets/'

#########
# Teams #
#########

class TeamList(Resource):
    def get(self):
        # TODO
        return {"hello": "world"}

    def push(self):
        # TODO
        # request.form['data']
        # team_name, team_id, pin
        return {
            "team_name": "FILLER",
            "team_id": "FILLER"
        }
        """
        or optionally
        {
            "easter_egg": True,
            "team_vehicle": "twister_jeep",
            "message": "We gotta go!",
        }
        """

api.add_resource(TeamList, '/team')

class TeamResource(Resource):
    def get(self, team_id):
        # TODO
        # Just output team.output_status_dict()
        return {"hello": "world"}

    def put(self, team_id):
        # TODO
        # request.form['data']
        # pin, speed, direction, refuel
        # (this is the chase.py replacement)
        # OUTPUT: team.output_status_dict() combined with messages
        return {"hello": "world"}

api.add_resource(TeamResource, '/team/<team_id>')

class TeamLocation(Resource):
    def get(self, team_id):
        # TODO
        return {
            "lat": 42.0,
            "lon": -95.0
        }

    def put(self, team_id):
        # TODO
        # request.form['data']
        # pin, lat, lon
        return {
            "success": True,
            "lat": 42.0,
            "lon": -95.0
        }

api.add_resource(TeamLocation, '/team/<team_id>/location')

class TeamVehicle(Resource):
    def get(self, team_id):
        # TODO
        # Reuse from vehicle below
        return {"hello": "world"}

    def put(self, team_id):
        # TODO
        # request.form['data']
        # pin, vehicle_type
        # OUTPUT: (like output from vehicle list below, under the vehicle field)
        return {"hello": "world"}

api.add_resource(TeamVehicle, '/team/<team_id>/vehicle')

# TODO
# class TeamPoints(Resource):
# api.add_resource(TeamPoints, '/team/<team_id>/points')

# TODO
# class TeamBalance(Resource):
# api.add_resource(TeamBalance, '/team/<team_id>/balance')

class TeamVerify(Resource):
    def put(self, team_id):
        # TODO
        # request.form['data']
        # pin
        return {
            "team_name": "FILLER",
            "needs_setup": False,
            "setup_step": ""
        }

api.add_resource(TeamVerify, '/team/<team_id>/verify')

##############
# Placefiles #
##############

class PlacefileLsrContent(Resource):
    def get(self):
        # TODO
        output = "LSR CONTENT HERE"
        response = make_response(output)
        response.headers['content-type'] = 'text/plain'
        return response

api.add_resource(PlacefileLsrContent, '/placefile/lsr/content')

class PlacefileLsrLoad(Resource):
    def post(self):
        # TODO
        # request.form['data']
        # 'auth', 'start', 'end', 'wfos'
        return {"count": -1}

api.add_resource(PlacefileLsrLoad, '/placefile/lsr/load')

class PlacefileAllTeamsCurrentContent(Resource):
    def get(self):
        # TODO
        output = "LSR CONTENT HERE"
        response = make_response(output)
        response.headers['content-type'] = 'text/plain'
        return response

api.add_resource(PlacefileAllTeamsCurrentContent, '/placefile/team/current/content')

# TODO PlacefileAllTeamsTracksContent

class PlacefileAllTeamsHistoryContent(Resource):
    def get(self):
        # TODO
        output = "LSR CONTENT HERE"
        response = make_response(output)
        response.headers['content-type'] = 'text/plain'
        return response

api.add_resource(PlacefileAllTeamsHistoryContent, '/placefile/team/history/content')

class PlacefileSingleTeamCurrentContent(Resource):
    def get(self, team_id):
        # TODO
        output = "LSR CONTENT HERE"
        response = make_response(output)
        response.headers['content-type'] = 'text/plain'
        return response

api.add_resource(PlacefileSingleTeamCurrentContent, '/placefile/team/<team_id>/current/content')

# TODO PlacefileSingleTeamTracksContent

class PlacefileSingleTeamHistoryContent(Resource):
    def get(self):
        # TODO
        output = "LSR CONTENT HERE"
        response = make_response(output)
        response.headers['content-type'] = 'text/plain'
        return response

api.add_resource(PlacefileSingleTeamHistoryContent, '/placefile/team/<team_id>/history/content')

############
# Vehicles #
############

class VehicleList(Resource):
    def get(self):
        # TODO
        return [
            {
                "vehicle_type": "sedan",
                "print_name": "Sedan",
                "top_speed": 100,
                "mpg": 40,
                "fuel_cap": 12,
                "traction_rating": "C-",
            }
        ]

api.add_resource(VehicleList, '/vehicle')

class VehicleResource(Resource):
    def get(self, vehicle_id):
        # TODO
        # See list above
        return {"hello": "world"}

api.add_resource(VehicleResource, '/vehicle/<vehicle_id>')

#########
# Admin #
#########

class SimTimings(Resource):
    def get(self):
        # TODO
        # See args below
        return {"hello": "world"}

    def put(self):
        # TODO
        # request.form['data']
        # auth, simulation_running, arc_start_time, cur_start_time, speed_factor
        return {"hello": "world"}

api.add_resource(SimTimings, '/simulation/timings')

class SimRunning(Resource):
    def get(self):
        # TODO
        return {
            "running": 1
        }

api.add_resource(SimRunning, '/simulation/running')

class SimConfig(Resource):
    def put(self):
        # TODO
        # request.form['data']
        # auth, simulation_running
        return {"hello": "world"}

api.add_resource(SimConfig, '/simulation/config')

# TODO
# class SimHazardConfig(Resource):
# api.add_resource(SimHazardConfig, '/simulation/hazard_config')

##########################

if __name__ == '__main__':
    app.run(debug=True)
