from flask import Blueprint, render_template, request, flash, jsonify
#from flask_login import login_required, current_user
#from .models import Note
#from . import db
import json
import os
import pandas as pd
import numpy as np
from datetime import datetime
import json
import io



views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
#@login_required
def home():
    return render_template('index.html', update_date = update_date, tables=[ex_erl_cmb.to_html(classes='data', header='true')],
                            table2=[ex_law_cmb.to_html(classes='data', header='true')]) #user=current_user)

APP_ROOT = os.path.dirname(os.path.abspath(__file__))

@views.route('/upload', methods= ['GET', 'POST'])
#@login_required
def upload():
    target1 =  os.path.join(APP_ROOT, 'pohistory/')
    target2 =  os.path.join(APP_ROOT, 'partmaster/')
    if request.method == 'POST':
        file = request.files['pohistory']
        file2= request.files['partmaster']
        #file3= request.files['carbon']
                    #fname = request.form.get('fname')
        if file:
            if not os.path.isdir(target1):
                os.mkdir(target1)
            new_fn = file.filename.split('.')[-1]
            filepath =   os.path.join(target1, 'costing' +'.'+ new_fn )
            file.save(filepath)
            flash('The file as been upploaded!', category = 'success' )
        if file2:
            if not os.path.isdir(target2):
                os.mkdir(target2)
            new_fn = file2.filename.split('.')[-1]
            filepath =   os.path.join(target2, 'master_raw-material_sku-info' +'.'+ new_fn )
            file2.save(filepath)
            flash('The file as been upploaded!', category = 'success' )

    return render_template('uploads.html') #user=current_user)

#### Reading the Po history excel and making df for time periods
rawbase_1 = pd.read_csv('program/pohistory/costing.csv', index_col='Date', parse_dates=True,
                       usecols=['Date','Item','Document Number','Quantity','Amount','Location'], engine='python')
rawbase_1 = rawbase_1.dropna()
rawbase_1= rawbase_1.sort_index(ascending=False)
update_date = pd.to_datetime(rawbase_1.index[0]).date()
curr_date = pd.to_datetime('today').date()
last30 = curr_date- pd.Timedelta(days=30)
previous30 = last30 - pd.Timedelta(days=30)
recent30df = rawbase_1.loc[curr_date: last30]
previous30df = rawbase_1.loc[last30: previous30]

#Grouping Time-sectioned df's by Item
f = {'Quantity': 'sum', 'Amount': 'sum'}
gp_previous30df = previous30df.groupby(['Item'], as_index=False).agg(f)
gp_recent30df= recent30df.groupby(['Item'], as_index=False).agg(f)

# reading the sku info file with wwights and other info for each part
rawskuinfo = pd.read_csv('program/partmaster/master_raw-material_sku-info.csv', index_col=None, usecols=['Item', 'Pounds Per Unit', 'Grade', 'Form', 'Units'], engine='python')

## Code for plate and sheet
shtpltinfo_1 = rawskuinfo[rawskuinfo['Form'].str.match('PLATE') | rawskuinfo['Form'].str.match('SHEET')]
shtpltinfo_2 = shtpltinfo_1[shtpltinfo_1['Grade'].str.match('304') | shtpltinfo_1['Grade'].str.match('316') | shtpltinfo_1['Grade'].str.match('303')]
recshtpltdf = pd.merge(shtpltinfo_2,gp_recent30df, on='Item', how='inner', validate="1:1")
preshtpltdf= pd.merge(shtpltinfo_2, gp_previous30df, on='Item', how='inner', validate="1:1")
#ss_flats_rec_df =recshtpltdf.dropna()
#ss_flats_pre_df = preshtpltdf.dropna()
recshtpltdf['TT Lbs'] = recshtpltdf['Pounds Per Unit'] * recshtpltdf['Quantity']
preshtpltdf['TT Lbs'] = preshtpltdf['Pounds Per Unit'] * preshtpltdf['Quantity']
rec_ppp_flats = round(recshtpltdf['Amount'].sum() /recshtpltdf['TT Lbs'].sum(),2)
pre_ppp_flats = round(preshtpltdf['Amount'].sum() /preshtpltdf['TT Lbs'].sum(),2)
tt_lbs_rec = round(recshtpltdf['TT Lbs'].sum(),2)
tt_lbs_pre = round(preshtpltdf['TT Lbs'].sum(),2)

