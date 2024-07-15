# INDRECT EMISSIONS MODEL
# by Jason Verrall 2024
# See `ReadMe.md` for details

import numpy as np  # np mean, np random
import pandas as pd  # read csv, df manipulation
import plotly.express as px  # interactive charts
import streamlit as st  # 🎈 data web app development
import common_functions as utils
from typing import Any
from datetime import datetime as dt

#  set up main page
st.set_page_config(
    page_title="Indirect Emissions Modeller",
    page_icon=":sun_with_face:",
    layout="wide",
)

# load cached variables to minimise processor time
@st.cache_data
def fn_DoDate():
    return dt.now().strftime('%d%b%Y')

DATE_TODAY = fn_DoDate()

# set up default RNG
@st.cache_resource
def fn_SetRng():
    return np.random.default_rng()

rng = fn_SetRng()

# load defaults
@st.cache_data
def fn_GetDefaultParams(parameter_filename: str = 'config.yml') -> dict:
    return utils.fn_LoadFile(parameter_filename)

params_d = fn_GetDefaultParams()

# get readme text for the bottom of the page
@st.cache_data
def fn_GetReadMeText(readme_filename: str = 'README.md') -> str:
    return utils.fn_LoadFile(readme_filename)

readme_text = fn_GetReadMeText()

#  set up button click callback
def fn_Refresher(placeholder_obj: Any, commit_obj: list = None):
    """
    Refresh the dashboard with updated values by committing changes to `st. session_state`.

    Parameters
    placeholder_obj: the sidebar object using for reporting the headline figures
    commit_obj: list of lists containing [sessionObjectName, newValue] to be committed to session_state

    Returns
    nothing
    """
    if commit_obj is not None:
        for sessionObj in commit_obj:
                st.session_state[sessionObj[0]] = sessionObj[1]

    with placeholder_obj.container(border=True):
        st.session_state['sessionEmissionsTotal'] = st.session_state['sessionEmissionsTransport'] + st.session_state['sessionEmissionsWfh']
        st.session_state['sessionLog'].append(
            [
                st.session_state.sessionFteTotal, 
                st.session_state.sessionDistanceTotal, 
                st.session_state.sessionEmissionsTransport, 
                st.session_state.sessionEmissionsWfh, 
                st.session_state.sessionEmissionsTotal, 
                ]
                )
        
        st.metric('Total FTE', st.session_state.sessionFteTotal, None)
        st.metric('Total distance (km)', f'{st.session_state.sessionDistanceTotal:.0f}', None)
        st.metric('Commute Emissions (tn CO2-e)', f'{st.session_state.sessionEmissionsTransport/1000:.1f}', None)
        st.metric('WFH Emissions (tn CO2-e)', f'{st.session_state.sessionEmissionsWfh/1000:.1f}', None)
        st.metric('Total Emissions (tn CO2-e)', f'{st.session_state.sessionEmissionsTotal/1000:.1f}', None)

        download_obj = pd.DataFrame(
            data=st.session_state.sessionLog[1:], 
            columns=st.session_state.sessionLog[0]
            ).to_csv().encode("utf-8")

        st.download_button('Download log', download_obj, file_name=f'Indirect Emissions Log {DATE_TODAY}.csv', mime="text/csv")
        # end 

# PAGE set up page content using Streamlit fragments
# set up forms for each main area of user input, so we can treat them as fragments and hence 
# not have everything refreshed each time the user clicks

