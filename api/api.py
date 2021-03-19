#!/usr/bin/env python
"""
Main API Control
================

Using Flask-RESTful, this script hosts the resources for the full frontend API
"""

from flask import Flask, request, make_response
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)

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
        return {"hello": "world"}

api.add_resource(TeamList, '/team')

class TeamResource(Resource):
    def get(self, team_id):
        # TODO
        return {"hello": "world"}

    def put(self, team_id):
        # TODO
        # request.form['data']
        return {"hello": "world"}

api.add_resource(TeamResource, '/team/<team_id>')

class TeamLocation(Resource):
    def get(self, team_id):
        # TODO
        return {"hello": "world"}

    def put(self, team_id):
        # TODO
        # request.form['data']
        return {"hello": "world"}

api.add_resource(TeamLocation, '/team/<team_id>/location')

class TeamVehicle(Resource):
    def get(self, team_id):
        # TODO
        return {"hello": "world"}

    def put(self, team_id):
        # TODO
        # request.form['data']
        return {"hello": "world"}

api.add_resource(TeamVehicle, '/team/<team_id>/vehicle')

class TeamPoints(Resource):
    def get(self, team_id):
        # TODO
        return {"hello": "world"}

    def put(self, team_id):
        # TODO
        # request.form['data']
        return {"hello": "world"}

api.add_resource(TeamPoints, '/team/<team_id>/points')

class TeamBalance(Resource):
    def get(self, team_id):
        # TODO
        return {"hello": "world"}

    def put(self, team_id):
        # TODO
        # request.form['data']
        return {"hello": "world"}

api.add_resource(TeamBalance, '/team/<team_id>/balance')

class TeamVerify(Resource):
    def put(self, team_id):
        # TODO
        # request.form['data']
        return {"hello": "world"}

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
        return {"hello": "world"}

api.add_resource(VehicleList, '/vehicle')

class VehicleResource(Resource):
    def get(self, vehicle_id):
        # TODO
        return {"hello": "world"}

api.add_resource(VehicleResource, '/vehicle/<vehicle_id>')

#########
# Admin #
#########

class SimTimings(Resource):
    def get(self):
        # TODO
        return {"hello": "world"}

    def push(self):
        # TODO
        # request.form['data']
        return {"hello": "world"}

api.add_resource(SimTimings, '/simulation/timings')

class SimRunning(Resource):
    def get(self):
        # TODO
        return {"hello": "world"}

api.add_resource(SimRunning, '/simulation/running')

class SimConfig(Resource):
    def get(self):
        # TODO
        return {"hello": "world"}

    def push(self):
        # TODO
        # request.form['data']
        return {"hello": "world"}

api.add_resource(SimConfig, '/simulation/config')

class SimHazardConfig(Resource):
    def get(self):
        # TODO
        return {"hello": "world"}

    def push(self):
        # TODO
        # request.form['data']
        return {"hello": "world"}

api.add_resource(SimHazardConfig, '/simulation/hazard_config')

##########################

if __name__ == '__main__':
    app.run(debug=True)