def perc_change(val1,val2):
        #val1 is receny data / val2 is older data
        v2 =val1
        v1 =val2
        if v1 != 0:
            pct_chg = round(((v2-v1)/v1)*100,2)
        else:
            pct_chg = round(((v2-0.001)/0.001)*100,2)
        return pct_chg
price_per_chg = perc_change(rec_ppp_flats, pre_ppp_flats)
pounds_per_chg = perc_change(tt_lbs_rec,tt_lbs_pre)

## Code for rounds, flatbar, hex and square
roundinfo_1 = rawskuinfo[rawskuinfo['Form'].str.match('ROUND') | rawskuinfo['Form'].str.match('SQUARE')| rawskuinfo['Form'].str.match('FLATBAR')| rawskuinfo['Form'].str.match('HEX')]
roundinfo_2 = roundinfo_1[roundinfo_1['Grade'].str.match('304') | roundinfo_1['Grade'].str.match('316') | roundinfo_1['Grade'].str.match('303')| roundinfo_1['Grade'].str.match('416')]
roundinfo_3= roundinfo_2[roundinfo_2['Pounds Per Unit'] != 0]
rec_round_df = pd.merge(roundinfo_3,gp_recent30df, on='Item', how='inner', validate="1:1")
pre_round_df= pd.merge(roundinfo_3, gp_previous30df, on='Item', how='inner', validate="1:1")
rec_round_df['TT Lbs'] = rec_round_df['Pounds Per Unit'] * rec_round_df['Quantity']
pre_round_df['TT Lbs'] = pre_round_df['Pounds Per Unit'] * pre_round_df['Quantity']

rec_round_ppp = round(rec_round_df['Amount'].sum() /rec_round_df['TT Lbs'].sum(),2)
pre_round_ppp = round(pre_round_df['Amount'].sum() /pre_round_df['TT Lbs'].sum(),2)
tt_lbs_rec_rounds = round(rec_round_df['TT Lbs'].sum(),2)
tt_lbs_pre_rounds = round(pre_round_df['TT Lbs'].sum(),2)

round_ppp_per_chg= perc_change(rec_round_ppp,pre_round_ppp)
round_ttlbs_per_chg= perc_change(tt_lbs_rec_rounds, tt_lbs_pre_rounds)

###Code for  SS pipe and tube

tb_pp_ss_info_1 = rawskuinfo[rawskuinfo['Form'].str.match('TUBE') | rawskuinfo['Form'].str.match('PIPE')]
tb_pp_ss_info_2 = tb_pp_ss_info_1[tb_pp_ss_info_1['Grade'].str.match('304') | tb_pp_ss_info_1['Grade'].str.match('316') | tb_pp_ss_info_1['Grade'].str.match('303')| tb_pp_ss_info_1['Grade'].str.match('416')]
rec_tb_pp_df = pd.merge(tb_pp_ss_info_2,gp_recent30df, on='Item', how='inner', validate="1:1")
pre_tb_pp_df= pd.merge(tb_pp_ss_info_2, gp_previous30df, on='Item', how='inner', validate="1:1")
tb_rec_pp_avgperft = round(rec_tb_pp_df['Amount'].sum() /  rec_tb_pp_df['Quantity'].sum(),2)
tb_pre_pp_avgperft = round(pre_tb_pp_df['Amount'].sum() /  pre_tb_pp_df['Quantity'].sum(),2)
tt_rec_tb_pp =round(rec_tb_pp_df['Quantity'].sum(),2)
tt_pre_tb_pp = round(pre_tb_pp_df['Quantity'].sum(),2)
tb_cost_per_chg= perc_change(tb_rec_pp_avgperft,tb_pre_pp_avgperft)
tb_ttft_per_chg= perc_change(tt_rec_tb_pp,tt_pre_tb_pp)


## Code for Carbon Steel Products - Plate