# FORM - STAFF
@st.experimental_fragment
def fn_FormStaff():
    """
    Staff options page fragment. No parameters, no return.
    """
    st.header('Staffing options')
    # user-defined parameters
    cols11 = st.columns(2, vertical_alignment='center')
    total_staff_num = cols11[0].slider('Staff number', params_d['MinStaffNum'], params_d['MaxStaffNum'], params_d['DefaultStaffNum'])
    part_time_pct = cols11[0].slider('% of part-time workers', 0, 99, 25) / 100
    fteHoursPerWeek = cols11[0].slider('Full time hours/week', 30, 48, 35)
    daysHolidayPerYear = cols11[0].slider('Number of holiday days/yr excl public holidays', 20, 50, 25)
    absenceDaysPerYear = cols11[0].number_input('Mean other absence days/yr', min_value=0., max_value=10., step=0.5)

    # calculated parameters
    singleFtePerYear = (
        fteHoursPerWeek / params_d['MaxWorkDaysPerWeek']
        ) * (
            params_d['MaxWorkDaysPerYear'] - daysHolidayPerYear - absenceDaysPerYear
            )
    
    part_time_median = int(fteHoursPerWeek * 0.5)
    part_time_num = int(np.floor(total_staff_num * part_time_pct))
    full_time_num = total_staff_num - part_time_num
    # poisson is always positive but may exceed the working hours, so clip
    # part_time_group_r = rng.poisson(part_time_median, size=part_time_num *2) # oversample to make sure the group is big enough
    # part_time_group_r = [s for s in part_time_group_r if s >= params_d['MinHoursPerWeek'] and s < fteHoursPerWeek]
    # part_time_group = list(rng.choice(part_time_group_r, size=part_time_num, replace=False))

    # remove stochastic part to simplify
    part_time_group_lims = np.linspace(params_d['MinHoursPerWeek'], fteHoursPerWeek, num=5, endpoint=False)
    part_time_group = []
    for ix, ix2 in enumerate([0.1, 0.2, 0.4, 0.2]):
        part_time_group += [part_time_group_lims[ix] for y in range(int(part_time_num * ix2))]

    part_time_group += [part_time_group_lims[4] for y in range(part_time_num - len(part_time_group))]
    total_staff_group = [fteHoursPerWeek for i in range(full_time_num)] + part_time_group

    newFteTotal = np.round(sum(total_staff_group) / params_d['MaxHoursPerWeek'], 2) # sessionFteTotal
    newStaffTotal = total_staff_num # sessionStaffTotal
    newAbsenceRate = singleFtePerYear / ((fteHoursPerWeek / params_d['MaxWorkDaysPerWeek']) * params_d['MaxWorkDaysPerYear']) # sessionStaffAbsenceRate
    newTtlHrsPerYr = singleFtePerYear * newFteTotal # sessionStaffTotalHoursPerYear

    # display a graph of staffing and total FTE
    # then create a DF when it's committed
    # then save to session state
    fig = px.histogram(x=total_staff_group, histnorm='percent')
    fig.update_layout(yaxis_range=[0,100], xaxis_title="Hours per week")
    cols11[1].plotly_chart(fig, theme="streamlit")

    commit_l = [
        ['sessionFteTotal', newFteTotal],
        ['sessionStaffTotal', newStaffTotal],
        ['sessionStaffAbsenceRate', newAbsenceRate],
        ['sessionStaffTotalHoursPerYear', newTtlHrsPerYr]
    ]

    cols19 = st.columns(5, vertical_alignment='center')
    cols19[0].metric("Total FTE", f"{newFteTotal:.2f}", None)
    cols19[1].metric("Single FTE work hrs/yr", f"{singleFtePerYear:.2f}", None)
    cols19[2].metric("Total staff work hrs/yr", f"{newTtlHrsPerYr:.2f}", None)
    cols19[3].markdown("[Return to Top](#indirect-emissions-modeller)")
    if cols19[-1].button('Confirm', key='ConfirmStaff'):
        fn_Refresher(sidebar_ph, commit_l)

