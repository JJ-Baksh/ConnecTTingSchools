###### imports and dependancies
from flask import Flask, render_template, request, url_for, redirect, flash, session
from flask_mail import Mail, Message
from itsdangerous import SignatureExpired, URLSafeTimedSerializer
import os
from functools import wraps
from modules.user_accounts import UserAccounts
from modules.schools import Schools, arrangeSchoolData, getMiddleMileDefaultParamters, getLastMileDefaultParamters
from modules.map import addCoverageMap, convertTemplate

# database test functions
from pymongo import MongoClient
cluster = MongoClient('mongodb+srv://ECNG3020:Electrical1999@cluster0.nxa5e.mongodb.net/ECNG3020?retryWrites=true&w=majority')
database = cluster['ECNG3020']
collection = database['Test']
print(collection.find_one())
cluster.close()


##### initialize project components
app = Flask(__name__)                                               # create Flask application
app.config['SECRET_KEY'] = 'rA7AfwoD0i'  # required for forms collection
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'connecTTingSchools@gmail.com'
app.config['MAIL_PASSWORD'] = 'irnrafphtremufyp'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

## decorator to ensure correct user authorization level before accessing
def login_required(f):
    @wraps(f)
    def decorater(*args, **kwargs):
        if session.get('firstName') is None:
            return redirect('/login',code=302)
        return f(*args, **kwargs)
    return decorater



def userSession():
    return session.get('firstName')


def updateMap():
    with open('./static/map/map_template_c.html', 'w') as f:
        all_schools = Schools().getSchoolListing()
        f.write(render_template('map_template_b.html', school=all_schools))
        return all_schools




## initalize the map
@app.route('/')
def inital():
        
    if not os.path.exists('./templates/map_template_b.html'):
        template = render_template('map_template_a.html', tower=addCoverageMap())
        with open('./templates/map_template_b.html', 'w') as f: 
            f.write(convertTemplate(template))
    
    with open('./static/map/map_template_c.html', 'w') as f:
        f.write(render_template('map_template_b.html', school=Schools().getSchoolListing()))
    
    return redirect(url_for(".home"))


## information routes
@app.route('/home')
def home():
    session.pop('all_groups', None)
    return render_template('home.html', user=userSession())


@app.route('/about')
def about():
    session.pop('all_groups', None)
    return render_template('about.html', user=userSession())


## user authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    session.pop('all_groups', None)
    
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
@login_required
def logout():
    session.pop('firstName', None)
    session.pop('all_groups', None)
    return redirect(url_for(".home"))


@app.route('/register', methods=['GET', 'POST'])
def register():
    session.pop('all_groups', None)
    
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
    
    # send token to user email to verify email
    token = s.dumps(email, salt='email-confirm')
    msg = Message('ConnecTTing Schools Verify Email', sender='connecTTingSchools@gmail.com', recipients=[email])
    
    link = url_for('confirm_email', token=token, _external=True)
    msg.body = f'Click on the link to verify your email: {link}\n\n This code will expire in 1 hour.'
    mail.send(msg)
    
    reg_form = { 'firstName': firstName, 'lastName': lastName, 'email': email, 'password': password, 'verified': False}
    UserAccounts().AddtoDB(reg_form)

    # return to landing page
    flash(f'Check {email} for your verification link')
    return redirect(url_for(".login"))


@app.route('/confirm_email/<token>')
def confirm_email(token):
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600)
        
        session['name'] = UserAccounts().VerifyEmail(email)
        flash('Verification Successful. Please Log In!')
        return redirect(url_for(".login"))
    
    except SignatureExpired:
        flash(f'Verification Link Expired. Try Again.')
        return redirect(url_for(".register"))


##### functionality routes
@app.route('/schools', methods=['GET', 'POST'])
@login_required
def schoolListing():
    session.pop('all_groups', None)
    all_schools = Schools().getSchoolListing()
    
    # if an edit button was clicked
    if request.form.get("edit"): 
        return redirect(url_for("schoolEdit", school=request.form["edit"]))

    # if a delete button was clicked
    elif request.form.get("delete"):
        school_name = request.form["delete"]
        Schools().DeletefromDB(school_name)
        all_schools = updateMap()
    
    return render_template('schoolListing.html', user=userSession(), list=all_schools)


