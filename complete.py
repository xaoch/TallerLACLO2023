import streamlit as st
import pandas as pd

#Open the Data
schoolData = pd.read_csv("data/schoolData.csv")
frpl = pd.read_csv("data/frpl.csv")

#Cleaning School Data
#Only keep those rows in which school_name contains total
mask = schoolData["school_name"].str.contains('Total')
schoolData=schoolData[mask]

#Change the school_name to remove the "Total"
schoolData["school_name"]=schoolData["school_name"].str.replace(" Total","")

#Remove this columns  "school_group", "grade", "pi_pct" and "blank_col"
schoolData=schoolData.drop(columns=["school_group","grade","pi_pct","blank_col"])

#Remove the school name "Grand" because it was "Grand Total"
mask = schoolData["school_name"]!="Grand"
schoolData=schoolData[mask]

#Remove the percentage from the percentage columns
def removePercentageSign(dataframe,column_name):
    dataframe[column_name]=dataframe[column_name].str.replace("%","")

removePercentageSign(schoolData,"na_pct")
removePercentageSign(schoolData,"aa_pct")
removePercentageSign(schoolData,"as_pct")
removePercentageSign(schoolData,"hi_pct")
removePercentageSign(schoolData,"wh_pct")

#Clean Free Lunch
#Remove rows without school name
frpl = frpl.dropna(subset=["school_name"])

#Remove school names that have "ELM K_08", "Mid Schl", "High Schl", "Alt HS", "Spec Ed Total", "Cont Alt Total", "Hospital Sites Total", "Dist Total"
mask = ~(frpl["school_name"].isin(["ELM K_08", "Mid Schl", "High Schl", "Alt HS", "Spec Ed Total", "Cont Alt Total", "Hospital Sites Total", "Dist Total"]))
frpl = frpl[mask]

#Remove the percentage on the percentage column
removePercentageSign(frpl,"frpl_pct")

# Data Wrangling First Part
## Joining datasets
schoolData=schoolData.merge(frpl, on='school_name', how='left')

## Convert percentages to Numerica
schoolData["na_pct"]=pd.to_numeric(schoolData["na_pct"])
schoolData["aa_pct"]=pd.to_numeric(schoolData["aa_pct"])
schoolData["as_pct"]=pd.to_numeric(schoolData["as_pct"])
schoolData["hi_pct"]=pd.to_numeric(schoolData["hi_pct"])
schoolData["wh_pct"]=pd.to_numeric(schoolData["wh_pct"])
schoolData["frpl_pct"]=pd.to_numeric(schoolData["frpl_pct"])

## Calculating high poverty
schoolData["high_poverty"] = schoolData["frpl_pct"]>75


# Controls and Data Selection
st.set_page_config(layout="wide")
st.title("School Data")
st.sidebar.title("Visualizations")
visualization = st.sidebar.radio(
    "What visualization do you want to see?",
    options=['Race/Ethnicity in the District', 'Percentage Poverty', "Race/Ethnicity in High Poverty Schools"])

size= st.sidebar.slider(
    'Only considers schools with this size:',
    min_value=int(schoolData["tot"].min()),
    max_value=int(schoolData["tot"].max()),
    value=(int(schoolData["tot"].min()), int(schoolData["tot"].max())))

mask=schoolData["tot"].between(size[0],size[1])
schoolData=schoolData[mask]

schools= st.sidebar.multiselect(
    'What schools do you want to include',
    options=schoolData["school_name"].unique(),
    default=schoolData["school_name"].unique())

mask=schoolData["school_name"].isin(schools)
schoolData=schoolData[mask]


# Data Wrangling Second Part
## Create a Wide version
schoolData_wide = schoolData.melt(
    id_vars=['school_name', 'high_poverty'], # column that uniquely identifies a row (can be multiple)
    value_vars=['na_num','aa_num','as_num','hi_num','wh_num'],
    var_name='race_ethnicity', # name for the new column created by melting
    value_name='population' # name for new column containing values from melted columns
)

## Change the codes to names
schoolData_wide["race_ethnicity"]= schoolData_wide["race_ethnicity"].replace({ 'aa_num' : "African American",
                                                                               'as_num' : "Asian American",
                                                                               'na_num' : "Native American",
                                                                               'hi_num' : "Hispanic",
                                                                               'wh_num' : "White"})

##
schoolData_totals = schoolData_wide.groupby("race_ethnicity").sum()


import plotly.express as px

## Race/Ethnicity per District
if (visualization=="Race/Ethnicity in the District"):
    col1, col2= st.columns(2)

    with col1:
        fig = px.pie(schoolData_wide, values='population', names='race_ethnicity',
                     title='Percentages of Population per Race/Ethnicity')
        st.plotly_chart(fig)

    with col2:
        fig2 = px.histogram(schoolData_wide, x="race_ethnicity", y='population',
                      title="Population per Race/Ethnicity")
        st.plotly_chart(fig2)

## Percentage Poverty
if (visualization=="Percentage Poverty"):
    fig = px.pie(schoolData_wide, names='high_poverty', title='Percentage of Schools in Poverty', hole=0.5)
    st.plotly_chart(fig)

## Population Division per Poverty Level
if (visualization=="Race/Ethnicity in High Poverty Schools"):
    fig = px.pie(schoolData_wide, values='population', names='race_ethnicity', facet_col="high_poverty",
                 title='Percentages of Population per Race/Ethnicity', width=1200)
    st.plotly_chart(fig)
