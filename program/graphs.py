from flask import Blueprint, render_template, request, flash, jsonify
import json
import os
import pandas as pd
import numpy as np
from datetime import datetime
import json
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
import base64

graphs = Blueprint('graphs', __name__)
@graphs.route('/', methods=['GET', 'POST'])


###Ploting function for steinless steel flats
@graphs.route('/visualsspltsht', methods=['GET', 'POST'])
def plot():
    img = BytesIO()
    y = plot_ss_price['Price Per Lb.'].values
    #x = [1,2,3,4,5,6,7,8,9,10,11,12]

    plt.plot(y)
    plt.ylabel("Price per pound$", fontsize=18, color="blue")
    plt.xlabel('Months: Recent <----> Older')
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')

    return render_template('plot.html', plot_url=plot_url)

###Ploting function for carbon steel flats
@graphs.route('/visualcspltsht', methods=['GET', 'POST'])
def cs_plot():
    img = BytesIO()
    y = plot_cs_price['Price Per Lb.'].values
    #x = [1,2,3,4,5,6,7,8,9,10,11,12]

    plt.plot(y)
    plt.ylabel("Price per pound$", fontsize=18, color="blue")
    plt.xlabel('Months: Recent <----> Older')
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)
    cs_plot_url = base64.b64encode(img.getvalue()).decode('utf8')

    return render_template('plotcs.html', cs_plot_url=cs_plot_url)

#### Reading the Po history excel and making df for time periods
rawbase_1 = pd.read_csv('pohistory/costing.csv', index_col='Date', parse_dates=True,
                       usecols=['Date','Item','Document Number','Quantity','Amount','Location'], engine='python')
rawbase_1 = rawbase_1.dropna()
rawbase_1= rawbase_1.sort_index(ascending=False)

# reading the sku info file with wwights and other info for each part STEINLESS FLATS

rawskuinfo = pd.read_csv('pohistory/master_raw-material_sku-info.csv', index_col=None, usecols=['Item', 'Pounds Per Unit', 'Grade', 'Form', 'Units'], engine='python')
shtpltinfo_1 = rawskuinfo[rawskuinfo['Form'].str.match('PLATE') | rawskuinfo['Form'].str.match('SHEET')]
shtpltinfo_2 = shtpltinfo_1[shtpltinfo_1['Grade'].str.match('304') | shtpltinfo_1['Grade'].str.match('316') | shtpltinfo_1['Grade'].str.match('303')]
curr_date = pd.to_datetime('today').date()

def yearly_avg():
    year_mo_tt_sslbs_flats =[]
    year_mo_avg_ss_flats =[]
    curr_date = pd.to_datetime('today').date()

    for month in range(1,13):

        last30 = curr_date- pd.Timedelta(days=30)
        recent30df = rawbase_1.loc[curr_date: last30]
        #Grouping Time-sectioned df's by Item
        f = {'Quantity': 'sum', 'Amount': 'sum'}
        gp_recent30df= recent30df.groupby(['Item'], as_index=False).agg(f)

        # Code for the Plate and Sheet
        recshtpltdf = pd.merge(shtpltinfo_2,gp_recent30df, on='Item', how='inner', validate="1:1")
        recshtpltdf['TT Lbs'] = recshtpltdf['Pounds Per Unit'] * recshtpltdf['Quantity']
        rec_ppp_flats = round(recshtpltdf['Amount'].sum() /recshtpltdf['TT Lbs'].sum(),2)
        tt_lbs_rec = round(recshtpltdf['TT Lbs'].sum(),2)
        year_mo_avg_ss_flats.append(rec_ppp_flats)
        year_mo_tt_sslbs_flats.append(tt_lbs_rec)
        curr_date = pd.to_datetime('today').date()- pd.Timedelta(days=30*month)
    return year_mo_tt_sslbs_flats, year_mo_avg_ss_flats

plot_ss_lbs,plot_ss_price = yearly_avg()
plot_ss_price = pd.DataFrame(data = plot_ss_price)
plot_ss_lbs = pd.DataFrame(data = plot_ss_lbs)
plot_ss_lbs.columns = ['Total Lbs. Purchased']
plot_ss_price.columns = ['Price Per Lb.']

# reading the sku info file with wwights and other info for each part CARBON STEEL FLATS


cs_info_1 = rawskuinfo[rawskuinfo['Form'].str.match('SHEET')| rawskuinfo['Form'].str.match('PLATE')]
cs_info_2 = cs_info_1[cs_info_1['Grade'].str.match('CS')]
cs_info_3= cs_info_2[cs_info_2['Pounds Per Unit'] != 0]

curr_date = pd.to_datetime('today').date()


def cs_yearly_avg():
    ###Function to agreggate monthly totals and iterate to make a df with each month's value
    #### This one is for SS flats (plate and sheet)
    year_mo_tt_cslbs_flats =[]
    year_mo_avg_cs_flats =[]
    curr_date = pd.to_datetime('today').date()

    for month in range(1,13):

        last30 = curr_date- pd.Timedelta(days=30)
        recent30df = rawbase_1.loc[curr_date: last30]
        #Grouping Time-sectioned df's by Item
        f = {'Quantity': 'sum', 'Amount': 'sum'}
        gp_recent30df= recent30df.groupby(['Item'], as_index=False).agg(f)

        # Code for the Plate and Sheet
        rec_cs_df = pd.merge(cs_info_3,gp_recent30df, on='Item', how='inner', validate="1:1")
        rec_cs_df['TT Lbs'] = rec_cs_df['Pounds Per Unit'] * rec_cs_df['Quantity']
        rec_cs_ppp = round(rec_cs_df['Amount'].sum() /rec_cs_df['TT Lbs'].sum(),2)
        #recshtpltdf = pd.merge(shtpltinfo_2,gp_recent30df, on='Item', how='inner', validate="1:1")
        #recshtpltdf['TT Lbs'] = recshtpltdf['Pounds Per Unit'] * recshtpltdf['Quantity']
        #rec_ppp_flats = round(recshtpltdf['Amount'].sum() /recshtpltdf['TT Lbs'].sum(),2)
        tt_lbs_rec = round(rec_cs_df['TT Lbs'].sum(),2)
        year_mo_avg_cs_flats.append(rec_cs_ppp)
        year_mo_tt_cslbs_flats.append(tt_lbs_rec)
        curr_date = pd.to_datetime('today').date()- pd.Timedelta(days=30*month)
    return year_mo_tt_cslbs_flats, year_mo_avg_cs_flats

plot_cs_lbs,plot_cs_price = cs_yearly_avg()
plot_cs_price = pd.DataFrame(data = plot_cs_price)
plot_cs_lbs = pd.DataFrame(data = plot_ss_lbs)
plot_cs_lbs.columns = ['Total Lbs. Purchased']
plot_cs_price.columns = ['Price Per Lb.']













#ax1 = plot_ss_price.plot()


#ax1.plot(plot_ss_price, lw=2, color="blue")
#ax1.set_ylabel(r"Price per pound$", fontsize=18, color="blue")
#for label in ax1.get_yticklabels():
#    label.set_color("blue")
