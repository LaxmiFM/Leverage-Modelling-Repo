import pandas as pd
import numpy as np

from io import BytesIO
from flask import Flask, render_template, request, session, send_file, jsonify, redirect, url_for
from LeverageModellingFunctions import *
from flasgger import Swagger
from flasgger.utils import swag_from
import yearfrac as yf
from dash import Dash, dash_table, dcc, html, Input, Output, State, dependencies
import dash_bootstrap_components as dbc


def permittedTTMEBITDA_BZ(df_Portfolio1, df_Ebitda1, df_VAE1):
    EBITDA_Addback_1 = df_Ebitda1['EBITDA'].values[0]
    EBITDA_Addback_2 = df_Ebitda1['EBITDA'].values[1]
    EBITDA_Addback_3 = df_Ebitda1['EBITDA'].values[2]
    Add_Backs_10MM = df_Ebitda1['Permitted Add-Backs'].values[1]
    Add_Backs_10_50MM = df_Ebitda1['Permitted Add-Backs'].values[3]
    Add_Backs_50MM = df_Ebitda1['Permitted Add-Backs'].values[5]

    global df_newBorrowerPortfolio
    df_newBorrowerPortfolio = df_Portfolio1.tail(1)
    global df_newBorrowerVAE
    df_newBorrowerVAE = df_VAE1.tail(1)

    df_Portfolio1['Add Back Percentage'] = df_Portfolio1.apply(
        lambda x: Add_Back_Percentage(x['Adjusted TTM EBITDA_Initial'], x['EBITDA Addbacks']), axis=1)
    df_Portfolio1['Capped AddBack Percentage'] = df_Portfolio1.apply(
        lambda x: Capped_Addback_Percentage(x['Loan Type'], x['Rated B- or better'],
                                            x['Adjusted TTM EBITDA_Initial'],
                                            x['EBITDA Addbacks'],
                                            x['Initial Debt-to Cash Capitalization Ratio of Obligor'],
                                            EBITDA_Addback_3,
                                            EBITDA_Addback_1, Add_Backs_10MM, Add_Backs_10_50MM, Add_Backs_50MM),
        axis=1)

    df_Portfolio1['Excess Add-Backs'] = df_Portfolio1.apply(
        lambda x: Excess_AddBacks(x['Adjusted TTM EBITDA_Initial'], x['EBITDA Addbacks'], x['Add Back Percentage'],
                                  x['Capped AddBack Percentage']), axis=1)

    df_Portfolio1['Permitted TTM EBITDA'] = df_Portfolio1.apply(
        lambda x: Permitted_TTM_EBITDA(x['Adjusted TTM EBITDA_Initial'], x['Excess Add-Backs'],
                                       x['Agent Approved Add-Backs']), axis=1)

    df_Portfolio1['EBITDA Haircut'] = df_Portfolio1.apply(
        lambda x: EBITDA_Haircut(x['Permitted TTM EBITDA'], x['Adjusted TTM EBITDA_Initial']), axis=1)

    df_Portfolio1['Inclusion EBITDA Haircut'] = df_Portfolio1.apply(
        lambda x: Inclusion_EBITDA_Haircut(x['Borrower'], df_VAE1[df_VAE1['Borrower'] == x['Borrower']],
                                           x['EBITDA Haircut']), axis=1)

    df_Portfolio1['Permitted TTM EBITDA Current'] = df_Portfolio1.apply(
        lambda x: Permitted_TTM_EBITDA_Current(x['Agent Post-Inclusion Adj. Haircut'],
                                               x['Inclusion EBITDA Haircut'],
                                               x['Adjusted TTM EBITDA_Current'],
                                               x['Agent Adjusted Addback Haircut']),
        axis=1)
    return df_Portfolio1[['Borrower','Loan Type','Permitted TTM EBITDA Current']]



def permittedNetSeniorLeverage_CX(df_Portfolio1, df_Ebitda1, df_VAE1):
    df_Portfolio1['Permitted TTM EBITDA Current']=permittedTTMEBITDA_BZ(df_Portfolio1, df_Ebitda1, df_VAE1)['Permitted TTM EBITDA Current']
    df_Portfolio1['Permitted Net Senior Leverage'] = df_Portfolio1.apply(
        lambda x: Permitted_Net_senior_Leverage(x['Senior Debt'], x['Current Unrestricted Cash'],
                                                x['Permitted TTM EBITDA Current']), axis=1)
    return df_Portfolio1[['Borrower','Loan Type','Permitted Net Senior Leverage']]

def permittedNetTotalLeverage_CZ(df_Portfolio1, df_Ebitda1, df_VAE1):
    df_Portfolio1['Permitted TTM EBITDA Current'] = permittedTTMEBITDA_BZ(df_Portfolio1, df_Ebitda1, df_VAE1)['Permitted TTM EBITDA Current']
    df_Portfolio1['Permitted Net Total Leverage'] = df_Portfolio1.apply(
        lambda x: permittedNetTotalLeverage(x['Total Debt'], x['Current Unrestricted Cash'],
                                            x['Permitted TTM EBITDA Current']), axis=1)
    return df_Portfolio1[['Borrower','Loan Type','Permitted Net Total Leverage']]