@app.route('/schools/add', methods=['GET', 'POST'])
@login_required
def schoolAdd():
    session.pop('all_groups', None)
    all_schools = Schools().getSchoolListing()
    
    if not request.form: 
        return render_template('addSchool.html',user=userSession(), list=all_schools)

    school_data = arrangeSchoolData(request.form)
    Schools().AddtoDB(school_data)
    updateMap()
    
    return redirect(url_for(".schoolUserDeviceGroup", school=school_data['school_name']))


@app.route('/schools/<school>/editInfo', methods=['GET', 'POST'])
@login_required
def schoolEdit(school):
    session.pop('all_groups', None)
    
    if not request.form:
        all_schools = Schools().getSchoolListing()
        school_data_dB = [x for x in all_schools if x['school_name'] == school]
        return render_template('editSchool.html', user=userSession(), school_data_dB=school_data_dB[0], list=all_schools)

    school_data_dB = arrangeSchoolData(request.form)
    Schools().EditDB(school_data_dB)
    updateMap()
    
    return redirect(url_for(".schoolUserDeviceGroup", school=school_data_dB['school_name']))


@app.route('/schools/<school>/editUDG', methods=['GET', 'POST'])
@login_required
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
                    tmp = session['all_groups']
                    tmp[index] = user_group
                    session['all_groups'] = tmp
                    break

            return redirect(url_for(".schoolUserDeviceGroup", school=school))

    if request.form.get("delete"):
        for x in session['all_groups']:
            if x['group_name'] == request.form['delete']:
                tmp = session['all_groups']
                tmp.remove(x)
                session['all_groups'] = tmp
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
@login_required
def middlemile(school):
    session.pop('all_groups', None)
    
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
            'length' : float(request.form["focl_length"]),
            'T_payback' : request.form["focl_T_payback"],
            'C_hdd' : request.form["focl_C_hdd"],
            'C_cd' : request.form["focl_C_cd"],
            'C_clm' : request.form["focl_C_clm"],
            'C_focl' : request.form["focl_C_focl"],
            'C_design' : request.form["focl_C_design"],
            
            'N_CHm_avg': request.form["focl_N_CHm_avg"],
            'N_c_avg': request.form["focl_N_c_avg"],
            
            'T_geod_norm' : request.form["focl_T_geod_norm"],
            'T_hdd_norm' : request.form["focl_T_hdd_norm"],
            'T_cd_norm' : request.form["focl_T_cd_norm"],
            'T_CHm_norm' : request.form["focl_T_CHm_norm"],
            'T_clm_norm' : request.form["focl_T_clm_norm"],
            'T_c_norm' : request.form["focl_T_c_norm"],
            'T_st_norm' : request.form["focl_T_st_norm"],
            'T_ts_norm' : request.form["focl_T_ts_norm"],
            'T_sc_norm' : request.form["focl_T_sc_norm"],
            'T_maint_focl_norm' : request.form["focl_T_maint_focl_norm"],
            'T_maint_cd_norm' : request.form["focl_T_maint_cd_norm"],
            
            'S_geod_norm' : request.form["focl_S_geod_norm"],
            'S_1focl' : request.form["focl_S_1focl"],
            'S_1c' : request.form["focl_S_1c"],
            'S_hdd_norm' : request.form["focl_S_hdd_norm"],
            'S_1cd' : request.form["focl_S_1cd"],
            'S_1CMh' : request.form["focl_S_1CMh"],
            'S_cd_norm' : request.form["focl_S_cd_norm"],
            'S_CHm_norm' : request.form["focl_S_CHm_norm"],
            'S_clm_norm' : request.form["focl_S_clm_norm"],
            'S_c_norm' : request.form["focl_S_c_norm"],
            'S_st_norm' : request.form["focl_S_st_norm"],
            'S_ts_norm' : request.form["focl_S_ts_norm"],
            'S_sc_norm' : request.form["focl_S_sc_norm"],
            'S_tr_eq' : request.form["focl_S_tr_eq"],
            'S_maint_focl_norm' : request.form["focl_S_maint_focl_norm"],
            'S_maint_cd_norm' : request.form["focl_S_maint_cd_norm"],
            
            'In' : request.form["focl_In"],
            'T_vat' : request.form["focl_T_vat"],
            'S_operation' : request.form["focl_S_operation"],
            'T_prof' : request.form["focl_T_prof"],
            'S_equip_mat' : request.form["focl_S_equip_mat"],
            'T_lt' : request.form["focl_T_lt"],
            'K_disc' : request.form["focl_K_disc"],
            's_inv' : request.form["focl_s_inv"],
        },
        
        'mw': {
            'L_rpl' : request.form["mw_L_rpl"],
            'N_rts_term' : request.form["mw_N_rts_term"],
            'C_rts' : request.form["mw_C_rts"],
            'C_afd' : request.form["mw_C_afd"],
            'C_design' : request.form["mw_C_design"],
            'S_1rts' : request.form["mw_S_1rts"],
            'S_1afd' : request.form["mw_S_1afd"],
            'S_1pylon' : request.form["mw_S_1pylon"],

            'S_geod_rts_norm' : request.form["mw_S_geod_rts_norm"],
            'S_pylon_norm' : request.form["mw_S_pylon_norm"],
            'S_afd_norm' : request.form["mw_S_afd_norm"],
            'S_rts_norm' : request.form["mw_S_rts_norm"],

            'S_rts_coord_norm' : request.form["mw_S_rts_coord_norm"],
            'S_maint_1pylon_norm' :request.form["mw_S_maint_1pylon_norm"],
            'S_maint_afd_norm' : request.form["mw_S_maint_afd_norm"],
            'S_maint_rts_norm' : request.form["mw_S_maint_rts_norm"],
            'S_spectrum' : request.form["mw_S_spectrum"],
            'S_annual_spectrum_fee' : request.form["mw_S_annual_spectrum_fee"],

            'T_geod_norm' :request.form["mw_T_geod_norm"],
            'T_pylon_norm' : request.form["mw_T_pylon_norm"],
            'T_afd_norm' : request.form["mw_T_afd_norm"],
            'T_rts_norm' : request.form["mw_T_rts_norm"],
            'T_coord_norm' : request.form["mw_T_coord_norm"],
            
            'T_maint_pylon_norm' : request.form["mw_T_maint_pylon_norm"],
            'T_maint_afd_norm' : request.form["mw_T_maint_afd_norm"],
            'T_maint_rts_norm' : request.form["mw_T_maint_rts_norm"],
            
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
            'V_chan' : request.form["sat_V_chan"],
            'V_1user' : request.form["sat_V_1user"],
            'S_1user' : request.form["sat_S_1user"],
            'S_mat_1user' : request.form["sat_S_mat_1user"],
            'S_user_typ' : request.form["sat_S_user_typ"],
            'T_user_typ' : request.form["sat_T_user_typ"],
            'C_user' : request.form["sat_C_user"],
            'C_design' : request.form["sat_C_design"],
            'S_rent_1mbit' : request.form["sat_S_rent_1mbit"],
            'S_maint_1user' :request.form["sat_S_maint_1user"],
            'T_maint_1user' : request.form["sat_T_maint_1user"],
            
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
    
    Schools().selectMiddleMile(school_data_dB[0], middle_mile_paramters)
    updateMap()     # update map
    
    return redirect(url_for(".lastmile", school=school))


@app.route('/schools/<school>/lastmile', methods=['GET', 'POST'])
@login_required
def lastmile(school):
    session.pop('all_groups', None)
    
    all_schools = Schools().getSchoolListing()
    school_data_dB = [x for x in all_schools if x['school_name'] == school]
    
    if not school_data_dB[0]['last_mile_parameters']:
        paramter_val = getLastMileDefaultParamters()
    else:
        paramter_val = school_data_dB[0]['last_mile_parameters']

    # arrival to middle-mile paramter configuration page with no POST data
    if not request.form:
        return render_template('lastmile.html', user=userSession(), school=school, param = paramter_val)
    
    last_mile_paramters = {
        'Fiber Optic Cable': {
            'M_aoe_cover' : request.form["focl_M_aoe_cover"],
            'M_aoe' : request.form["focl_M_aoe"],
            'N_connect' : request.form["focl_N_connect"],
            'C_teap_aoe' : request.form["focl_C_teap_aoe"],
            'length' : request.form["focl_length"],
            'S_places_cost' : request.form["focl_S_places_cost"],
            'S_inst_equip' : request.form["focl_S_inst_equip"],
            'S_cable' : request.form["focl_S_cable"],
            
            'In' : request.form["focl_In"],
            'T_vat' : request.form["focl_T_vat"],
            'S_operation' : request.form["focl_S_operation"],
            'T_prof' : request.form["focl_T_prof"],
            'S_equip_mat' : request.form["focl_S_equip_mat"],
            'T_lt' : request.form["focl_T_lt"],
            'K_disc' : request.form["focl_K_disc"],
            's_inv' : request.form["focl_s_inv"],
        },
        
        'Microwave': {
            'M_aoe_cover' : request.form["mw_M_aoe_cover"],
            'M_aoe' : request.form["mw_M_aoe"],
            'N_connect' : request.form["mw_N_connect"],
            'C_teap_aoe' : request.form["mw_C_teap_aoe"],
            'length' : request.form["mw_length"],
            'S_places_cost' : request.form["mw_S_places_cost"],
            'S_inst_equip' : request.form["mw_S_inst_equip"],
            'S_cable' : request.form["mw_S_cable"],
            
            'In' : request.form["mw_In"],
            'T_vat' : request.form["mw_T_vat"],
            'S_operation' : request.form["mw_S_operation"],
            'T_prof' : request.form["mw_T_prof"],
            'S_equip_mat' : request.form["mw_S_equip_mat"],
            'T_lt' : request.form["mw_T_lt"],
            'K_disc' : request.form["mw_K_disc"],
            's_inv' : request.form["mw_s_inv"],
        },
        
        'Satellite': {
            'M_aoe_cover' : request.form["sat_M_aoe_cover"],
            'M_aoe' : request.form["sat_M_aoe"],
            'N_connect' : request.form["sat_N_connect"],
            'C_teap_aoe' : request.form["sat_C_teap_aoe"],
            'length' : request.form["sat_length"],
            'S_places_cost' : request.form["sat_S_places_cost"],
            'S_inst_equip' : request.form["sat_S_inst_equip"],
            'S_cable' : request.form["sat_S_cable"],
            
            'In' : request.form["sat_In"],
            'T_vat' : request.form["sat_T_vat"],
            'S_operation' : request.form["sat_S_operation"],
            'T_prof' : request.form["sat_T_prof"],
            'S_equip_mat' : request.form["sat_S_equip_mat"],
            'T_lt' : request.form["sat_T_lt"],
            'K_disc' : request.form["sat_K_disc"],
            's_inv' : request.form["sat_s_inv"],
        },
        
        'Cellular': {
            'M_aoe_cover' : request.form["cell_M_aoe_cover"],
            'M_aoe' : request.form["cell_M_aoe"],
            'N_connect' : request.form["cell_N_connect"],
            'C_teap_aoe' : request.form["cell_C_teap_aoe"],
            'length' : request.form["cell_length"],
            'S_places_cost' : request.form["cell_S_places_cost"],
            'S_inst_equip' : request.form["cell_S_inst_equip"],
            'S_cable' : request.form["cell_S_cable"],
            
            'In' : request.form["cell_In"],
            'T_vat' : request.form["cell_T_vat"],
            'S_operation' : request.form["cell_S_operation"],
            'T_prof' : request.form["cell_T_prof"],
            'S_equip_mat' : request.form["cell_S_equip_mat"],
            'T_lt' : request.form["cell_T_lt"],
            'K_disc' : request.form["cell_K_disc"],
            's_inv' : request.form["cell_s_inv"],
        }
    }
    

    all_schools = Schools().getSchoolListing()
    school_data_dB = [x for x in all_schools if x['school_name'] == school]
    
    Schools().selectLastMile(school_data_dB[0], last_mile_paramters)
    updateMap()
    
    return redirect(url_for(".schoolListing"))




##### run application
if __name__ == '__main__':
    app.run(debug=True)