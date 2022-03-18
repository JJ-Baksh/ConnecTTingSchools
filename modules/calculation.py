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


def middleMileTechnology(parameters):
    
    def focl():
        ##### inital data
        
        l = float(parameters['focl']['length'])          # kilometers
        T_payback = 5   # years

        ##### default values

        # coefficients (C)
        C_hdd = float(parameters['focl']['C_hdd'])
        C_cd = float(parameters['focl']['C_cd'])
        C_clm = float(parameters['focl']['C_clm'])
        C_focl = float(parameters['focl']['C_focl'])
        C_design = float(parameters['focl']['C_design'])


        # user definable
        N_CHm_avg = float(parameters['focl']['N_CHm_avg'])           # assumed
        N_c_avg = float(parameters['focl']['N_c_avg'])           # assumed


        # labour norms (T)
        T_geod_norm = float(parameters['focl']['T_geod_norm'])     # units: man-hours/km, value: provided
        T_hdd_norm = float(parameters['focl']['T_hdd_norm'])    # units: man-hours/km, value: provided
        T_cd_norm = float(parameters['focl']['T_cd_norm']) 
        T_CHm_norm = float(parameters['focl']['T_CHm_norm'])
        T_clm_norm = float(parameters['focl']['T_clm_norm'])
        T_c_norm = float(parameters['focl']['T_c_norm'])
        T_st_norm = float(parameters['focl']['T_st_norm']) 
        T_ts_norm = float(parameters['focl']['T_ts_norm'])
        T_sc_norm = float(parameters['focl']['T_sc_norm'])
        T_maint_focl_norm = float(parameters['focl']['T_maint_focl_norm'])
        T_maint_cd_norm = float(parameters['focl']['T_maint_cd_norm'])

        # cost norms (S)
        S_geod_norm = float(parameters['focl']['S_geod_norm'])       # assumed
        S_1focl = float(parameters['focl']['S_1focl'])       
        S_1c = float(parameters['focl']['S_1c'])           
        S_hdd_norm = float(parameters['focl']['S_hdd_norm'])        # assumed
        S_1cd = float(parameters['focl']['S_1cd'])       
        S_1CMh = float(parameters['focl']['S_1CMh'])        
        S_cd_norm = float(parameters['focl']['S_cd_norm'])        # assumed
        S_CHm_norm = float(parameters['focl']['S_CHm_norm'])        # assumed
        S_clm_norm = float(parameters['focl']['S_clm_norm'])       # assumed
        S_c_norm = float(parameters['focl']['S_c_norm'])          # assumed
        S_st_norm = float(parameters['focl']['S_st_norm'])         # assumed
        S_ts_norm = float(parameters['focl']['S_ts_norm'])       # assumed
        S_sc_norm = float(parameters['focl']['S_sc_norm'])       # assumed
        S_tr_eq = float(parameters['focl']['S_tr_eq'])
        S_maint_focl_norm = float(parameters['focl']['S_maint_focl_norm']) # assumed
        S_maint_cd_norm = float(parameters['focl']['S_maint_cd_norm'])   # assumed


        ##### TCO calculations
        L_focl = l * (1.0 + C_hdd)
        L_cd = L_focl * C_cd
        L_clm = L_focl * C_clm
        N_CMh = L_cd * N_CHm_avg
        N_c = L_focl * N_c_avg
        S_geod = l * T_geod_norm * S_geod_norm
        S_focl = L_focl * (1 + C_focl) * S_1focl + (N_c * S_1c)
        S_hdd = L_focl * T_hdd_norm * S_hdd_norm
        S_cd_mat = (L_cd * S_1cd) + (N_CMh * S_1CMh)
        S_cd_lab = (L_cd * T_cd_norm * S_cd_norm) + (N_CMh * T_CHm_norm * S_CHm_norm)
        S_cd = S_cd_mat + S_cd_lab
        S_clm = (L_clm * T_clm_norm * S_clm_norm) + (N_c * T_c_norm * S_c_norm)
        S_st = L_focl * T_st_norm * S_st_norm
        S_ts = T_ts_norm * S_ts_norm
        S_sc = T_sc_norm * S_sc_norm
        S_design = (S_focl + S_hdd + S_cd + S_clm) * C_design
        S_focl_instal = S_geod + S_focl + S_hdd + S_cd + S_clm + S_st + S_ts + S_sc + S_design + S_tr_eq
        S_maint_FOCL = L_focl * T_maint_focl_norm * S_maint_focl_norm
        S_maint_cd = L_cd * T_maint_cd_norm * S_maint_cd_norm
        S_maint_total = S_maint_FOCL + S_maint_cd


        In = float(parameters['focl']['In'])           # assumed
        T_vat = float(parameters['focl']['T_vat'])              # assumed
        S_operation = float(parameters['focl']['S_operation'])    # assumed
        T_prof = float(parameters['focl']['T_prof'])             # assumed
        S_equip_mat = float(parameters['focl']['S_equip_mat'])    # assumed
        T_lt = float(parameters['focl']['T_lt'])               # assumed
        K_disc = float(parameters['focl']['K_disc'])              # assumed
        s_inv = float(parameters['focl']['s_inv'])        # assumed

        # NPV calculations
        niat = In * (1 - (T_vat/100))
        nopat = (niat - S_operation) * (1 - (T_prof/100))
        cf = nopat + (S_equip_mat / T_lt)
        
        cf_disc = 0
        for j in range(1, T_payback):
            cf_disc += (cf / (1 + (K_disc/100))**j)
        
        npv = cf_disc - s_inv

        return S_focl_instal+ (T_payback *S_maint_total), npv
    
    
    def microwave():
        ##### inital data
        l = 100          # kilometers
        T_payback = 5   # years

        ##### default values
        L_rpl = float(parameters['mw']['L_rpl']) 
        N_rts_term = float(parameters['mw']['N_rts_term']) 
        
        # coefficients
        C_rts = float(parameters['mw']['C_rts']) 
        C_afd = float(parameters['mw']['C_afd']) 
        C_design = float(parameters['mw']['C_design']) 
        
        # cost norms (S)
        S_1rts = float(parameters['mw']['S_1rts']) 
        S_1afd = float(parameters['mw']['S_1afd']) 
        S_1pylon =float(parameters['mw']['S_1pylon']) 
        S_geod_rts_norm = float(parameters['mw']['S_geod_rts_norm'])   # assumed
        S_pylon_norm = float(parameters['mw']['S_pylon_norm'])      # assumed
        S_afd_norm = float(parameters['mw']['S_afd_norm'])        # assumed
        S_rts_norm = float(parameters['mw']['S_rts_norm'])        # assumed
        S_rts_coord_norm = float(parameters['mw']['S_rts_coord_norm']) 
        S_maint_1pylon_norm = float(parameters['mw']['S_maint_1pylon_norm']) 
        S_maint_afd_norm = float(parameters['mw']['S_maint_afd_norm']) 
        S_maint_rts_norm = float(parameters['mw']['S_maint_rts_norm']) 
        S_spectrum = float(parameters['mw']['S_spectrum']) 
        S_annual_spectrum_fee = float(parameters['mw']['S_annual_spectrum_fee'])    # assumed
        
        # labor norms (T)
        T_geod_norm = float(parameters['mw']['T_geod_norm'])
        T_pylon_norm = float(parameters['mw']['T_pylon_norm'])
        T_afd_norm = float(parameters['mw']['T_afd_norm']) 
        T_rts_norm = float(parameters['mw']['T_rts_norm']) 
        T_coord_norm = float(parameters['mw']['T_coord_norm']) 
        T_maint_pylon_norm = float(parameters['mw']['T_maint_pylon_norm'])    # assumed
        T_maint_afd_norm = float(parameters['mw']['T_maint_afd_norm'])      # assumed
        T_maint_rts_norm = float(parameters['mw']['T_maint_rts_norm'])      # assumed

        ##### TCO calculations
        N_rs = l / L_rpl
        N_rts_repeat = N_rs - 1
        
        S_rts = S_1rts * (C_rts * (N_rts_repeat + N_rts_term))
        S_afd = S_1afd * (C_afd * (N_rts_repeat + N_rts_term))
        S_pylon = S_1pylon * (N_rts_repeat + N_rts_term)
        S_geod_rts = S_geod_rts_norm * T_geod_norm * (N_rts_repeat + N_rts_term)
        S_p_pylon = (S_pylon_norm * T_pylon_norm) * (N_rts_repeat + N_rts_term)
        S_p_afd = (S_afd_norm * T_afd_norm) * (N_rts_repeat + N_rts_term)
        S_p_rts = (S_rts_norm * T_rts_norm) * (N_rts_repeat + N_rts_term)
        S_rts_coord = (S_rts_coord_norm * T_coord_norm) * (N_rts_repeat + N_rts_term)
        S_design = (S_p_afd + S_p_rts + S_p_pylon) * C_design
        S_cost_rts = S_p_rts + S_p_afd + S_p_pylon + S_rts + S_afd + S_pylon + S_design + S_rts_coord + S_spectrum
        S_maint_pylon = T_maint_pylon_norm * S_maint_1pylon_norm * (N_rts_repeat + N_rts_term)
        S_maint_afd = T_maint_afd_norm * S_maint_afd_norm * (N_rts_repeat + N_rts_term)
        S_maint_rts = T_maint_rts_norm * S_maint_rts_norm * (N_rts_repeat + N_rts_term)
        S_maint = S_maint_rts + S_maint_afd + S_maint_pylon + S_annual_spectrum_fee
        
        ##### NPV calculations
        In = float(parameters['mw']['In'])            # assumed
        T_vat = float(parameters['mw']['T_vat'])               # assumed
        S_operation = float(parameters['mw']['S_operation'])     # assumed
        T_prof = float(parameters['mw']['T_prof'])              # assumed
        S_equip_mat = float(parameters['mw']['S_equip_mat'])     # assumed
        T_lt = float(parameters['mw']['T_lt'])                # assumed
        K_disc = float(parameters['mw']['K_disc'])               # assumed
        s_inv = float(parameters['mw']['s_inv'])         # assumed

        # NPV calculations
        niat = In * (1 - (T_vat/100))
        nopat = (niat - S_operation) * (1 - (T_prof/100))
        cf = nopat + (S_equip_mat / T_lt)
        
        cf_disc = 0
        for j in range(1, T_payback):
            cf_disc += (cf / (1 + (K_disc/100))**j)
        
        npv = cf_disc - s_inv

        return S_cost_rts+ (T_payback *S_maint), npv
        
    
    def satellite():
        ##### inital data
        T_payback = 5   # years

        ##### default values
        V_chan = float(parameters['sat']['V_chan'])
        V_1user = float(parameters['sat']['V_1user'])
        S_1user = float(parameters['sat']['S_1user'])       # assumed
        S_mat_1user = float(parameters['sat']['S_mat_1user'])   # assumed
        S_user_typ = float(parameters['sat']['S_user_typ'])      # assumed
        T_user_typ = float(parameters['sat']['T_user_typ'])         # assumed
        C_user = float(parameters['sat']['C_user'])
        C_design = float(parameters['sat']['C_design'])
        S_rent_1mbit = float(parameters['sat']['S_rent_1mbit'])     # assumed
        S_maint_1user = float(parameters['sat']['S_maint_1user'])    # assumed
        T_maint_1user = float(parameters['sat']['T_maint_1user'])

        # TCO calculations
        N_user = int(math.ceil(V_chan / V_1user))
        S_user = N_user * (S_1user + S_mat_1user)
        S_m_user = N_user * (S_user_typ * T_user_typ)
        S_design = ((C_user * S_user) + S_m_user) * C_design
        S_establ_user = S_user = S_user + S_m_user + S_design
        S_rent_chan = V_chan * S_rent_1mbit
        S_serv_user = N_user * S_maint_1user * T_maint_1user
        S_maint_user = S_rent_chan + S_serv_user
        
        ##### NPV calculations
        In = float(parameters['sat']['In'])           # assumed
        T_vat = float(parameters['sat']['T_vat'])              # assumed
        S_operation = float(parameters['sat']['S_operation'])    # assumed
        T_prof = float(parameters['sat']['T_prof'])             # assumed
        S_equip_mat = float(parameters['sat']['S_equip_mat'])    # assumed
        T_lt = float(parameters['sat']['T_lt'])               # assumed
        K_disc = float(parameters['sat']['K_disc'])              # assumed
        s_inv = float(parameters['sat']['s_inv'])        # assumed

        # NPV calculations
        niat = In * (1 - (T_vat/100))
        nopat = (niat - S_operation) * (1 - (T_prof/100))
        cf = nopat + (S_equip_mat / T_lt)
        
        cf_disc = 0
        for j in range(1, T_payback):
            cf_disc += (cf / (1 + (K_disc/100))**j)
        
        npv = cf_disc - s_inv   

        return S_establ_user+ (T_payback *S_maint_user), npv


    focl_tco, focl_npv = focl()
    mw_tco, mw_npv = microwave()
    sat_tco, sat_npv = satellite()
    
    tco = [focl_tco, mw_tco, sat_tco]
    npv = [focl_npv, mw_npv, sat_npv]

    index_min_tco = tco.index(min(tco))
    index_max_npv = npv.index(max(npv))

    # name, tco, npv
    final_tco = ['', "{:.2f}".format( tco[index_min_tco] ), "{:.2f}".format( npv[index_min_tco] )]
    if index_min_tco == 0: final_tco[0] = 'Fiber optic'
    if index_min_tco == 1: final_tco[0] = 'Microwave radio'
    if index_min_tco == 2: final_tco[0] = 'Satellite'


    final_npv = ['', "{:.2f}".format( tco[index_max_npv] ), "{:.2f}".format( npv[index_max_npv] )]
    if index_max_npv == 0: final_npv[0] = 'Fiber optic'
    if index_max_npv == 1: final_npv[0] = 'Microwave radio'
    if index_max_npv == 2: final_npv[0] = 'Satellite'

    return final_tco, final_npv


def lastMileTechnology(parameters):
    tech = {'Fiber Optic Cable': 0, 
            'Microwave': 0, 
            'Satellite': 0, 
            'Cellular': 0}
    
    T_payback = 5
    
    for i in parameters: 
        In = float(parameters[i]['In'])
        T_vat = float(parameters[i]['T_vat'])
        S_operation = float(parameters[i]['S_operation'])
        T_prof = float(parameters[i]['T_prof'])
        S_equip_mat = float(parameters[i]['S_equip_mat'])
        T_lt = float(parameters[i]['T_lt'])
        K_disc = float(parameters[i]['K_disc'])
        s_inv = float(parameters[i]['s_inv'])

        # NPV calculations
        niat = In * (1 - (T_vat/100))
        nopat = (niat - S_operation) * (1 - (T_prof/100))
        cf = nopat + (S_equip_mat / T_lt)
        
        cf_disc = 0
        for j in range(1, T_payback):
            cf_disc += (cf / (1 + (K_disc/100))**j)
        
        npv = cf_disc - s_inv
        
        tech[i] = float("{:.2f}".format( npv ))

    
    return min(tech.items(), key=lambda x: x[1])