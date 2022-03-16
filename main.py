###### imports and dependancies
from flask import Flask, render_template, request, url_for, redirect, flash, session
import os
from modules.user_accounts import UserAccounts
from modules.schools import Schools, arrangeSchoolData, getMiddleMileDefaultParamters
from modules.map import addCoverageMap, convertTemplate


##### initialize project components
app = Flask(__name__)                                               # create Flask application
app.config['SECRET_KEY'] = os.environ['3020_flask_app_secret_key']  # required for forms collection


###### function methods for convenience (run once if necessary)
# Schools().setDefaultParamters() # adds default middle- mile and last- mile paramters to the database



##### primary functions

def userSession():
    if 'firstName' in session: return session['firstName']
    return None


def updateMap():
    all_schools = Schools().getSchoolListing()
    with open('./static/map/map_template_c.html', 'w') as f: 
        f.write(render_template('map_template_b.html', school=all_schools))
    return all_schools





###### route for initalizing the map and default values used in the application
@app.route('/')
def inital():
    ##### initalizing the map
    
    # if map_template_b does not exist: 
        # render the original code (map_template_a) with cellular coverage areas
        # add the jinja2 loop for schools (convertTemplate function)
        # write contents to map_template_b
        
    if not os.path.exists('./templates/map_template_b.html'):
        template = render_template('map_template_a.html', tower=addCoverageMap())
        with open('./templates/map_template_b.html', 'w') as f: f.write(convertTemplate(template))
    
    
    # create final HTML which will be displayed (map_template_c)
        # take map_template_b and add the schools in the database
    
    with open('./static/map/map_template_c.html', 'w') as f:
        all_schools = Schools().getSchoolListing()
        f.write(render_template('map_template_b.html', school=all_schools))
    

    return redirect(url_for(".home"))





##### information routes
@app.route('/home')
def home():
    if 'all_groups' in session:
        session.pop('all_groups', None)
    return render_template('home.html', user=userSession())


@app.route('/about')
def about():
    return render_template('about.html', user=userSession())





##### user authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    
    # inital arrival to login page
    if not request.form: 
        return render_template('login.html')
    
    # retrieve and validate POST data
    user = UserAccounts().ValidateUserAccount(request.form)
    

    # on failed validation, show error message and return to login page with previously filled information
    if not user:
        flash('Invalid email/password')
        return render_template('login.html', form=request.form)

    # on successful validation, return to landing page with login status
    session['firstName'] = user['firstName']
    return redirect(url_for(".home"))


@app.route('/logout')
def logout():
    session.pop('firstName', None)
    return redirect(url_for(".home"))


@app.route('/register', methods=['GET', 'POST'])
def register():

    # inital arrival to registration page
    if not request.form: return render_template('register.html')

    # retreive POST form registation data
    firstName = request.form['firstName']
    lastName = request.form['lastName']
    email = request.form['email']
    password = request.form['password']

    # validate all data submitted from registration form
    error = { "status": False, "email": None, "password": None }
    error = UserAccounts().ValidateRegistration(error, email, password)

    if error['status']: return render_template('register.html', error=error, form=request.form)
    
    # submit user data to database
    reg_form = { 'firstName': firstName, 'lastName': lastName, 'email': email, 'password': password }
    UserAccounts().AddtoDB(reg_form)

    # return to landing page with login status
    session['firstName'] = firstName
    return redirect(url_for(".home"))





##### functionality routes
@app.route('/schools', methods=['GET', 'POST'])
def schoolListing():
    all_schools = Schools().getSchoolListing()
    
    # edit or delete school record
    if request.form.get("edit"): 
        return redirect(url_for("schoolEdit", school=request.form["edit"]))

    elif request.form.get("delete"):
        school_name = request.form["delete"]
        Schools().DeletefromDB(school_name)     # remove from database
        all_schools = updateMap()               # update listing and map
    
    return render_template('schoolListing.html', user=userSession(), list=all_schools)


@app.route('/schools/add', methods=['GET', 'POST'])
def schoolAdd():

    # add school page (No POST data)
    all_schools = Schools().getSchoolListing()
    if not request.form: return render_template('addSchool.html',user=userSession(), list=all_schools)

    # POST data validation is performed on the front-end

    school_data = arrangeSchoolData(request.form)   # arrange POST data for entry to database
    Schools().AddtoDB(school_data)                  # add to database
    updateMap()                                     # update map
    
    return redirect(url_for(".schoolUserDeviceGroup", school=school_data['school_name']))


@app.route('/schools/<school>/editInfo', methods=['GET', 'POST'])
def schoolEdit(school):

    # edit school page (No POST data)
    if not request.form:
        all_schools = Schools().getSchoolListing()
        school_data_dB = [x for x in all_schools if x['school_name'] == school]
        return render_template('editSchool.html', user=userSession(), school_data_dB=school_data_dB[0], list=all_schools)
    
    # POST data validation is performed on the front-end

    school_data_dB = arrangeSchoolData(request.form)    # arrange POST data for entry to database
    Schools().EditDB(school_data_dB)                    # update databaseng
    updateMap()                                         # update map
    
    return redirect(url_for(".schoolUserDeviceGroup", school=school_data_dB['school_name']))