# FORM - COMMUTE OPTIONS
@st.experimental_fragment
def fn_FormCommute():
    """
    Commute options page fragment. No parameters, no return.
    """
    st.header('Commuting options')
    cols40 = st.columns(2, vertical_alignment='top')
    sliderDistance = cols40[0].slider('Staff travel distance range (km)', 1, 1000, (1, params_d['DefaultMaxStaffDistance']), key='sliderDistance')
    sliderOfficeVisits = cols40[0].slider('Office visits per month', 1, params_d['MaxVisitsPerMonth'], 4, key='sliderOfficeVisits')
    
    radioCloseFar_d = {'Very close':'VeryCloseList', 'Close':'CloseList', 'Far':'FarList', 'Medium': 'MediumList'}
    radioCloseFar = cols40[0].radio('Closeness to the office', options=[k for k in radioCloseFar_d.keys()], index=0, key='radioCloseFar')
    
    # calculated params
    distanceRange = max(sliderDistance) - min(sliderDistance)
    maxCommuteDistance = max(sliderDistance) * 4 

    # remove stochastic part to simplify
    # distanceMedian = min(sliderDistance) + (distanceRange * radioCloseFar_d[radioCloseFar])
    # distance_group_r = rng.gamma(distanceMedian, size=st.session_state.sessionStaffTotal *2)
    # distance_group_r = [s for s in distance_group_r if s >= min(sliderDistance) and s <= max(sliderDistance)]
    # distance_group = list(rng.choice(distance_group_r, size=st.session_state.sessionStaffTotal, replace=True))
        
    distance_group_lims = np.linspace(min(sliderDistance), max(sliderDistance) , num=20, endpoint=True)
    distance_group = []
    for ix, ix2 in enumerate(params_d[radioCloseFar_d[radioCloseFar]][:-2]):
        distance_group += [distance_group_lims[ix] for y in range(int(max(sliderDistance) * ix2))]

    distance_group += [distance_group_lims[-1] for y in range(st.session_state.sessionStaffTotal - len(distance_group))]
    
    distanceCommuteRaw = [d * 2 * sliderOfficeVisits for d in  distance_group]
    distanceCommute = [d if d < maxCommuteDistance else maxCommuteDistance for d in distanceCommuteRaw ]
    newOfficeRate = np.round(sliderOfficeVisits / params_d['MaxWorkDaysPerMonth'], 4) # sessionStaffOfficeRate
    newDistanceTotal = int(sum(distanceCommute)) # sessionDistanceTotal

    #display
    cols40[0].metric("Total distance", f"{newDistanceTotal} km", None)
    fig2 = px.histogram(x=distance_group, histnorm='percent')
    fig2.update_layout(xaxis_title="Distance from office (km)")
    cols40[1].plotly_chart(fig2, theme="streamlit")

    # set up commute options
    cols31 = st.columns([0.6, 0.4], vertical_alignment='center')
    # walk, car, public transport
    sliderTransMix = cols31[0].slider('Select %age mix between walk/cycle (left), car (middle range), and public transport (right)', 1, 100, (33,67))
    # bus or train
    sliderBusTrain = cols31[1].slider('Select %age mix between bus (left) and train (right)', 1, 100-max(sliderTransMix), int((100-max(sliderTransMix))/2))

    walk_pct = min(sliderTransMix)
    car_pct = max(sliderTransMix)-min(sliderTransMix)
    bus_pct = sliderBusTrain
    train_pct = int(100-max(sliderTransMix) - bus_pct)

    cols32 = st.columns(5, vertical_alignment='center')
    cols32[0].metric("Walk/cycle", f"{walk_pct}%", None)
    cols32[1].metric("Car", f"{car_pct}%", None)
    cols32[2].metric("Bus", f"{bus_pct}%", None)
    cols32[3].metric("Train", f"{train_pct}%", None)
    carFuelOptions = ['United Kingdom', 'England', 'South East', 'North East', 'North West', 'Northern Ireland', 'Scotland', 'South West', 'Wales']
    selectCarRegion = cols32[-1].selectbox('Region for car fuel', options=carFuelOptions, index=0) 

    #  assign transport and calculate emissions
    emissionsCar = st.session_state['sessionDistanceTotal'] * car_pct
    emissionsCarPetrol = emissionsCar * params_d[f'{selectCarRegion}_PetrolRatio']
    emissionsCarDiesel = emissionsCar - emissionsCarPetrol
    # assign car fuels
    newEmissionsTransport = sum(
        [
            emissionsCarPetrol * params_d['CarPetrolConvFactor'], 
            emissionsCarDiesel * params_d['CarDieselConvFactor'],
            st.session_state['sessionDistanceTotal'] * bus_pct * params_d['BusConvFactor'],
            st.session_state['sessionDistanceTotal'] * train_pct * params_d['TrainConvFactor'],
            ]
            ) # sessionEmissionsTransport
    
    commit_l = [
        ['sessionStaffOfficeRate', newOfficeRate],
        ['sessionDistanceTotal', newDistanceTotal],
        ['sessionEmissionsTransport', newEmissionsTransport],
    ]

    cols39 = st.columns(3, vertical_alignment='center')
    cols39[0].metric("Transport Emissions", f"{newEmissionsTransport/1000:.2f} tn-CO2e", None)
    cols39[1].markdown("[Return to Top](#indirect-emissions-modeller)")
    if cols39[-1].button('Confirm', key='ConfirmCommute'):
        fn_Refresher(sidebar_ph, commit_l)

