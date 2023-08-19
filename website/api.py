from flask_pymongo import PyMongo
from flask import Blueprint, render_template, request, Response, jsonify, current_app
import os
from .database import db
from .cache import cache
import math as Math
# from .webpush_handler import trigger_push_notifications_for_subscriptions

api = Blueprint('api', __name__)

csrf = current_app.extensions['csrf']

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

@api.route('/get_location_info', methods=['GET'])
def get_location_info():
    location = request.args.get('location_name')
    if location is None:
        return Response(status=400)
    if location == 'Ponds':
        location = 'Kilima Pond/Bahari Ponds'
    
    location_info = db.fishing_locations.find({'location': location})
    location_fish_info = {}
    for entry in location_info:
        fish_names = []
        fish_percents = []
        location_name = entry['location']
        time_of_day = entry['time_of_day']
        bait = entry['bait']
        fish_sell_prices = []

        # check cache for location, time of day, and bait
        if entry['total_caught'] >= 30:
            fish_query = cache.get(location_name + time_of_day + bait)
            if fish_query is None:
                fish_query = db.fish_info.find({'locations': location_name, 'time_of_day': time_of_day, 'bait': bait})
                # convert cursor to list to store in cache
                fish_query = list(fish_query)
                cache.set(location_name + time_of_day + bait, fish_query, timeout=3600)
        else:
            fish_query = db.fish_info.find({'locations': location_name, 'time_of_day': time_of_day, 'bait': bait})

        for fish in fish_query:
            if entry['total_caught'] != 0:
                percent_raw = round(fish['num_caught'] / entry['total_caught'], 2)
                percent = round(fish['num_caught'] / entry['total_caught'] * 100)
                fish_percents.append(percent)
                fish_names.append(fish['name'] + ' (' + str(percent) + '%)')
            fish_sell_prices.append(int(fish['sells_for']) * percent_raw)

        sell_average = 0

        if len(fish_sell_prices) != 0:
            sell_average = round(sum(fish_sell_prices))
        bait = entry['bait']
        location_fish_info[entry['time_of_day'] + ' - ' + bait] = {'fish_names': fish_names,
                                                                    'fish_percents': fish_percents,
                                                                    'total_caught': entry['total_caught'],
                                                                    'time_of_day': entry['time_of_day'],
                                                                    'bait': bait,
                                                                    'location': entry['location'],
                                                                    'sell_average': sell_average}

    return jsonify(render_template('location_info.html', location_info=location_fish_info, fish_names=fish_names, location=location))

# for push notifications if/when I implement them
# @api.route('/subscribe', methods=['POST'])
# def create_push_subscription():
#     data = request.get_json()
#     subscription = db.push_subscriptions.find_one({'subscription_json': data['subscription_json']})
#     if subscription is None:
#         db.push_subscriptions.insert_one(data)
#         subscription = db.push_subscriptions.find_one({'subscription_json': data['subscription_json']})
#     return jsonify({
#         'result': {
#             'status': 'success',
#             'subscription_json': subscription['subscription_json']
#         }
#     })

# @api.route('/trigger-push-notifications', methods=['POST'])
# @csrf.exempt
# def trigger_push_notifications():
#     json_data = request.get_json()
#     subscriptions = db.push_subscriptions.find()
#     results = trigger_push_notifications_for_subscriptions(subscriptions, json_data['title'], json_data['body'])
#     return jsonify({
#         'status': 'success',
#         'result': results
#     })

# for personal use. not used in website
# @api.route('/manually_increment_fish', methods=['POST'])
# def manually_increment_fish():
#     data = request.form
#     chosen_fish = data.get('fish')
#     num_caught = data.get('num_caught')
#     chosen_time_of_day = data.get('time')

#     fish_query = db.fish_info.find_one({'name': chosen_fish, 'time_of_day': chosen_time_of_day})

#     if fish_query is None:
#         return Response(status=400)
    
#     location = fish_query['locations']
#     bait = fish_query['bait']
#     location_query = db.fishing_locations.find_one({'location': location, 'bait': bait, 'time_of_day': chosen_time_of_day})

#     if location_query is None:
#         return Response(status=400)
    
#     db.fish_info.update_one({'name': chosen_fish, 'time_of_day': chosen_time_of_day}, {'$inc': {'num_caught': int(num_caught)}})
#     db.fishing_locations.update_one({'location': location, 'bait': bait, 'time_of_day': chosen_time_of_day}, {'$inc': {'total_caught': int(num_caught)}})
#     return Response(status=200)