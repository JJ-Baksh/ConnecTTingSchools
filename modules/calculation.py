import pandas as pd
import math
from math import log10, floor

def round_sig(x, sig=3):
   return round(x, sig-int(floor(log10(abs(x))))-1)

def requiredNetworkBandwidth(user_device_groups):
    # all parameter values are stored in the Excel document
    df = pd.read_excel('./static/services/Profile_Service_Parametes.xlsx')
    
    rb = 0 # initially set the required bandwidth in Mbps
    
    # loop for user device goups
    for group in user_device_groups:
    
        # sub-divide the profile category
        if group['profile'] == 'Basic-': quality, intensity = 'low', 'low'
        elif group['profile'] == 'Basic': quality, intensity = 'low', 'medium'
        elif group['profile'] == 'Basic+': quality, intensity = 'low', 'high'
        elif group['profile'] == 'Intermediate-': quality, intensity = 'medium', 'low'
        elif group['profile'] == 'Intermediate': quality, intensity = 'medium', 'medium'
        elif group['profile'] == 'Intermediate+': quality, intensity = 'medium', 'high'
        elif group['profile'] == 'Advanced-': quality, intensity = 'high', 'low'
        elif group['profile'] == 'Advanced': quality, intensity = 'high', 'medium'
        elif group['profile'] == 'Advanced+': quality, intensity = 'high', 'high'

        # loop for services for specific user device group
        for service in group['services']:
            row = df.loc[df['service'] == service]
        
            # calculate the service session duration for service (j) and user group (i)
            
            Lij = row.iloc[0]['session_data_per_hour_' + intensity]
                # volume of data per session for service (j) and profile of user group (i)
                # taken from the QoS parameters as 'session data per hour' in MB 
                # this is influenced by the intensity profile

            Vj = row.iloc[0]['data_transfer_rate_' + quality]
                # data transfer rate (per session) for service (j)
                # taken from the QoS parameters as 'Transfer (bit) rate' in Mbps 
                # this is influenced by the quality profile

            Tij = 8.38 * Lij / Vj


            # calculate intensity of requests to create a new session for service (j) by user group (i)
            Ci = group['devices']
                # number of users in user device group (i)

            Iij = row.iloc[0]['intensity_per_user_' + intensity]
                # intensity of usage for service (j) by user group (i) in requests per hour
                # taken from the QoS parameters as 'Intensity per user' in requests/hour 
                # this is influenced by the intensity profile

            requests_ij = Ci * Iij


            # calculate expected load for service (j) by user group (i)
            Yij = requests_ij * Tij / 3600


            # calculate no. of simultaneous sessions for service (j) by user group (i)
            Pqg = 0.05
                # QoE degradation probability percentage

            Cij, Pqg_calc = 0, 1
            
            while Pqg_calc > Pqg:
                Cij += 1

                Pqg_calc_numerator = (Yij**Cij)/(math.factorial(Cij))
                
                Pqg_calc_denumerator = 0
                for f in range(1, Cij+1):
                    try: x = math.gamma(((Yij**f)/f)+1)
                    except OverflowError: x = float('inf')
                    
                    Pqg_calc_denumerator += x 

                Pqg_calc = Pqg_calc_numerator / Pqg_calc_denumerator
                
                
            # calculate the required bandwidth for service (j) usage by user group (i)
            RBi = Cij * Vj

            # aggregate the required bandwidth for all services of user group (i)
            rb += RBi
          
    if rb: rb = round_sig(rb, sig=3)
    return rb