@app.route('/schools/<school>/editUDG', methods=['GET', 'POST'])
def schoolUserDeviceGroup(school):

    if 'all_groups' not in session:
        all_schools = Schools().getSchoolListing()
        school_data_dB = [x for x in all_schools if x['school_name'] == school]
        dB_groups = school_data_dB[0]['user_device_groups']
        session['all_groups'] = dB_groups



    # arrival to school user device group page with no POST data
    if not request.form:
        return render_template('editUDG.html', user=userSession(), school=school, udg=session['all_groups'])

    
    
    if request.form.get("addUDG") or request.form.get("editUDG"):
        # arrange services
        service_list = ['Conversational Voice', 
                        'Video Conference',
                        'Streaming Audio',
                        'Streaming Video',
                        'Web Browsing',
                        'Data Transfer',
                        'Low Priority Transactions',
                        'Email',
                        'Client Server Software']

        services = [i for i in service_list if request.form.get(i)]

        user_group = {
            "group_name": request.form["group_name"],
            "profile": request.form["profile"],
            "services": services,
            "devices": int(request.form["devices"])
        }

        if request.form.get("addUDG"):
            tmp = session['all_groups']
            tmp.append(user_group)
            session['all_groups'] = tmp
            return redirect(url_for(".schoolUserDeviceGroup", school=school))
        
        
        elif request.form.get("editUDG"):
            for index, group in enumerate(session['all_groups']):
                if group['group_name'] == request.form.get('id_name'):
                    session['all_groups'][index] = user_group
                    break
            return redirect(url_for(".schoolUserDeviceGroup", school=school))


    if request.form.get("delete"):
        for x in session['all_groups']:
            if x['group_name'] == request.form['delete']:
                session['all_groups'].remove(x)
                break
        return redirect(url_for(".schoolUserDeviceGroup", school=school))
    
    if request.form.get("save"):
        all_schools = Schools().getSchoolListing()
        school_data_dB = [x for x in all_schools if x['school_name'] == school]
        school_data_dB[0]['user_device_groups'] = session['all_groups'].copy()
        session.pop('all_groups', None)

        Schools().EditUDG(school_data_dB[0])        # edit
        updateMap()                                 # update map

        return redirect(url_for(".middlemile", school=school))


