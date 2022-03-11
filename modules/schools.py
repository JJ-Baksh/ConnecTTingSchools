import os, math
from pymongo import MongoClient
from bson.objectid import ObjectId
from modules.calculation import requiredNetworkBandwidth, middleMileTechnology
import pandas as pd


class Schools:
    def __init__(self):
        self.cluster = MongoClient(os.environ['3020_DB_uri'], connectTimeoutMS=30000, socketTimeoutMS=None, socketKeepAlive=True, connect=False, maxPoolsize=1)
        self.db = self.cluster['ECNG3020']['Schools']

    
    
    def AddtoDB(self, school_form):
        self.db.insert_one(school_form)
        self.cluster.close()


    def setDefaultParamters(self):
        database = self.cluster['ECNG3020']['DefaultParamters']
        
        middle_mile_focl = {
            'length' : 20,
            'T_payback' : 5,   # years
            'C_hdd' : 0.01,
            'C_cd' : 0.1,
            'C_clm' : 0.9,
            'C_focl' : 0.1,
            'C_design' : 0.05,
            
            'N_CHm_avg': 2,           # assumed
            'N_c_avg': 0.5,           # assumed
            
            'T_geod_norm' : 80.18,     # units: man-hours/km, value: provided
            'T_hdd_norm' : 6837.20,    # units: man-hours/km, value: provided
            'T_cd_norm' : 2467.48 ,
            'T_CHm_norm' : 754.77,
            'T_clm_norm' : 451.20,
            'T_c_norm' : 44.2,
            'T_st_norm' : 31.50,
            'T_ts_norm' : 0,
            'T_sc_norm' : 0,
            'T_maint_focl_norm' : 30.00,
            'T_maint_cd_norm' : 16,
            
            'S_geod_norm' : 100,       # assumed
            'S_1focl' : 3071.44,       
            'S_1c' : 268.24,           
            'S_hdd_norm' : 500,        # assumed
            'S_1cd' : 24787.90,       
            'S_1CMh' : 2666.83,        
            'S_cd_norm' : 2500,        # assumed
            'S_CHm_norm' : 500,        # assumed
            'S_clm_norm' : 1000,       # assumed
            'S_c_norm' : 500,          # assumed
            'S_st_norm' : 250,         # assumed
            'S_ts_norm' : 10000,       # assumed
            'S_sc_norm' : 10000,       # assumed
            'S_tr_eq' : 1221.75,
            'S_maint_focl_norm' : 1000, # assumed
            'S_maint_cd_norm' : 1000,   # assumed
            
            'In' : 36000000,           # assumed
            'T_vat' : 15,              # assumed
            'S_operation' : 400000,    # assumed
            'T_prof' : 10,             # assumed
            'S_equip_mat' : 500000,    # assumed
            'T_lt' : 25,               # assumed
            'K_disc' : 5,              # assumed
            's_inv' : 50000000        # assumed
        }
        
        middle_mile_mw = {
            'L_rpl' : 20,
            'N_rts_term' : 2,
            'C_rts' : 2,
            'C_afd' : 2,
            'C_design' : 5,
            'S_1rts' : 4517.14,
            'S_1afd' : 1419.67,
            'S_1pylon' : 7437.99,

            'S_geod_rts_norm' : 5000,  # assumed
            'S_pylon_norm' : 3000,     # assumed
            'S_afd_norm' : 3000,       # assumed
            'S_rts_norm' : 3000,       # assumed

            'S_rts_coord_norm' : 0,
            'S_maint_1pylon_norm' : 0,
            'S_maint_afd_norm' : 0,
            'S_maint_rts_norm' : 0,
            'S_spectrum' : 10000,
            'S_annual_spectrum_fee' : 1000,   # assumed

            'T_geod_norm' : 67,
            'T_pylon_norm' : 87.80,
            'T_afd_norm' : 40,
            'T_rts_norm' : 40,
            'T_coord_norm' : 0,
            
            'T_maint_pylon_norm' : 2000,   # assumed
            'T_maint_afd_norm' : 2000,     # assumed
            'T_maint_rts_norm' : 2000,     # assumed
            
            'In' : 36000000,           # assumed
            'T_vat' : 15,              # assumed
            'S_operation' : 300000,    # assumed
            'T_prof' : 10,             # assumed
            'S_equip_mat' : 100000,    # assumed
            'T_lt' : 25,               # assumed
            'K_disc' :5 ,              # assumed
            's_inv' : 20000000        # assumed
        }
        
        middle_mile_sat = {
            'V_chan' : 5.54,
            'V_1user' : 100,
            'S_1user' : 10000 ,      # assumed
            'S_mat_1user' : 10000,   # assumed
            'S_user_typ' : 5000,      # assumed
            'T_user_typ' : 16,         # assumed
            'C_user' : 0.4,
            'C_design' : 5,
            'S_rent_1mbit' : 1000,     # assumed
            'S_maint_1user' : 500,    # assumed
            'T_maint_1user' : 16,
            
            'In' : 36000000,           # assumed
            'T_vat' : 15,              # assumed
            'S_operation' : 600000,    # assumed
            'T_prof' : 10,             # assumed
            'S_equip_mat' : 400000,    # assumed
            'T_lt' : 25,               # assumed
            'K_disc' : 5,              # assumed
            's_inv' : 20000000        # assumed
        }
        
        database.insert_one({'focl': middle_mile_focl,
                            'mw': middle_mile_mw,
                            'sat': middle_mile_sat})
        self.cluster.close()
        
        return {'focl': middle_mile_focl,
                'mw': middle_mile_mw,
                'sat': middle_mile_sat}
    
    
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
        if school_data_dB["user_device_groups"]: 
            bandwidth = requiredNetworkBandwidth(school_data_dB["user_device_groups"])
            

        # arrange results data for entry to database
        results = { 'required_bandwidth' : bandwidth,
                    'middle_mile_technology_TCO': {'name': '', 
                                                   'TCO':  '',
                                                   'NPV':  ''}, 
                    'middle_mile_technology_NPV': {'name': '', 
                                                   'TCO':  '',
                                                   'NPV':  ''}, 
                    'last_mile_technology_NPV': {'name': '',
                                                 'NPV': ''}
        }

        self.db.update_one({"_id": ObjectId(f'{school_data_dB["_id"]}')}, 
        {'$set': {
            "user_device_groups": school_data_dB["user_device_groups"],
            "middle_mile_paramters": '',
            "last_mile_paramters": '',
            "results": results
        }})

        self.cluster.close()


    # updating results for middle- mile
    def updateMiddleMile(self, school_data_dB, parameters):
        
        middle_tech_tco, middle_tech_npv = middleMileTechnology(parameters)
        
        # arrange results data for entry to database
        print(school_data_dB['results']['required_bandwidth'])
        
        results = { 'required_bandwidth' : school_data_dB['results']['required_bandwidth'],
                    'middle_mile_technology_TCO': {'name': f'{middle_tech_tco[0]}', 
                                                   'TCO':  f'${middle_tech_tco[1]} TTD',
                                                   'NPV':  f'${middle_tech_tco[2]} TTD'}, 
                    'middle_mile_technology_NPV': {'name': f'{middle_tech_npv[0]}', 
                                                   'TCO':  f'${middle_tech_npv[1]} TTD',
                                                   'NPV':  f'${middle_tech_npv[2]} TTD'}, 
                    'last_mile_technology_NPV': {'name': '',
                                                 'NPV': ''}
        }

        self.db.update_one({"_id": ObjectId(f'{school_data_dB["_id"]}')}, 
        {'$set': {
            "results": results
        }})

        self.cluster.close()
    
    
    # updating results for middle- mile
    def updateMiddleMileParamters(self, school_data_dB, parameters):
            
            if not school_data_dB['middle_mile_parameters']:
                      
                self.db.update_one({"_id": ObjectId(f'{school_data_dB["_id"]}')}, 
                {'$set': {
                    "middle_mile_parameters": parameters
                }})

                self.cluster.close()
    
    # updating resutls for last- mile
    def updateLastMile():
        pass


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
            'middle_mile_parameters': [],
            'last_mile_parameters': [],
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
            'middle_mile_parameters': [],
            'last_mile_parameters': [],
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