# FORM - WFH OPTIONS
@st.experimental_fragment
def fn_FormWfh():
    """
    WFH options page fragment. No parameters, no return.
    """
    st.header('WFH options')
    # IT
    # user-defined params
    cols51 = st.columns(3, vertical_alignment='center')
    sliderLaptop = cols51[0].slider('% of staff with laptops', 0, 100, 75) / 100
    sliderPhone = cols51[1].slider('% of staff with mobile phones', 0, 100, 50) / 100 
    optionsMonitor = cols51[2].multiselect(
        "Monitor options",
        [k for k in params_d['ScreenOptions'].keys()],
        ['1 extra monitor']
    )
    
    #  calulated params
    wfhHours = st.session_state.sessionStaffTotalHoursPerYear * (1 - st.session_state.sessionStaffOfficeRate)
    numLaptop = int(np.floor(st.session_state.sessionStaffTotal * sliderLaptop))
    numDesktop = int(st.session_state.sessionStaffTotal - numLaptop)
    numPhone = int(np.floor(st.session_state.sessionStaffTotal * sliderPhone))

    #  allocate emissions 
    phoneGroupRaw = params_d['ItOptions']['mobile phone'] * numPhone
    computerGroupRaw = (wfhHours * sliderLaptop * params_d['ItOptions']['laptop'] ) + (
        wfhHours * (1-sliderLaptop) * params_d['ItOptions']['desktop + monitor']
    )
      
    monitorGroupRaw = 0

    if len(optionsMonitor) > 0:
        for this_option in optionsMonitor:
            opt_ttl = rng.integers(low=1, high=int(100/(len(optionsMonitor) + 1)))
            monitorGroupRaw += wfhHours * (opt_ttl / 100) * params_d['ScreenOptions'][this_option]
    # sessionEmissionsIt
    newEmissionsIt = sum(
        [
            computerGroupRaw,
            phoneGroupRaw, 
            monitorGroupRaw,
            ]
            ) * params_d['ElectricConvFactor']
    
    # lighting
    # st.session_state.sessionEmissionsLight
    newEmissionsLight = params_d['ElectricConvFactor'] * wfhHours * params_d['LightAllowance'] * 0.5 # lighting only on for 6 months of the year

    # Heating
    newEmissionsHeat = 0
    
    cols52 = st.columns(3, vertical_alignment='center')
    sliderHeatMonths = cols52[0].slider('Select no heating (left), winter heating (centre), whole year (right)', 0, 100, (30,80))
    sliderHeatHome = cols52[1].slider('Select workspace only (left), part of home (centre), whole home (right)', 0, 100, (30, 60))
    sliderHeatSharing = cols52[2].slider('% sharing with others', 0, 100, 33)

    # create an overall scalar for our total WFH hours, built on the various options
    #  first identify those who use heating
    numNonZeroHeat = int(st.session_state.sessionStaffTotal * (1-(min(sliderHeatMonths)/100))) # exclude people who don't use heating
    #  set up a list of scalars for 6 & 12 months of heating respectively (heating allowance is calculated for 6 months)
    heatMonthsRaw = [1 for x in range(max(sliderHeatMonths) - min(sliderHeatMonths))] + [2 for x in range(100-max(sliderHeatMonths))]
    heatMonthsRaw = rng.choice(heatMonthsRaw, size=numNonZeroHeat, replace=True) # randomise to size of our set
    # now randomly assign the extent of heating
    heatHomeRaw = rng.choice(
        [0.25, 0.5, 1], 
        size = numNonZeroHeat, 
        p = [
            min(sliderHeatHome) / 100, # workspace only
            (max(sliderHeatHome) - min(sliderHeatHome)) / 100, # part of home
            (100-max(sliderHeatHome)) / 100 # whole home
        ]
        )

    # now randomly assign sharing
    heatShareRaw = rng.choice(
            [0.5, 1], 
            size = numNonZeroHeat, 
            p = [
                sliderHeatSharing / 100, # sharing
                (100-sliderHeatSharing) / 100 # no sharing
            ]
            )

    # now multiply all scalars 
    heatGroup = [
        i * j * k for i, j, k in zip(heatMonthsRaw, heatHomeRaw, heatShareRaw)
        ] 

    # now normalise our heating group and convert to kWh gas / yr
    newEmissionsHeat = (
        sum(heatGroup) / st.session_state.sessionStaffTotal 
        ) * wfhHours * params_d['HeatAllowance'] * params_d['HeatConvFactor'] # sessionEmissionsHeat
    
    newEmissionsWfh = sum(
        [
            newEmissionsIt,
            newEmissionsLight,
            newEmissionsHeat
        ], 
        ) # sessionEmissionsWfh
    
    commit_l = [
        ['sessionEmissionsLight', newEmissionsLight],
        ['sessionEmissionsIt', newEmissionsIt],
        ['sessionEmissionsHeat', newEmissionsHeat],
        ['sessionEmissionsWfh', newEmissionsWfh]
    ]

    cols59 = st.columns(6, vertical_alignment='center')
    cols59[0].metric("IT Emissions (tn-CO2e)", f"{newEmissionsIt/1000:.3f}", None)
    cols59[1].metric("Light Emissions (tn-CO2e)", f"{newEmissionsLight/1000:.3f}", None)
    cols59[2].metric("Heat Emissions (tn-CO2e)", f"{newEmissionsHeat/1000:.3f}", None)
    cols59[3].metric("WFH Emissions (tn-CO2e)", f"{newEmissionsWfh/1000:.3f}", None)
    cols59[4].markdown("[Return to Top](#indirect-emissions-modeller)")
    if cols59[-1].button('Confirm', key='ConfirmWfh'):
        fn_Refresher(sidebar_ph, commit_l)