cs_plt_info_1 = rawskuinfo[rawskuinfo['Form'].str.match('PLATE') | rawskuinfo['Form'].str.match('SHEET')]
cs_plt_info_2 = cs_plt_info_1[cs_plt_info_1['Grade'].str.match('CS')]
cs_plt_info_3= cs_plt_info_2[cs_plt_info_2['Pounds Per Unit'] != 0]
rec_plt_cs_df = pd.merge(cs_plt_info_3,gp_recent30df, on='Item', how='inner', validate="1:1")
pre_plt_cs_df= pd.merge(cs_plt_info_3, gp_previous30df, on='Item', how='inner', validate="1:1")

rec_plt_cs_df['TT Lbs'] = rec_plt_cs_df['Pounds Per Unit'] * rec_plt_cs_df['Quantity']
pre_plt_cs_df['TT Lbs']= pre_plt_cs_df['Pounds Per Unit'] * pre_plt_cs_df['Quantity']

rec_plt_cs_ppp = round(rec_plt_cs_df['Amount'].sum() /rec_plt_cs_df['TT Lbs'].sum(),2)
pre_plt_cs_ppp = round(pre_plt_cs_df['Amount'].sum() /pre_plt_cs_df['TT Lbs'].sum(),2)
tt_plt_lbs_rec_cs = round(rec_plt_cs_df['TT Lbs'].sum(),2)
tt_plt_lbs_pre_cs = round(pre_plt_cs_df['TT Lbs'].sum(),2)
#tt_plt_lbs_rec_cs = format(tt_plt_lbs_rec_cs,',.2f')

plt_per_cost_chg = perc_change(rec_plt_cs_ppp,pre_plt_cs_ppp)
plt_per_ttlbs_chg = perc_change(tt_plt_lbs_rec_cs, tt_plt_lbs_pre_cs)


##### CODE FOR HOME PAGE:

### Landing tables of esxpense summary by Expense account

rawbase_ex = pd.read_csv('pohistory/costing.csv', index_col='Date', parse_dates=True,
                       usecols=['Date','Expense/COGS Account','Amount','Location'], engine='python')
rawbase_ex = rawbase_ex.dropna()
rawbase_ex= rawbase_ex.sort_index(ascending=False)
law_rawbase_ex = rawbase_ex[rawbase_ex['Location']=='Texas (LV)']
erl_rawbase_ex = rawbase_ex[rawbase_ex['Location']!='Texas (LV)']
erl_recent30df_ex = erl_rawbase_ex.loc[curr_date: last30]
erl_previous30df_ex = erl_rawbase_ex.loc[last30: previous30]

law_recent30df_ex = law_rawbase_ex.loc[curr_date: last30]
law_previous30df_ex = law_rawbase_ex.loc[last30: previous30]

f = {'Amount': 'sum'}
ex_erl_gp_previous30df = erl_previous30df_ex.groupby(['Expense/COGS Account'], as_index=False).agg(f)
ex_erl_gp_recent30df= erl_recent30df_ex.groupby(['Expense/COGS Account'], as_index=False).agg(f)
ex_erl_gp_previous30df= ex_erl_gp_previous30df.sort_values(by='Amount', ascending=False, ignore_index=True)
ex_erl_gp_recent30df= ex_erl_gp_recent30df.sort_values(by='Amount', ascending=False, ignore_index=True)

ex_law_gp_previous30df = law_previous30df_ex.groupby(['Expense/COGS Account'], as_index=False).agg(f)
ex_law_gp_recent30df= law_recent30df_ex.groupby(['Expense/COGS Account'], as_index=False).agg(f)
ex_law_gp_recent30df= ex_law_gp_recent30df.sort_values(by='Amount', ascending=False, ignore_index=True)
ex_law_gp_previous30df= ex_law_gp_previous30df.sort_values(by='Amount', ascending=False, ignore_index=True)

#Combined tables for recent and past expenses

ex_erl_cmb = pd.merge(ex_erl_gp_recent30df, ex_erl_gp_previous30df, on='Expense/COGS Account', how='outer', validate='1:1')
ex_erl_cmb.fillna(0, inplace=True) # Could present and Atom isue
ex_erl_cmb.columns = ['Expense/COGS Account', 'Last 30 days (Recent)', 'Previous 30 Days (Older)']

ex_law_cmb = pd.merge(ex_law_gp_recent30df, ex_law_gp_previous30df, on='Expense/COGS Account', how='outer', validate='1:1')
ex_law_cmb.fillna(0, inplace=True)
ex_law_cmb.columns = ['Expense/COGS Account', 'Last 30 days (Recent)', 'Previous 30 Days (Older)']