@app.route('/schools/<school>/middlemile', methods=['GET', 'POST'])
def middlemile(school):

    
    all_schools = Schools().getSchoolListing()
    school_data_dB = [x for x in all_schools if x['school_name'] == school]
    
    if not school_data_dB[0]['middle_mile_parameters']:
        bandwidth = school_data_dB[0]['results']['required_bandwidth']
        paramter_val = getMiddleMileDefaultParamters(bandwidth)
    else:
        paramter_val = school_data_dB[0]['middle_mile_parameters']


    # arrival to middle-mile paramter configuration page with no POST data
    if not request.form:
        return render_template('middlemile.html', user=userSession(), school=school, param = paramter_val)
    
        
    middle_mile_paramters = {
        'focl': {
            'length' : float(request.form["length"]),
            'C_hdd' : request.form["C_hdd"],
            'C_cd' : request.form["C_cd"],
            'C_clm' : request.form["C_clm"],
            'C_focl' : request.form["C_focl"],
            'C_design' : request.form["C_design"],
            
            'N_CHm_avg': request.form["N_CHm_avg"],
            'N_c_avg': request.form["N_c_avg"],
            
            'T_geod_norm' : request.form["T_geod_norm"],
            'T_hdd_norm' : request.form["T_hdd_norm"],
            'T_cd_norm' : request.form["T_cd_norm"],
            'T_CHm_norm' : request.form["T_CHm_norm"],
            'T_clm_norm' : request.form["T_clm_norm"],
            'T_c_norm' : request.form["T_c_norm"],
            'T_st_norm' : request.form["T_st_norm"],
            'T_ts_norm' : request.form["T_ts_norm"],
            'T_sc_norm' : request.form["T_sc_norm"],
            'T_maint_focl_norm' : request.form["T_maint_focl_norm"],
            'T_maint_cd_norm' : request.form["T_maint_cd_norm"],
            
            'S_geod_norm' : request.form["S_geod_norm"],
            'S_1focl' : request.form["S_1focl"],
            'S_1c' : request.form["S_1c"],
            'S_hdd_norm' : request.form["S_hdd_norm"],
            'S_1cd' : request.form["S_1cd"],
            'S_1CMh' : request.form["S_1CMh"],
            'S_cd_norm' : request.form["S_cd_norm"],
            'S_CHm_norm' : request.form["S_CHm_norm"],
            'S_clm_norm' : request.form["S_clm_norm"],
            'S_c_norm' : request.form["S_c_norm"],
            'S_st_norm' : request.form["S_st_norm"],
            'S_ts_norm' : request.form["S_ts_norm"],
            'S_sc_norm' : request.form["S_sc_norm"],
            'S_tr_eq' : request.form["S_tr_eq"],
            'S_maint_focl_norm' : request.form["S_maint_focl_norm"],
            'S_maint_cd_norm' : request.form["S_maint_cd_norm"],
            
            'In' : request.form["In"],
            'T_vat' : request.form["T_vat"],
            'S_operation' : request.form["S_operation"],
            'T_prof' : request.form["T_prof"],
            'S_equip_mat' : request.form["S_equip_mat"],
            'T_lt' : request.form["T_lt"],
            'K_disc' : request.form["K_disc"],
            's_inv' : request.form["s_inv"],
        },
        
        'mw': {
            'L_rpl' : request.form["L_rpl"],
            'N_rts_term' : request.form["N_rts_term"],
            'C_rts' : request.form["C_rts"],
            'C_afd' : request.form["C_afd"],
            'C_design' : request.form["C_design"],
            'S_1rts' : request.form["S_1rts"],
            'S_1afd' : request.form["S_1afd"],
            'S_1pylon' : request.form["S_1pylon"],

            'S_geod_rts_norm' : request.form["S_geod_rts_norm"],
            'S_pylon_norm' : request.form["S_pylon_norm"],
            'S_afd_norm' : request.form["S_afd_norm"],
            'S_rts_norm' : request.form["S_rts_norm"],

            'S_rts_coord_norm' : request.form["S_rts_coord_norm"],
            'S_maint_1pylon_norm' :request.form["S_maint_1pylon_norm"],
            'S_maint_afd_norm' : request.form["S_maint_afd_norm"],
            'S_maint_rts_norm' : request.form["S_maint_rts_norm"],
            'S_spectrum' : request.form["S_spectrum"],
            'S_annual_spectrum_fee' : request.form["S_annual_spectrum_fee"],

            'T_geod_norm' :request.form["T_geod_norm"],
            'T_pylon_norm' : request.form["T_pylon_norm"],
            'T_afd_norm' : request.form["T_afd_norm"],
            'T_rts_norm' : request.form["T_rts_norm"],
            'T_coord_norm' : request.form["T_coord_norm"],
            
            'T_maint_pylon_norm' : request.form["T_maint_pylon_norm"],
            'T_maint_afd_norm' : request.form["T_maint_afd_norm"],
            'T_maint_rts_norm' : request.form["T_maint_rts_norm"],
            
            'In' : request.form["mw_In"],
            'T_vat' : request.form["mw_T_vat"],
            'S_operation' : request.form["mw_S_operation"],
            'T_prof' : request.form["mw_T_prof"],
            'S_equip_mat' : request.form["mw_S_equip_mat"],
            'T_lt' : request.form["mw_T_lt"],
            'K_disc' : request.form["mw_K_disc"],
            's_inv' : request.form["mw_s_inv"],
        },
        
        'sat': {
            'V_chan' : request.form["V_chan"],
            'V_1user' : request.form["V_1user"],
            'S_1user' : request.form["S_1user"],
            'S_mat_1user' : request.form["S_mat_1user"],
            'S_user_typ' : request.form["S_user_typ"],
            'T_user_typ' : request.form["T_user_typ"],
            'C_user' : request.form["C_user"],
            'C_design' : request.form["C_design"],
            'S_rent_1mbit' : request.form["S_rent_1mbit"],
            'S_maint_1user' :request.form["S_maint_1user"],
            'T_maint_1user' : request.form["T_maint_1user"],
            
            'In' : request.form["sat_In"],
            'T_vat' : request.form["sat_T_vat"],
            'S_operation' : request.form["sat_S_operation"],
            'T_prof' : request.form["sat_T_prof"],
            'S_equip_mat' : request.form["sat_S_equip_mat"],
            'T_lt' : request.form["sat_T_lt"],
            'K_disc' : request.form["sat_K_disc"],
            's_inv' : request.form["sat_s_inv"],

        }
    }
    
    all_schools = Schools().getSchoolListing()
    school_data_dB = [x for x in all_schools if x['school_name'] == school]
    
    Schools().updateMiddleMile(school_data_dB[0], middle_mile_paramters)
    updateMap()     # update map
    
    return redirect(url_for(".schoolListing"))


@app.route('/schools/<school>/lastmile', methods=['GET', 'POST'])
def lastmile(school):
    
    # arrival to middle-mile paramter configuration page with no POST data
    if not request.form:
        return render_template('lastmile.html', user=userSession(), school=school)
    
    
    return redirect(url_for(".schoolListing"))





##### run application
if __name__ == '__main__':
    app.run(debug=True)
