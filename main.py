# imports and dependancies
from flask import Flask, render_template, request, url_for, redirect, flash, session
import os
from modules.user_accounts import UserAccounts
from modules.schools import Schools, arrangeSchoolData
from modules.map import addCoverageMap, convertTemplate



# initialize project components
app = Flask(__name__)                                               # create Flask application
app.config['SECRET_KEY'] = os.environ('3020_flask_app_secret_key')  # required for forms collection



def userSession():
    if 'firstName' in session: return session['firstName']
    return None



def updateMap():
    all_schools = Schools().getSchoolListing()
    with open('./static/map/map_template_c.html', 'w') as f: 
        f.write(render_template('map_template_b.html', school=all_schools))
    return all_schools




# route for initalizing map
@app.route('/')
def inital():
    
    # map_template_a contains leaflet code for map, feature groups and jinja2 loop for tower locations
    # map_template_b contains leaflet code for map, feature groups, coverage maps and jinja2 loop for schools
    # map_template_c contains leaflet code for map, feature groups, coverage maps and schools
    
    if not os.path.exists('./templates/map_template_b.html'):
        # if template b does not exist, get code from template a
        template = render_template('map_template_a.html', tower=addCoverageMap())
        
        # then write to template b (after adding jinja2 loop for schools)
        with open('./templates/map_template_b.html', 'w') as f: 
            f.write(convertTemplate(template))
    
    # then write template c for displaying (this will be used repeatitively)
    with open('./static/map/map_template_c.html', 'w') as f:
        all_schools = Schools().getSchoolListing()
        f.write(render_template('map_template_b.html', school=all_schools))
    
    return redirect(url_for(".home"))




# information
@app.route('/home')
def home():
    if 'all_groups' in session:
        session.pop('all_groups', None)
    return render_template('home.html', user=userSession())




@app.route('/about')
def about():
    return render_template('about.html', user=userSession())




# user authentication
@app.route('/login', methods=['GET', 'POST'])
def login():
    
    # inital arrival to login page
    if not request.form: return render_template('login.html')
    
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




# functionality
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

        return redirect(url_for(".schoolListing"))




if __name__ == '__main__':
    app.run(debug=True)
