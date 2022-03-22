import os, math
from pymongo import MongoClient
from bson.objectid import ObjectId
from modules.calculation import requiredNetworkBandwidth, middleMileTechnology, lastMileTechnology
import pandas as pd


class Schools:
    def __init__(self):
        self.cluster = MongoClient(os.environ['3020_DB_uri'], connectTimeoutMS=30000, socketTimeoutMS=None, socketKeepAlive=True, connect=False, maxPoolsize=1)
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
            #"middle_mile_parameters": '',
            #"last_mile_parameters": '',
            "results": results
        }})

        self.cluster.close()


    # updating results for middle- mile
    def selectMiddleMile(self, school_data_dB, parameters):
        
        self.db.update_one({"_id": ObjectId(f'{school_data_dB["_id"]}')}, 
        {'$set': {
            "middle_mile_parameters": parameters
        }})
        
        middle_tech_tco, middle_tech_npv = middleMileTechnology(parameters)
        
        # arrange results data for entry to database      
        results = { 'required_bandwidth' : school_data_dB['results']['required_bandwidth'],
                    'middle_mile_technology_TCO': {'name': f'{middle_tech_tco[0]}', 
                                                   'TCO':  f'{middle_tech_tco[1]}',
                                                   'NPV':  f'{middle_tech_tco[2]}'}, 
                    'middle_mile_technology_NPV': {'name': f'{middle_tech_npv[0]}', 
                                                   'TCO':  f'{middle_tech_npv[1]}',
                                                   'NPV':  f'{middle_tech_npv[2]}'}, 
                    'last_mile_technology_NPV': {'name': '',
                                                 'NPV': ''}
        }

        self.db.update_one({"_id": ObjectId(f'{school_data_dB["_id"]}')}, 
        {'$set': {
            "results": results
        }})

        self.cluster.close()
    
    
    # updating resutls for last- mile
    def selectLastMile(self, school_data_dB, parameters):
        
        self.db.update_one({"_id": ObjectId(f'{school_data_dB["_id"]}')}, 
        {'$set': {
            "last_mile_parameters": parameters
        }})
        
        a = lastMileTechnology(parameters)
        
        # arrange results data for entry to database      
        results = { 'required_bandwidth' : school_data_dB['results']['required_bandwidth'],
                    'middle_mile_technology_TCO': {'name': school_data_dB['results']['middle_mile_technology_TCO']['name'], 
                                                   'TCO':  school_data_dB['results']['middle_mile_technology_TCO']['TCO'],
                                                   'NPV':  school_data_dB['results']['middle_mile_technology_TCO']['NPV']},
                    'middle_mile_technology_NPV': {'name': school_data_dB['results']['middle_mile_technology_NPV']['name'], 
                                                   'TCO':  school_data_dB['results']['middle_mile_technology_NPV']['TCO'],
                                                   'NPV':  school_data_dB['results']['middle_mile_technology_NPV']['NPV']},
                    'last_mile_technology_NPV': {'name': f'{a[0]}',
                                                 'NPV': f'{a[1]}'}
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
    
    
    # retrieve schools in database
    def getSchoolListing(self, school_name={}):
        if school_name: item = self.db.find_one(school_name)
        else: item = list(self.db.find(school_name))
        self.cluster.close()
        return item



def getMiddleMileDefaultParamters(bandwidth): 
    # all values will be user-definable but all assumed should be defined by the user first
    middle_mile_focl = {
        'length' : 20,      # distance between school and local PoP (km) - ASSUMED
        'T_payback' : 5,    # payback period on investment (years) - ASSUMED
        
        'N_CHm_avg': 2,     # average number of cable manholes per km (cable manholes per km) - ASSUMED
        'N_c_avg': 0.5,     # average FOCL section length that needs a cable duct (km) - ASSUMED
        
        # coefficient for ...
        'C_hdd' : 0.01,     # extending FOCL length due to road crossing (horiz. dir. drilling.)
        'C_cd' : 0.1,       # the FOCL sections that need cable ducts
        'C_clm' : 0.9,      # the FOCL sections that need cable laying machine
        'C_focl' : 0.1,     # the FOCL cost with cable laying and unpacking margin
        'C_design' : 0.05,  # the FOCL design cost
        
        # labor cost norms (man-hours/km) for ...
        'T_geod_norm' : 80.18,          # geodetic work along FOCL route
        'T_hdd_norm' : 6837.20,         # road crossings construction by horiz. dir. drilling
        'T_cd_norm' : 2467.48 ,         # cable-duct construction
        'T_CHm_norm' : 754.77,          # cable manhole construction and FOCL installation
        'T_clm_norm' : 451.20,          # FOCL laying by cable laying machine
        'T_c_norm' : 44.2,              # cable coupling installation
        'T_st_norm' : 31.50,            # signalling test
        'T_ts_norm' : 0,                # technical specification design
        'T_sc_norm' : 0,                # design solutions coordination
        'T_maint_focl_norm' : 30.00,    # FOCL maintainance along route
        'T_maint_cd_norm' : 16,         # cable duct mantainance
        
        # cost norms ($TTD/hour) for ...
        'S_geod_norm' : 100,        # geodetic work along FOCL route  - ASSUMED
        'S_1focl' : 3071.44,        ## cost of FOCL materials per km ($TTD/hour)
        'S_1c' : 268.24,            ## cost of one cable coupling ($TTD/unit)
        'S_hdd_norm' : 500,         # road crossings construction by horiz. dir. drilling - ASSUMED
        'S_1cd' : 24787.90,         ## cost of basic materials for cable duct construction per km ($TTD/km)
        'S_1CMh' : 2666.83,         ## cost of basic materials for cable manhole ($TTD/manhole)
        'S_cd_norm' : 2500,         # cable-duct construction - ASSUMED
        'S_CHm_norm' : 500,         # cable manhole construction and FOCL installation - ASSUMED
        'S_clm_norm' : 1000,        # FOCL laying by cable laying machine - ASSUMED
        'S_c_norm' : 500,           # cable coupling installation - ASSUMED
        'S_st_norm' : 250,          # signalling test - ASSUMED
        'S_ts_norm' : 10000,        # technical specification design - ASSUMED
        'S_sc_norm' : 10000,        # design solutions coordination - ASSUMED
        'S_tr_eq' : 1221.75,        ## cost of data transmission equipment for L2 channel
        'S_maint_focl_norm' : 1000, # FOCL maintainance along route - ASSUMED
        'S_maint_cd_norm' : 1000,   # cable duct mantainance - ASSUMED
        
        'In' : 36000000,            # annual potential income from channel operation ($TTD/year) - ASSUMED
        'T_vat' : 15,               # value-added tax rate (%) - ASSUMED
        'S_operation' : 400000,     # cost of annual operation ($TTD/year) - ASSUMED
        'T_prof' : 10,              # corporate tax rate (%) - ASSUMED
        'S_equip_mat' : 500000,     # total cost of equipment, components, and material ($TTD) - ASSUMED
        'T_lt' : 25,                # average lifetime of equipment and materials (years) - ASSUMED
        'K_disc' : 5,               # discount rate (%) - ASSUMED
        's_inv' : 50000000          # total investment costs for access network construction ($TTD) - ASSUMED
    }
    
    middle_mile_mw = {
        'L_rpl' : 20,               # retransmission path length (km)
        'N_rts_term' : 2,           # number of terminal RTS (units) 
        'C_rts' : 2,                # number of RTS devices per repeaters (units)
        'C_afd' : 2,                # number of antenna feeder devices per repeater (units)
        'C_design' : 0.05,          # microwave design cost coefficient
        'S_1rts' : 4517.14,         # internal RTS device subassembly cost ($TTD/device)
        'S_1afd' : 1419.67,         # internal RTS antenna feeder device subassembly cost ($TTD/device)
        'S_1pylon' : 7437.99,       # main material cost for one RTS pylon construction ($TTD/device)

        # cost norms ($TTD/hour) for ...
        'S_geod_rts_norm' : 5000,   # geodetic work at RTS pylon location ($TTD/device) - ASSUMED
        'S_pylon_norm' : 3000,      # per pylon construction of RTS antenna ($TTD/device) - ASSUMED
        'S_afd_norm' : 3000,        # antenna feeder deivce installation and commisioning ($TTD/device) - ASSUMED
        'S_rts_norm' : 3000,        # internal devices installion and commissioning per RTS ($TTD/device) - ASSUMED

        'S_rts_coord_norm' : 0,         # design solutions coordination per RTS construction ($TTD/hour)
        'S_maint_1pylon_norm' : 0,      # typical cost for one RTS pylon maintainance ($TTD/hour)
        'S_maint_afd_norm' : 0,         # typical cost for antenna feeder device maintainance per RTS ($TTD/hour)
        'S_maint_rts_norm' : 0,         # typical cost for internal RTS device maintainance ($TTD/hour)
        'S_spectrum' : 10000,           # spectrum licensing cost for the entire channel ($TTD)
        'S_annual_spectrum_fee' : 1000, # annual spectrum licensing cost for the entire channel ($TTD) - ASSUMED

        # labor cost norms (man-hour/unit) for ...
        'T_geod_norm' : 67,         # geodetic work at RTS pylon location
        'T_pylon_norm' : 87.80,     # pylon construction of RTS antenna
        'T_afd_norm' : 40,          # antenna feeder devices installation and commissioning
        'T_rts_norm' : 40,          # internal RTS devices installtion and commissioning
        'T_coord_norm' : 0,         # design solutions coordination on one RTS construction

        # typical annual labor cost (man-hours/unit) for ...
        'T_maint_pylon_norm' : 2000,    # RTS pylon maintainance - ASSUMED
        'T_maint_afd_norm' : 2000,      # cost for antenna feeder device maintainance - ASSUMED
        'T_maint_rts_norm' : 2000,      # internal RTS device maintainance - ASSUMED
        
        'In' : 36000000,            # annual potential income from channel operation ($TTD/year) - ASSUMED
        'T_vat' : 15,               # value-added tax rate (%) - ASSUMED
        'S_operation' : 300000,     # cost of annual operation ($TTD/year) - ASSUMED
        'T_prof' : 10,              # corporate tax rate (%) - ASSUMED
        'S_equip_mat' : 100000,     # total cost of equipment, components, and material ($TTD) - ASSUMED
        'T_lt' : 25,                # average lifetime of equipment and materials (years) - ASSUMED
        'K_disc' :5 ,               # discord rate (%) - ASSUMED
        's_inv' : 20000000          # total investment costs for access network construction ($TTD) - ASSUMED
    }
    
    middle_mile_sat = {
        'V_chan' : bandwidth,   # required network bandwidth for school (Mbps)
        'V_1user' : 100,        # communication channel capacity per single Internet channel (Mbps)
        'S_1user' : 10000,      # cost of user terminal set ($TTD/unit) - ASSUMED
        'S_mat_1user' : 10000,  # cost of materials and supplied equipment for one terminal set ($TTD/unit) - ASSUMED
        'S_user_typ' : 5000,    # typical cost of installation and configuration of one user terminal set ($TTD/unit) - ASSUMED
        'T_user_typ' : 16,      # labor cost for installation and configuration of one user terminal set (man-hours/unit) - ASSUMED
        'C_user' : 0.4,         # total cost of user terminal equipment and installation materials coefficient
        'C_design' : 0.05,      # satellite design cost coefficient
        'S_rent_1mbit' : 1000,  # annual cost for 1Mbps channel rent ($TTD/Mbps) - ASSUMED
        'S_maint_1user' : 500,  # typical cost for user terminal set maintainance per hour ($TTD/hour) - ASSUMED
        'T_maint_1user' : 16,   # annual labor norms for one user terminal set maintainance (man-hours/unit)
        
        'In' : 36000000,            # annual potential income from channel operation ($TTD/year) - ASSUMED
        'T_vat' : 15,               # value-added tax rate (%) - ASSUMED
        'S_operation' : 600000,     # cost of annual operation ($TTD/year) - ASSUMED
        'T_prof' : 10,              # corporate tax rate (%) - ASSUMED
        'S_equip_mat' : 400000,     # total cost of equipment, components, and material ($TTD) - ASSUMED
        'T_lt' : 25,                # average lifetime of equipment and materials (years) - ASSUMED
        'K_disc' : 5,               # discord rate (%) - ASSUMED
        's_inv' : 20000000          # total investment costs for access network construction ($TTD) - ASSUMED
    }
    
    
    return {'focl': middle_mile_focl,
            'mw': middle_mile_mw,
            'sat': middle_mile_sat}


def getLastMileDefaultParamters(): 
    # all values will be user-definable but all assumed should be defined by the user first
    last_mile_focl = {
        'aoe_units' : 5,
        'teap_units' : 10,
        'length' : 20,
        'equipment' : 1000000,
        'deployment' : 2500000, 
        'operation' : 560000, 
        
        'In' : 26000000,            # annual potential income from channel operation ($TTD/year) - ASSUMED
        'T_vat' : 15,               # value-added tax rate (%) - ASSUMED
        'S_operation' : 600000,     # cost of annual operation ($TTD/year) - ASSUMED
        'T_prof' : 10,              # corporate tax rate (%) - ASSUMED
        'S_equip_mat' : 200000,     # total cost of equipment, components, and material ($TTD) - ASSUMED
        'T_lt' : 25,                # average lifetime of equipment and materials (years) - ASSUMED
        'K_disc' : 5,               # discount rate (%) - ASSUMED
        's_inv' : 20000000          # total investment costs for access network construction ($TTD) - ASSUMED
    }
    
    last_mile_mw = {
        'aoe_units' : 10,
        'teap_units' : 20,
        'length' : 20,
        'equipment' : 5000000,
        'deployment' : 1500000, 
        'operation' : 420000, 
        
        'In' : 36000000,            # annual potential income from channel operation ($TTD/year) - ASSUMED
        'T_vat' : 15,               # value-added tax rate (%) - ASSUMED
        'S_operation' : 300000,     # cost of annual operation ($TTD/year) - ASSUMED
        'T_prof' : 10,              # corporate tax rate (%) - ASSUMED
        'S_equip_mat' : 100000,     # total cost of equipment, components, and material ($TTD) - ASSUMED
        'T_lt' : 25,                # average lifetime of equipment and materials (years) - ASSUMED
        'K_disc' :5 ,               # discord rate (%) - ASSUMED
        's_inv' : 70000000          # total investment costs for access network construction ($TTD) - ASSUMED
    }
    
    last_mile_sat = {
        'aoe_units' : 5,
        'teap_units' : 10,
        'length' : 20,
        'equipment' : 1000000,
        'deployment' : 2500000, 
        'operation' : 560000, 
        
        'In' : 39000000,            # annual potential income from channel operation ($TTD/year) - ASSUMED
        'T_vat' : 15,               # value-added tax rate (%) - ASSUMED
        'S_operation' : 900000,     # cost of annual operation ($TTD/year) - ASSUMED
        'T_prof' : 10,              # corporate tax rate (%) - ASSUMED
        'S_equip_mat' : 600000,     # total cost of equipment, components, and material ($TTD) - ASSUMED
        'T_lt' : 25,                # average lifetime of equipment and materials (years) - ASSUMED
        'K_disc' : 5,               # discord rate (%) - ASSUMED
        's_inv' : 80000000          # total investment costs for access network construction ($TTD) - ASSUMED
    }
    
    last_mile_cell = {
        'aoe_units' : 5,
        'teap_units' : 10,
        'length' : 20,
        'equipment' : 1000000,
        'deployment' : 2500000, 
        'operation' : 560000, 
        
        'In' : 21000000,            # annual potential income from channel operation ($TTD/year) - ASSUMED
        'T_vat' : 15,               # value-added tax rate (%) - ASSUMED
        'S_operation' : 300000,     # cost of annual operation ($TTD/year) - ASSUMED
        'T_prof' : 10,              # corporate tax rate (%) - ASSUMED
        'S_equip_mat' : 200000,     # total cost of equipment, components, and material ($TTD) - ASSUMED
        'T_lt' : 25,                # average lifetime of equipment and materials (years) - ASSUMED
        'K_disc' : 5,               # discord rate (%) - ASSUMED
        's_inv' : 1000000          # total investment costs for access network construction ($TTD) - ASSUMED
    }
    
    
    return {'Fiber Optic Cable': last_mile_focl,
            'Microwave': last_mile_mw,
            'Satellite': last_mile_sat,
            'Cellular': last_mile_cell}



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