# initiate session vars
for k,v in params_d['SessionDefaults'].items():
    if k not in st.session_state:
        st.session_state[k] = v

# calc'd session vars
if 'sessionLog' not in st.session_state:
    st.session_state['sessionLog'] = ['TotalFte TotalDistance TotalEmissionsCommute TotalEmissionsWfh TotalEmissions'.split()]

if 'sessionStaffAbsenceRate' not in st.session_state:
    st.session_state['sessionStaffAbsenceRate'] = (params_d['MaxWorkDaysPerYear'] - params_d['DefaultAbsencePerYear']) / params_d['MaxWorkDaysPerYear']

if 'sessionStaffOfficeRate' not in st.session_state:
    st.session_state['sessionStaffOfficeRate'] = 4 / params_d['MaxWorkDaysPerMonth']

if 'sessionStaffTotalHoursPerYear' not in st.session_state:
    st.session_state['sessionStaffTotalHoursPerYear'] = params_d['MaxWorkDaysPerYear'] * (1 - st.session_state['sessionStaffAbsenceRate']) * (params_d['MaxHoursPerWeek'] / 5)

# set up sidebar
with st.sidebar.container(border=True):
    st.markdown("[Staffing options](#staffing-options)")
    st.markdown("[Staff home distance options](#staff-home-distance-options)")
    st.markdown('[Commuting options](#commuting-options)')
    st.markdown('[WFH options](#wfh-options)')
    st.markdown('[ReadMe](#readme)')
    sidebar_ph = st.sidebar.empty() # placeholder for dashboard

# describe main page
st.title('Indirect Emissions Modeller')

with st.container(border=True):
    cols01 = st.columns(4, vertical_alignment='center')
    cols01[0].markdown("[Staffing options](#staffing-options)")
    cols01[1].markdown('[Commuting options](#commuting-options)')
    cols01[2].markdown('[WFH options](#wfh-options)')
    cols01[-1].markdown('[ReadMe](#readme)')

with st.container(border=True):
    fn_FormStaff()

with st.container(border=True):
    fn_FormCommute()

with st.container(border=True):
    fn_FormWfh()

with st.container(border=True):
    st.subheader('ReadMe')
    st.markdown(readme_text)