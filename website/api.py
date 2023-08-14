from flask_pymongo import PyMongo
from flask import Blueprint, render_template, request, Response, jsonify
import os
from .database import db
from .cache import cache
import math as Math

api = Blueprint('api', __name__)

@api.route('/get_content', methods=['GET'])
def get_content():
    total_fish = cache.get('total_fish')
    if total_fish is None:
        total_fish = 0
        # get total count of total_caught in every location
        for location in db.fishing_locations.find():
            total_fish += location['total_caught']
        cache.set('total_fish', total_fish, timeout=3600)
    width = request.args.get('width')
    if width is None:
        return Response(status=400)
    
    fish_dict = cache.get('fish_dict')
    if fish_dict is None:
        fish_info = db.fish_info.find()
        # sort fish_info by name
        fish_info.sort('name', 1)

        # split fish_info into dictionary of fish names based on first letter
        fish_dict = {}
        i = 0
        for fish in fish_info:
            if i == 0:
                latest_fish_name = fish['name']
            if fish['name'][0] not in fish_dict:
                fish_dict[fish['name'][0]] = []
            if fish['name'] != latest_fish_name or i == 0:
                fish_dict[fish['name'][0]].append(fish)
                latest_fish_name = fish['name']
            i += 1

        cache.set('fish_dict', fish_dict, timeout=3600)

    fishing_locations = db.fishing_locations.distinct('location')
    fishing_locations.sort()
    
    if int(width) < 768:
        return jsonify(render_template('mobile_content.html', fish_dict=fish_dict, fishing_locations=fishing_locations, total_fish=total_fish))
    else:
        return jsonify(render_template('desktop_content.html', fish_dict=fish_dict, fishing_locations=fishing_locations, total_fish=total_fish))

@api.route('/get_fish_info', methods=['GET'])
def get_fish_info():
    fish_dict = cache.get('fish_dict')
    if fish_dict is None:
        fish_info = db.fish_info.find()

        # split fish_info into dictionary of fish names based on first letter
        fish_dict = {}
        i = 0
        for fish in fish_info:
            if i == 0:
                latest_fish_name = fish['name']
            if fish['name'][0] not in fish_dict:
                fish_dict[fish['name'][0]] = []
            if fish['name'] != latest_fish_name or i == 0:
                fish_dict[fish['name'][0]].append(fish)
                latest_fish_name = fish['name']
            i += 1
        
        cache.set('fish_dict', fish_dict, timeout=3600)

    fish_name = request.args.get('fish_name')
    if fish_name is None:
        return Response(status=400)
    
    fish_times = []
    fish_entries = db.fish_info.find({'name': fish_name})
    f = fish_entries[0]
    fish_location = f['locations']
    fish_bait = f['bait']
    entry_percents = {}
    for entry in fish_entries:
        time = entry['time_of_day']
        location_time_bait = db.fishing_locations.find_one({'location': fish_location, 'time_of_day': time, 'bait': fish_bait})
        if location_time_bait['total_caught'] != 0:
            entry_percent = Math.floor(entry['num_caught'] / location_time_bait['total_caught'] * 100)
        else:
            entry_percent = 0
        entry_percents[entry['time_of_day']] = entry_percent
        fish_times.append(entry)

    return jsonify(render_template('fish_info.html', fish=f, fish_times=fish_times, entry_percents=entry_percents))

# @api.route('/get_location_info', methods=['GET'])
# def get_location_info():
#     location = request.args.get('location_name')
#     if location is None:
#         return Response(status=400)
    
#     location_info = db.fishing_locations.find({'location': location})
#     location_fish_info = {}
#     for entry in location_info:
#         fish_names = []
#         fish_percents = []
#         location_name = entry['location']
#         time_of_day = entry['time_of_day']
#         bait = entry['bait']

#         # check cache for location, time of day, and bait
#         if entry['total_caught'] >= 30:
#             fish_query = cache.get(location_name + time_of_day + bait)
#             if fish_query is None:
#                 fish_query = db.fish_info.find({'locations': location_name, 'time_of_day': time_of_day, 'bait': bait})
#                 # convert cursor to list to store in cache
#                 fish_query = list(fish_query)
#                 cache.set(location_name + time_of_day + bait, fish_query, timeout=3600)
#         else:
#             fish_query = db.fish_info.find({'locations': location_name, 'time_of_day': time_of_day, 'bait': bait})

#         for fish in fish_query:
#             fish_names.append(fish['name'])
#             if entry['total_caught'] != 0:
#                 fish_percents.append(round(fish['num_caught'] / entry['total_caught'] * 100, 2))
#         bait = entry['bait']
#         location_fish_info[entry['time_of_day'] + ' - ' + bait] = {'fish_names': fish_names, 'fish_percents': fish_percents, 'total_caught': entry['total_caught'], 'time_of_day': entry['time_of_day'], 'bait': bait, 'location': entry['location']}

#     return jsonify(render_template('location_info_new.html', location_info=location_fish_info, fish_names=fish_names, location=location))

@api.route('/get_location_info', methods=['GET'])
def get_location_info():
    location = request.args.get('location_name')
    if location is None:
        return Response(status=400)
    
    if location == 'Ponds':
        location = 'Kilima Pond/Bahari Ponds'
    
    location_info = cache.get(location)
    if location_info is None:
        location_info = db.fishing_locations.find({'location': location})
        location_info = list(location_info)
        cache.set(location, location_info, timeout=3600)

    fish_at_location = cache.get(location + '_fish')
    if fish_at_location is None:
        fish_at_location = db.fish_info.find({'locations': location})
        fish_at_location.sort('bait', 1)
        fish_names = []
        for fish in fish_at_location:
            if fish['name'] not in fish_names:
                fish_names.append(fish['name'])
        fish_at_location = list(fish_names)
        cache.set(location + '_fish', fish_at_location, timeout=3600)

    fish_info = cache.get(location + '_fish_info')
    if fish_info is None:
        fish_info = {}
        for fish in fish_at_location:
            fish_query = db.fish_info.find({'name': fish})
            fish_info[fish] = list(fish_query)
        cache.set(location + '_fish_info', fish_info, timeout=3600)
        
    return jsonify(render_template('location_info_new.html', location=location, fish_at_location=fish_at_location, location_info=location_info, fish_info=fish_info))