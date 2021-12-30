import os, math
from pymongo import MongoClient
from bson.objectid import ObjectId
from modules.calculation import requiredNetworkBandwidth
import pandas as pd


class Schools:
    def __init__(self):
        self.cluster = MongoClient(os.environ('3020_DB_uri'), connectTimeoutMS=3000, socketTimeoutMS=None, socketKeepAlive=True, connect=False, maxPoolsize=1)
        self.db = self.cluster['ECNG3020']['Schools']

    
    
    def AddtoDB(self, school_form):
        self.db.insert_one(school_form)
        self.cluster.close()

    
    
    def DeletefromDB(self, school_name):
        self.db.delete_one( { "school_name": school_name } )
        self.cluster.close()

    
    
    def EditDB(self, school_data_dB):
        self.db.update_one( { "_id": ObjectId(f'{school_data_dB["_id"]}' ) }, 
        {'$set': {
            "school_name": school_data_dB["school_name"],
            "region": school_data_dB["region"],
            "subregion": school_data_dB["subregion"],
            "longitude": school_data_dB["longitude"],
            "latitude": school_data_dB["latitude"],
            "length": school_data_dB["length"],
            "width": school_data_dB["width"],
            "floors": school_data_dB["floors"],
            "electricity": school_data_dB["electricity"]
        }})
        self.cluster.close()



    # edit user device groups
    def EditUDG(self, school_data_dB):
        bandwidth = 'No user device groups configured'    # this will be used to indicate that no user device groups were mapped
        if school_data_dB["user_device_groups"]: bandwidth = requiredNetworkBandwidth(school_data_dB["user_device_groups"])

        # arrange results data for entry to database
        results = { 'required_bandwidth' : bandwidth,
                    'recommended_technology': '',
                    'projected_cost': ''
        }

        self.db.update_one({"_id": ObjectId(f'{school_data_dB["_id"]}')}, 
        {'$set': {
            "user_device_groups": school_data_dB["user_device_groups"],
            "results": results
        }})

        self.cluster.close()



    # retrieve schools in database
    def getSchoolListing(self, school_name={}):
        if school_name: item = self.db.find_one(school_name)
        else: item = list(self.db.find(school_name))
        self.cluster.close()
        return item




def arrangeSchoolData(post_data):
    if post_data['longlat_type'] == 'dd':
        longitude = float(post_data['long_deg'])
        latitude = float(post_data['lat_deg'])
    
    elif post_data['longlat_type'] == 'ddm':
        longitude = float(post_data['long_deg']) + float(post_data['long_min'])/60
        latitude = float(post_data['lat_deg']) + (float(post_data['lat_min'])/60)

        if post_data['cardinal_long'] == 'W': longitude = -longitude
        if post_data['cardinal_lat'] == 'S': latitude = -latitude

    elif post_data['longlat_type'] == 'dms':
        longitude = float(post_data['long_deg']) + float(post_data['long_min'])/60 + float(post_data['long_sec'])/3600
        latitude = float(post_data['lat_deg']) + float(post_data['lat_min'])/60 + float(post_data['lat_sec'])/3600

        if post_data['cardinal_long'] == 'W': longitude = -longitude
        if post_data['cardinal_lat'] == 'S': latitude = -latitude

    try:
        school_data = {
            '_id': post_data['_id'],
            'school_name': post_data['school_name'],
            'region': post_data['region'],
            'subregion': post_data['subregion'],
            'longitude': longitude,
            'latitude': latitude,
            'length': float(post_data['length']),
            'width': float(post_data['width']),
            'floors': int(post_data['floors']),
            'electricity': post_data['electricity'],
            'available_coverage': findCoverage(latitude, longitude),
            'user_device_groups': [],
            'results': []
        }
    except:
        school_data = {
            'school_name': post_data['school_name'],
            'region': post_data['region'],
            'subregion': post_data['subregion'],
            'longitude': longitude,
            'latitude': latitude,
            'length': float(post_data['length']),
            'width': float(post_data['width']),
            'floors': int(post_data['floors']),
            'electricity': post_data['electricity'],
            'available_coverage': findCoverage(latitude, longitude),
            'user_device_groups': [],
            'results': []
        }

    return school_data


def findCoverage(latitude, longitude):
    df = pd.read_excel('./static/map/Tower_Data.xlsx')
    available_coverage = set()
    for i, row in df.iterrows():
        try:
            tower_latitude = row['Latitude N'].split('-')
            tower_longitude = row['Longitude W'].split('-') 
            
            tower_latitude = float(tower_latitude[0]) + float(tower_latitude[1])/60 + float(tower_latitude[2])/3600
            tower_longitude = -(float(tower_longitude[0]) + float(tower_longitude[1])/60 + float(tower_longitude[2])/3600)
        
            tower_latitude = float("{:.5f}".format(tower_latitude))
            tower_longitude = float("{:.5f}".format(tower_longitude))

            # calculate the distance between the school and the current tower
            distance = getDistanceFromLatLonInKm(latitude, longitude, tower_latitude, tower_longitude)
            #print(distance)
            if distance <= 4.5:
                available_coverage.add('3G')
            if distance <= 2:
                available_coverage.add('4G')

        except:
            print(f'Row {i} format is different')
            continue
    
    return list(available_coverage)


def getDistanceFromLatLonInKm(lat1,lon1,lat2,lon2):
    radius = 6371
    dLat = deg2rad(lat2-lat1)
    dLon = deg2rad(lon2-lon1)
    a = math.sin(dLat/2) * math.sin(dLat/2) + math.cos(deg2rad(lat1)) * math.cos(deg2rad(lat2)) * math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a)); 
    d = radius * c
    return d

def deg2rad(deg): return deg * (math.pi/180)