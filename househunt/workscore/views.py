from django.shortcuts import render
from django.http import HttpResponse
import urllib
import json
import datetime
import pytz

def index(request):
    origin = "288 San Jose Ave, SF"
    destinations = []
    destinations.append(("24th St Mission Station", "2800 Mission St, San Francisco, CA 94110"))
    destinations.append(("16th St Mission Station", "2000 Mission St, San Francisco, CA 94110"))
    destinations.append(("STRATIM", "489 Clementina Street, Floor 2, San Francisco, CA 94103"))
    destinations.append(("mLab", "660 York St, San Francisco, CA 94110"))
    destinations.append(("Twitter", "1355 Market St, San Francisco, CA 94103"))
    destinations.append(("Reddit", "420 Taylor St, San Francisco, CA 94102"))
    walk_data = TravelView(origin, destinations, "walking").get()
    bike_data = TravelView(origin, destinations, "bicycling").get()
    transit_data = TravelView(origin, destinations, "transit").get()
    merged_data = merge_data(walk_data, bike_data, transit_data)
    return render(request, "index.html", context={"data": merged_data})

def merge_data(walk_data, bike_data, transit_data):
    output = {}
    output["origin"] = walk_data["origin"]
    output["destinations"] = []
    for i in range(0, len(walk_data["destinations"])):
        destination = {}
        w_data = walk_data["destinations"][i]
        b_data = bike_data["destinations"][i]
        t_data = transit_data["destinations"][i]
        destination["name"] = w_data["name"]
        destination["address"] = w_data["address"]
        destination["walking"] = {}
        destination["walking"]["distance"] = w_data["distance"]
        destination["walking"]["duration"] = w_data["duration"]
        destination["walking"]["class"] = get_duration_class(w_data["duration_sec"], 15, 25)
        destination["bicycling"] = {}
        destination["bicycling"]["distance"] = b_data["distance"]
        destination["bicycling"]["duration"] = b_data["duration"]
        destination["bicycling"]["class"] = get_duration_class(b_data["duration_sec"], 20, 30)
        destination["transit"] = {}
        destination["transit"]["distance"] = t_data["distance"]
        destination["transit"]["duration"] = t_data["duration"]
        destination["transit"]["class"] = get_duration_class(t_data["duration_sec"], 25, 35)
        output["destinations"].append(destination)
    return output

def get_duration_class(duration_sec, thresh_1, thresh_2):
    minute = duration_sec / 60.0
    if minute <= thresh_1:
        return "time-1"
    elif minute <= thresh_2:
        return "time-2"
    else:
        return "time-3"

class TravelView():

    def __init__(self, origin, destinations, mode):
        self.origin = origin
        self.destinations = destinations
        self.mode = mode

    def get(self):
        url = self.make_request()
        print(url)
        response = urllib.request.urlopen(url)
        data = json.loads(response.read())
        parsed_data = self.parse(data)
        return parsed_data

    def make_request(self):
        params = {"units": "imperial", "origins": self.origin, "destinations": self.encode_destinations(), "mode": self.mode,
                "departure_time": self.next_tuesday_morning(), "key": "AIzaSyBJCmkrZ8oWgl-v-0yOBoFiABrMXDULg2I"}
        request_url = "https://maps.googleapis.com/maps/api/distancematrix/json?{}".format(urllib.parse.urlencode(params))
        return request_url

    def parse(self, data):
        output = {}
        output["origin"] = data["origin_addresses"][0]
        output["destinations"] = []
        addresses = data["destination_addresses"]
        for i in range(0, len(self.destinations)):
            dest = {}
            dest["name"] = self.destinations[i][0]
            dest["address"] = addresses[i]
            dest["distance"] = data["rows"][0]["elements"][i]["distance"]["text"]
            dest["duration"] = data["rows"][0]["elements"][i]["duration"]["text"]
            dest["duration_sec"] = data["rows"][0]["elements"][i]["duration"]["value"]
            output["destinations"].append(dest)
        return output

    def encode_destinations(self):
        addresses = [d[1] for d in self.destinations]
        return "|".join(addresses)

    def next_tuesday_morning(self):
        date = datetime.date.today()
        while date.weekday() != 1:
            date += datetime.timedelta(1)
        time = datetime.datetime(date.year, date.month, date.day, 16, tzinfo=pytz.utc)
        return int(time.strftime('%s'))