ex_erl_cmb.index = ex_erl_cmb['Expense/COGS Account']
ex_law_cmb.index = ex_law_cmb['Expense/COGS Account']
ex_erl_cmb = ex_erl_cmb.drop(columns='Expense/COGS Account')
ex_law_cmb = ex_law_cmb.drop(columns='Expense/COGS Account')

##Adding a column with the percentage chagen between periods in the Expense Summary table

###Revised Formula of percetage change

def sum_perc_change(val1,val2):
    v2 =val1
    v1 =val2
        #val1 is receny data / val2 is older data
    pct_chg = round(((v2-v1)/v1)*100,2)
    return pct_chg


ex_erl_cmb['% Change Between Periods'] =sum_perc_change(ex_erl_cmb['Last 30 days (Recent)'],ex_erl_cmb['Previous 30 Days (Older)'])
ex_law_cmb['% Change Between Periods'] =sum_perc_change(ex_law_cmb['Last 30 days (Recent)'],ex_law_cmb['Previous 30 Days (Older)'])

##Formatting currency and percetage columns:

def currency(x):
    return "${:,.1f}".format(x)

def percent(x):
    return "{:.1f}%".format(x)

ex_erl_cmb['Last 30 days (Recent)'] =ex_erl_cmb['Last 30 days (Recent)'].apply(currency)
ex_erl_cmb['Previous 30 Days (Older)'] =ex_erl_cmb['Previous 30 Days (Older)'].apply(currency)
ex_erl_cmb['% Change Between Periods']= ex_erl_cmb['% Change Between Periods'].apply(percent)

ex_law_cmb['Last 30 days (Recent)'] =ex_law_cmb['Last 30 days (Recent)'].apply(currency)
ex_law_cmb['Previous 30 Days (Older)'] =ex_law_cmb['Previous 30 Days (Older)'].apply(currency)
ex_law_cmb['% Change Between Periods']= ex_law_cmb['% Change Between Periods'].apply(percent)


@views.route('/ssteel', methods=['GET','POST'])
def ssteel():
    return render_template('ssteel.html', pre_ppp_flats=pre_ppp_flats, rec_ppp_flats=rec_ppp_flats, tt_lbs_pre=tt_lbs_pre,
                                tt_lbs_rec=tt_lbs_rec, price_per_chg=price_per_chg, pounds_per_chg=pounds_per_chg,
                                rec_round_ppp=rec_round_ppp, tt_lbs_rec_rounds=tt_lbs_rec_rounds, tt_lbs_pre_rounds=tt_lbs_pre_rounds,
                                pre_round_ppp=pre_round_ppp, round_ppp_per_chg=round_ppp_per_chg, round_ttlbs_per_chg=round_ttlbs_per_chg,
                                tb_rec_pp_avgperft=tb_rec_pp_avgperft, tb_pre_pp_avgperft=tb_pre_pp_avgperft, tt_rec_tb_pp =tt_rec_tb_pp,
                                tt_pre_tb_pp=tt_pre_tb_pp, tb_cost_per_chg=tb_cost_per_chg, tb_ttft_per_chg=tb_ttft_per_chg)

@views.route('/cs', methods=['GET','POST'])
def cs():
    return render_template('cs.html', rec_plt_cs_ppp = rec_plt_cs_ppp, pre_plt_cs_ppp = pre_plt_cs_ppp,
                            tt_plt_lbs_rec_cs = tt_plt_lbs_rec_cs, tt_plt_lbs_pre_cs = tt_plt_lbs_pre_cs,
                            plt_per_cost_chg = plt_per_cost_chg, plt_per_ttlbs_chg=plt_per_ttlbs_chg)

@views.route('/shipping', methods=['GET','POST'])
def shipping():
    return render_template('shipping.html')

@views.route('/perishable', methods=['GET','POST'])
def perishable():
    return render_template('perishable.html')

@views.route('/shopsupplies', methods=['GET','POST'])
def shopsupplies():
    return render_template('shopsupplies.html')

@views.route('/other', methods=['GET','POST'])
def other():
    return render_template('other.html')
