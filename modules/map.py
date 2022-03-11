import pandas as pd

def convertTemplate(template):
    index = template.find('var schoolPLACEMENT') - 1
    
    start = template[:index]
    
    end = template[index:]
    
    middle = '''
    {% for x in school %}
    
    var icon_{{x._id}} = L.AwesomeMarkers.icon(
        {"extraClasses": "fa-rotate-0", 
        icon: "info-sign", 
        "iconColor": "white",
        {% if x.user_device_groups %} "markerColor": "green", {% else %} "markerColor": "red", {% endif %}
        "prefix": "glyphicon"}
    )

    var school_{{x._id}} = L.marker(
        [{{x.latitude}}, {{x.longitude}}], {
            icon: icon_{{x._id}},
        },
    ).addTo({% if x.user_device_groups %} fullConfigGroup {% else %} partConfigGroup {% endif %})

    var popup_{{x._id}} = L.popup({"maxWidth": 650})
    var i_frame_{{x._id}} = `
        <u><b>SCHOOL INFORMATION</b></u><br>
        <b>Name:</b> {{x.school_name}} <br>
        <b>Electricity:</b> {{x.electricity}} Access<br>
        <b>Cellular Coverage:</b> 
        {% if x.available_coverage %}
        {% for i in x.available_coverage %}
        {{i}}   
        {% endfor %}
        {% else %}
        None
        {% endif %}
        
        <br><br>

        <u><b>RECOMMENDED CONNECTIVITY PARAMETERS</b></u><br>
        <b>Network Bandwidth:</b>
                            
        {% if not x.user_device_groups %} No user device groups configured
        {% else %} {{x.results.required_bandwidth}} Mbps
        {% endif %}
    
        <br> <br>

        {% if x.results %}
        <b>Middle Mile Technology and Projected Costs: </b> <br>
        
            <table style="width:100%">
                <tr>
                    <th rowspan='2' class="text-center">Technology</th>
                    <th colspan='2' class="text-center">Projected Costs</th>
                </tr>
                <tr>
                    <th class="text-center">TCO</th>
                    <th class="text-center">NPV</th>
                </tr>
                <tr>
                    <td> &nbsp {{x.results.middle_mile_technology_TCO.name}} &nbsp </td>
                    <td>  &nbsp<b>{{x.results.middle_mile_technology_TCO.TCO}} &nbsp</b> </td>
                    <td> &nbsp {{x.results.middle_mile_technology_TCO.NPV}} &nbsp </td>
                </tr>
                <tr>
                    <td> &nbsp {{x.results.middle_mile_technology_NPV.name}} &nbsp </td>
                    <td>  &nbsp{{x.results.middle_mile_technology_NPV.TCO}} &nbsp </td>
                    <td>  &nbsp <b>{{x.results.middle_mile_technology_NPV.NPV}} &nbsp</b> </td>
                </tr>
            </table>

         <br>

        <b>Last Mile Technology and Projected Costs: </b> <br><br>

        {% else %}
        <b>Middle Mile Technology and Projected Costs: </b> No user device groups have been configured <br>
         <br><br>

        <b>Last Mile Technology and Projected Costs: No user device groups have been configured</b> <br><br>
        {% endif %}
    `
    popup_{{x._id}}.setContent(i_frame_{{x._id}})
        
    school_{{x._id}}.bindPopup(popup_{{x._id}})

    school_{{x._id}}.bindTooltip(
        `<div> {{x.school_name}} </div>`,
        {"sticky": true}
    )

    {% endfor %}
    '''
    
    return start + middle + end

def addCoverageMap():
    # retrieve tower coordinates from spreadsheet
    df = pd.read_excel('./static/map/Tower_Data.xlsx')
    lst = []
    for i, row in df.iterrows():
        try:
            tower_latitude = row['Latitude N'].split('-')
            tower_longitude = row['Longitude W'].split('-') 
            
            tower_latitude = float(tower_latitude[0]) + float(tower_latitude[1])/60 + float(tower_latitude[2])/3600
            tower_longitude = -(float(tower_longitude[0]) + float(tower_longitude[1])/60 + float(tower_longitude[2])/3600)
        
            tower_latitude = float("{:.5f}".format(tower_latitude))
            tower_longitude = float("{:.5f}".format(tower_longitude))

            lst.append({'lat': tower_latitude, 'long':tower_longitude}) 
        
        except:
            print(f'Row {i} format is different')
            continue
    
    return lst