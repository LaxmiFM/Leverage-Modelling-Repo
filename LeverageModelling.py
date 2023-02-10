import pandas as pd
import numpy as np
from datetime import date
from io import BytesIO
from flask import Flask, render_template, request, session, send_file, jsonify, redirect, url_for
from LeverageModellingFunctions import *
from flasgger import Swagger
from flasgger.utils import swag_from
import yearfrac as yf
from dash import Dash, dash_table, dcc, html, Input, Output, State, dependencies
import dash_bootstrap_components as dbc

server = Flask(__name__, template_folder='template')

app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP], server=server, routes_pathname_prefix="/dash/")

app.layout = html.Div("This is the Dash app.")


# def update_output(clicks, input_value):
#     if clicks is not None:
#         print(clicks, input_value)

def calculateAvailability(df_Portfolio1, df_Tiers1, df_Ebitda1, df_VAE1, df_Availability1, df_ExcessConcentration1,
                          df_Industries1, df_BorrowerOutstandings1):
    measurement_date = df_Availability1['Value'].iloc[0]
    Tier_1_1L = df_Tiers1['First Lien Loans'].values[0]
    Tier_2_1L = df_Tiers1['First Lien Loans'].values[1]
    Tier_3_1L = df_Tiers1['First Lien Loans'].values[2]
    Tier_1_2L = df_Tiers1['FLLO/2nd Lien Loans'].values[0]
    Tier_2_2L = df_Tiers1['FLLO/2nd Lien Loans'].values[1]
    Tier_3_2L = df_Tiers1['FLLO/2nd Lien Loans'].values[2]
    Tier_1_ApplicableValue = df_Tiers1['Applicable Collateral Value'].values[0]
    Tier_2_ApplicableValue = df_Tiers1['Applicable Collateral Value'].values[1]
    Tier_3_ApplicableValue = df_Tiers1['Applicable Collateral Value'].values[2]
    EBITDA_Addback_1 = df_Ebitda1['EBITDA'].values[0]
    EBITDA_Addback_2 = df_Ebitda1['EBITDA'].values[1]
    EBITDA_Addback_3 = df_Ebitda1['EBITDA'].values[2]
    Add_Backs_10MM = df_Ebitda1['Permitted Add-Backs'].values[1]
    Add_Backs_10_50MM = df_Ebitda1['Permitted Add-Backs'].values[3]
    Add_Backs_50MM = df_Ebitda1['Permitted Add-Backs'].values[5]
    Tier_1_RR = df_Tiers1['Recurring Revenue'].values[0]
    Tier_2_RR = df_Tiers1['Recurring Revenue'].values[1]
    Tier_3_RR = df_Tiers1['Recurring Revenue'].values[2]
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

    df_Portfolio1['Permitted Net Senior Leverage'] = df_Portfolio1.apply(
        lambda x: Permitted_Net_senior_Leverage(x['Senior Debt'], x['Current Unrestricted Cash'],
                                                x['Permitted TTM EBITDA Current']), axis=1)

    df_Portfolio1['Amounts in excess of Tier 3 Reclassified as zero value'] = df_Portfolio1.apply(
        lambda x: Amounts_in_excess_of_Tier_3(x['Loan Type'], x['Permitted Net Senior Leverage'],
                                              x['Borrower Outstanding Principal Balance'], Tier_3_2L), axis=1)

    df_Portfolio1['Amounts in excess of Tier 3 Reclassified as 2nd Lien'] = df_Portfolio1.apply(
        lambda x: Amounts_excess_of_Tier3_Reclassified_2nd_Lien(x['Loan Type'], x[
            'Amounts in excess of Tier 3 Reclassified as zero value'], x['Permitted Net Senior Leverage'],
                                                                x['Borrower Outstanding Principal Balance'],
                                                                Tier_3_1L),
        axis=1)

    df_Portfolio1['First Lien Amount'] = df_Portfolio1.apply(
        lambda x: First_Lien_Amount(x['Loan Type'], x['Borrower Outstanding Principal Balance'],
                                    x['Amounts in excess of Tier 3 Reclassified as 2nd Lien'],
                                    x['Amounts in excess of Tier 3 Reclassified as zero value']), axis=1)

    df_Portfolio1['EBITDA > $5MM'] = df_Portfolio1.apply(lambda x: EBITDA_5MM(x['Permitted TTM EBITDA']), axis=1)

    df_Portfolio1['Second Lien or FLLO EBITDA >$10MM'] = df_Portfolio1.apply(
        lambda x: Second_Lien_Or_FLLO_EBITDA(x['Loan Type'], x['Permitted TTM EBITDA']), axis=1)

    df_Portfolio1['Eligible Cov-Lite'] = df_Portfolio1.apply(
        lambda x: Eligible_Cov_Lite(x['Cov-Lite?'], x['Permitted TTM EBITDA'], x['Initial Senior Debt'],
                                    x['Rated B- or better']), axis=1)

    df_Portfolio1['Eligible Recurring Revenue'] = df_Portfolio1.apply(
        lambda x: Eligible_recurring_revenue(x['Loan Type'], x['Initial Recurring Revenue'],
                                             x['Initial Total Debt']),
        axis=1)

    df_Portfolio1['Eligibility Check'] = df_Portfolio1.apply(
        lambda x: Eligibility_Check(x['Eligible Loan'], x['EBITDA > $5MM'], x['Second Lien or FLLO EBITDA >$10MM'],
                                    x['Eligible Cov-Lite'], x['Eligible Recurring Revenue'],
                                    x['Permitted TTM EBITDA Current']), axis=1)

    df_Portfolio1['Permitted Net Total Leverage'] = df_Portfolio1.apply(
        lambda x: permittedNetTotalLeverage(x['Total Debt'], x['Current Unrestricted Cash'],
                                            x['Permitted TTM EBITDA Current']), axis=1)

    df_Portfolio1['Current Multiple'] = df_Portfolio1.apply(
        lambda x: currentMultiple(x['Loan Type'], x['Total Debt'], x['Current Recurring Revenue']), axis=1)

    df_Portfolio1['Applicable Collateral Value'] = df_Portfolio1.apply(
        lambda x: applicableCollateralValue(x['Eligibility Check'], x['Loan Type'],
                                            x['Permitted Net Senior Leverage'], x['Permitted Net Total Leverage'],
                                            x['Current Multiple'], Tier_1_1L, Tier_1_ApplicableValue, Tier_2_1L,
                                            Tier_2_ApplicableValue, Tier_3_ApplicableValue, Tier_1_2L, Tier_2_2L,
                                            Tier_1_RR, Tier_2_RR), axis=1)

    df_Portfolio1['VAE'], df_Portfolio1['Event Type'], df_Portfolio1['VAE Effective Date'], df_Portfolio1[
        'Agent Assigned Value'] = zip(*df_Portfolio1.apply(
        lambda x: funcVAE(df_VAE1[df_VAE1['Borrower'] == x['Borrower']], measurement_date),
        axis=1))

    df_Portfolio1['Assigned Value'] = df_Portfolio1.apply(
        lambda x: assignedValues(x['VAE'], x['Actual Purchase Price'], x['Agent Assigned Value'],
                                 x['Applicable Collateral Value']), axis=1)

    df_Portfolio1['First Lien Value'] = df_Portfolio1.apply(
        lambda x: firstLienValue(x['Assigned Value'], x['First Lien Amount']), axis=1)

    df_Portfolio1['Second Lien Value'] = df_Portfolio1.apply(
        lambda x: secondLienValue(x['Amounts in excess of Tier 3 Reclassified as 2nd Lien'], x['Assigned Value']),
        axis=1)

    df_Portfolio1['Amounts in excess of Tier 3 Reclassified as zero valueZ'] = df_Portfolio1.apply(
        lambda x: amountExcessTier3ReclassifiedZeroValue(x['Loan Type'],
                                                         x['Borrower Outstanding Principal Balance'],
                                                         x['Permitted Net Total Leverage'], Tier_3_2L), axis=1)

    df_Portfolio1['Last Out or 2nd Lien Amount'] = df_Portfolio1.apply(
        lambda x: lastOutorSecondLienAmount(x['Loan Type'], x['Borrower Outstanding Principal Balance'],
                                            x['Amounts in excess of Tier 3 Reclassified as zero valueZ']), axis=1)

    df_Portfolio1['FLLO Value'] = df_Portfolio1.apply(
        lambda x: FLLOValue(['Loan Type'], x['Last Out or 2nd Lien Amount'], x['Assigned Value']), axis=1)

    df_Portfolio1['Second Lien ValueAC'] = df_Portfolio1.apply(
        lambda x: secondLienValueAC(x['Loan Type'], x['Last Out or 2nd Lien Amount'], x['Assigned Value']), axis=1)

    df_Portfolio1['Amounts in excess of 2.5x RR Multiple Reclassified as zero value'] = df_Portfolio1.apply(
        lambda x: amountsExcess25RRMultipleReclassifiedZero(x['Loan Type'], x['Current Multiple'],
                                                            x['Borrower Outstanding Principal Balance'], Tier_3_RR),
        axis=1)

    df_Portfolio1['Recurring Revenue Amount'] = df_Portfolio1.apply(
        lambda x: recurringRevenueAmount(x['Loan Type'], x['Borrower Outstanding Principal Balance'],
                                         x['Amounts in excess of 2.5x RR Multiple Reclassified as zero value']),
        axis=1)

    df_Portfolio1['Recurring Revenue Value'] = df_Portfolio1.apply(
        lambda x: recurringRevenueValue(x['Loan Type'], x['Recurring Revenue Amount'], x['Assigned Value']), axis=1)

    df_Portfolio1['Adjusted Borrowing Value'] = df_Portfolio1.apply(
        lambda x: adjustedBorrowingValue(x['First Lien Value'], x['Second Lien Value'], x['FLLO Value'],
                                         x['Second Lien ValueAC'], x['Recurring Revenue Value']), axis=1)

    # Output Adjusted Borrowing values
    Adjusted_Borrowing_Value_for_Eligible_Loans = df_Portfolio1['Adjusted Borrowing Value'].sum()
    # df_Portfolio1.to_excel('OutputAdjustedBorrowing.xlsx', index=False)

    global df_AdjustedIntermediate
    df_AdjustedIntermediate = df_Portfolio1[
        ['First Lien Value', 'Second Lien Value', 'FLLO Value', 'Second Lien ValueAC', 'Recurring Revenue Value',
         'Recurring Revenue Amount', 'Amounts in excess of Tier 3 Reclassified as 2nd Lien',
         'Assigned Value', 'Applicable Collateral Value', 'Current Multiple', 'Permitted Net Total Leverage',
         'Permitted Net Senior Leverage', 'Permitted TTM EBITDA', 'Permitted TTM EBITDA Current',
         'Excess Add-Backs', 'Capped AddBack Percentage', 'Add Back Percentage', 'Adjusted Borrowing Value']]

    try:
        df_Portfolio1['Adjusted Borrowing Value_DW'] = df_Portfolio1['Adjusted Borrowing Value']
    except:
        df_Portfolio1['Adjusted Borrowing Value_DW'] = 0

    # Calculating Obligor for (a) First Lien Last Out, Second Lien Loan, EBITDA <$10MM not in Top Three Obligors
    df_Portfolio1['Obligor_DY'] = df_Portfolio1.groupby('Borrower')['Adjusted Borrowing Value_DW'].transform('sum')

    # Remove dupes DZ
    df_Portfolio1['Remove Dupes'] = df_Portfolio1['Obligor_DY']
    is_duplicate = df_Portfolio1['Borrower'].duplicated(keep='first')
    df_Portfolio1['Remove Dupes'] = df_Portfolio1['Obligor_DY'].where(~is_duplicate, 0)

    # Rank column to be used as a reference for other rank coulmns
    df_Portfolio1['rank'] = df_Portfolio1['Remove Dupes'].rank(ascending=False, method='first')
    df_Portfolio1['Rank_EB'] = df_Portfolio1.apply(
        lambda x: rankEB(x['Remove Dupes'], x['rank'],
                         df_Portfolio1[df_Portfolio1['Remove Dupes'] == x['Remove Dupes']]),
        axis=1)

    # Rank EA
    # =IFERROR(INDEX(EB:EB,MATCH(A11,A:A,0)),0)
    df_Portfolio1['Rank_EA'] = df_Portfolio1.apply(
        lambda x: df_Portfolio1[df_Portfolio1['Borrower'] == x['Borrower']]['Rank_EB'].max(), axis=1)

    df_Portfolio1['Advance Rate Class'] = df_Portfolio1.apply(
        lambda x: advanceRateClass(x['Permitted TTM EBITDA Current'], x['Rated B- or better']), axis=1)

    df_Portfolio1['Advance Rate Definition'] = df_Portfolio1.apply(
        lambda x: advanceRateDefinition(x['Borrower'], x['Loan Type'], x['Advance Rate Class']), axis=1)

    df_Portfolio1['Qualifies?'] = df_Portfolio1.apply(
        lambda x: qualifies(x['Loan Type'], x['Advance Rate Definition'], x['Rank_EA']), axis=1)

    df_Portfolio1['Excess EBITDA not in top 3'] = df_Portfolio1.apply(
        lambda x: excessEC(df_Portfolio1[df_Portfolio1['Borrower'] == x['Borrower']],
                           x['Rank_EA'], x['Obligor_DY'], x['Adjusted Borrowing Value_DW'], x['Qualifies?']),
        axis=1)

    # Calculating Applicable Test LImit for Excess Concentration Limit table
    df_ExcessConcentration1['Applicable Test Limit'] = df_ExcessConcentration1.apply(
        lambda x: max(x['Concentration Limit Percentage'] * Adjusted_Borrowing_Value_for_Eligible_Loans,
                      x['Concentration Limit Values']), axis=1)

    # Calculate Excess Largest Obligor (EK)
    # EK --> EI, EG, EE, ED, A
    # EI --> EJ(EH-->EG-->ED-->(DW,EC))
    # ED (Revised Value)  =IFERROR(MAX(0,DW11-EC11),0)

    try:
        df_Portfolio1['Revised Value ED'] = df_Portfolio1.apply(
            lambda x: max(0, x['Adjusted Borrowing Value_DW'] - x['Excess EBITDA not in top 3']), axis=1)
    except:
        df_Portfolio1['Revised Value ED'] = 0

    # Top 3 MAX (EE) =IFERROR('Concentration Limits'!$J$38,0)
    try:
        df_Portfolio1['Top 3 Max'] = df_ExcessConcentration1['Applicable Test Limit'].loc[1]
    except:
        df_Portfolio1['Top 3 Max'] = 0

    # Obligor (EG) =IFERROR(SUMIF($A:$A,$A11,$ED:$ED),0)
    try:
        df_Portfolio1['Obligor EG'] = df_Portfolio1.groupby('Borrower')['Revised Value ED'].transform('sum')
    except:
        df_Portfolio1['Obligor EG'] = 0

    # Remove Dupes (EH) = IFERROR(IF(MATCH($A11,$A:$A,0)=ROW(),$EG11,0),0)--> for Largest Obligor
    # match the value of A in column A to the value of B in column B
    # df['match'] = df['A'].map(df.set_index('B')['A'])
    df_Portfolio1['Remove Dupes EH'] = df_Portfolio1['Obligor EG']
    is_duplicate = df_Portfolio1['Borrower'].duplicated(keep='first')
    df_Portfolio1['Remove Dupes EH'] = df_Portfolio1['Obligor EG'].where(~is_duplicate, 0)

    df_Portfolio1['Rank EJ'] = df_Portfolio1.apply(lambda x: rankEJ(x['Remove Dupes EH'], x['rank'], df_Portfolio1[
        df_Portfolio1['Remove Dupes EH'] == x['Remove Dupes EH']]), axis=1)

    # Rank EI
    # =IFERROR(INDEX(EJ:EJ,MATCH(A11,A:A,0)),0)
    df_Portfolio1['Rank_EI'] = df_Portfolio1.apply(
        lambda x: df_Portfolio1[df_Portfolio1['Borrower'] == x['Borrower']]['Rank EJ'].max(), axis=1)

    df_Portfolio1['Excess Largest Obligor'] = df_Portfolio1.apply(
        lambda x: largestExcess(df_Portfolio1[df_Portfolio1['Borrower'] == x['Borrower']],
                                x['Rank_EI'], x['Obligor EG'], x['Top 3 Max'], x['Revised Value ED']), axis=1)

    # Other Max (EF)
    try:
        df_Portfolio1['Other Max'] = df_ExcessConcentration1['Applicable Test Limit'].loc[2]
    except:
        df_Portfolio1['Other Max'] = 0

    df_Portfolio1['Other Excess'] = df_Portfolio1.apply(
        lambda x: otherExcess(df_Portfolio1[df_Portfolio1['Borrower'] == x['Borrower']],
                              x['Rank_EI'], x['Obligor EG'], x['Other Max'], x['Revised Value ED']), axis=1)

    df_Industries1['O/S Value'] = df_Industries1.apply(
        lambda x: osValue(df_Portfolio1[df_Portfolio1['GICS \nIndustry'] == x['S&P Industry Classification ']])
        , axis=1)
    # Percentage column for Industries Dataframe
    df_Industries1['Percentage'] = df_Industries1['O/S Value'] / df_Industries1['O/S Value'].sum()

    df_Industries1['Industry Rank'] = df_Industries1['O/S Value'].rank(ascending=False, method='min')

    df_Industries1['Industry Rank'] = df_Industries1.apply(
        lambda x: 0 if x['O/S Value'] == 0 else x['Industry Rank'],
        axis=1)

    df_Portfolio1['Largest Industry'] = df_Portfolio1.apply(
        lambda x: largestIndustry(
            df_Industries1[df_Industries1['S&P Industry Classification '] == x['GICS \nIndustry']]),
        axis=1)

    # Revised Value EM
    # =IFERROR(MAX(0,ED11-EK11-EL11),0)
    try:
        df_Portfolio1['Revised Value EM'] = df_Portfolio1.apply(
            lambda x: max(0, (x['Revised Value ED'] - x['Excess Largest Obligor'] - x['Other Excess'])), axis=1)
    except:
        df_Portfolio1['Revised Value EM'] = 0

    # Loan Limit (EO)
    # =IFERROR(SUMIF($AZ:$AZ,$AZ11,EM:EM),0)
    try:
        df_Portfolio1['Loan Limit'] = df_Portfolio1.groupby('GICS \nIndustry')['Revised Value EM'].transform('sum')
    except:
        df_Portfolio1['Loan Limit'] = 0

    # Max (EN)
    # Concentraion limit J40
    df_Portfolio1['Max EN'] = df_ExcessConcentration1['Applicable Test Limit'].loc[3]

    df_Portfolio1['Excess Largest Industry'] = df_Portfolio1.apply(
        lambda x: excessEQ(df_Portfolio1[df_Portfolio1['GICS \nIndustry'] == x['GICS \nIndustry']],
                           x['Largest Industry'], x['Loan Limit'], x['Max EN'], x['Revised Value EM']), axis=1)

    df_Portfolio1['Revised Value ER'] = df_Portfolio1.apply(
        lambda x: revisedValueER(x['Revised Value EM'], x['Excess Largest Industry']), axis=1)

    # Max (ES)
    try:
        df_Portfolio1['Max ES'] = df_ExcessConcentration1['Applicable Test Limit'].loc[4]
    except:
        df_Portfolio1['Max ES'] = 0

    df_Portfolio1['Loan Limit ET'] = df_Portfolio1.apply(
        lambda x: loanLimit(df_Portfolio1[df_Portfolio1['GICS \nIndustry'] == x['GICS \nIndustry']],
                            x['GICS \nIndustry'],
                            x['Revised Value ER']), axis=1)

    df_Portfolio1['2nd Largest Industry'] = df_Portfolio1.apply(lambda x: secondLargestIndustry(
        df_Industries1[df_Industries1['S&P Industry Classification '] == x['GICS \nIndustry']]), axis=1)

    df_Portfolio1['Excess 2nd Largest Industry'] = df_Portfolio1.apply(
        lambda x: excessEV(df_Portfolio1[df_Portfolio1['GICS \nIndustry'] == x['GICS \nIndustry']],
                           x['2nd Largest Industry'], x['Loan Limit ET'], x['Max ES'], x['Revised Value ER']),
        axis=1)

    df_Portfolio1['Revised Value EW'] = df_Portfolio1.apply(
        lambda x: thirdLargestIndustry(x['Revised Value ER'], x['Excess 2nd Largest Industry']), axis=1)

    # Max EX -->
    try:
        df_Portfolio1['Max EX'] = df_ExcessConcentration1['Applicable Test Limit'].loc[5]
    except:
        df_Portfolio1['Max EX'] = 0

    df_Portfolio1['Loan Limit EY'] = df_Portfolio1.apply(
        lambda x: loanLimit(df_Portfolio1[df_Portfolio1['GICS \nIndustry'] == x['GICS \nIndustry']],
                            x['GICS \nIndustry'],
                            x['Revised Value EW']), axis=1)

    df_Portfolio1['Excess 3rd Largest Industry'] = df_Portfolio1.apply(
        lambda x: excessFA(df_Portfolio1[df_Portfolio1['GICS \nIndustry'] == x['GICS \nIndustry']],
                           x['Largest Industry'],
                           x['Loan Limit EY'], x['Max EX'], x['Revised Value EW']), axis=1)

    df_Portfolio1['Revised Value FB'] = df_Portfolio1.apply(
        lambda x: otherIndustry(x['Revised Value EW'], x['Excess 3rd Largest Industry']), axis=1)

    df_Portfolio1['Loan Limit FD'] = df_Portfolio1.apply(
        lambda x: loanLimitFD(df_Portfolio1[df_Portfolio1['GICS \nIndustry'] == x['GICS \nIndustry']],
                              x['GICS \nIndustry'], x['Revised Value FB']), axis=1)

    # Max FC
    # =IFERROR('Concentration Limits'!$J$43,0)
    try:
        df_Portfolio1['Max FC'] = df_ExcessConcentration1['Applicable Test Limit'].loc[6]
    except:
        df_Portfolio1['Max FC'] = 0

    df_Portfolio1['Excess Other Industry'] = df_Portfolio1.apply(
        lambda x: excessFF(df_Portfolio1[df_Portfolio1['GICS \nIndustry'] == x['GICS \nIndustry']],
                           x['Largest Industry'],
                           x['Loan Limit FD'], x['Max FC'], x['Revised Value FB']), axis=1)

    df_Portfolio1['Revised Value FG'] = df_Portfolio1.apply(
        lambda x: revisedValueFG(x['Revised Value FB'], x['Excess Other Industry']), axis=1)

    # Max FH
    # =IFERROR('Concentration Limits'!$J$44,0)
    try:
        df_Portfolio1['Max FH'] = df_ExcessConcentration1['Applicable Test Limit'].loc[7]
    except:
        df_Portfolio1['Max FH'] = 0

    df_Portfolio1['Qualifies < $10MM'] = df_Portfolio1.apply(
        lambda x: qualifiesEbitdaLess10MM(x['Permitted TTM EBITDA Current']), axis=1)

    df_Portfolio1['Loan Limit FJ'] = df_Portfolio1.apply(
        lambda x: loanLimitFJ(df_Portfolio1[df_Portfolio1['Qualifies < $10MM'] == 'Yes'], x['Qualifies < $10MM'],
                              x['Revised Value FG']), axis=1)

    df_Portfolio1['Excess EBITDA < 10MM'] = df_Portfolio1.apply(
        lambda x: excessFK(df_Portfolio1[df_Portfolio1['Qualifies < $10MM'] == 'Yes'], x['Loan Limit FJ'],
                           x['Max FH'],
                           x['Revised Value FG']), axis=1)

    df_Portfolio1['Revised Value FL'] = df_Portfolio1.apply(
        lambda x: revisedValueFL(x['Revised Value FG'], x['Excess EBITDA < 10MM']), axis=1)

    # Max FM -->DIP Loans
    # =IFERROR('Concentration Limits'!$J$45,0)
    try:
        df_Portfolio1['Max FM'] = df_ExcessConcentration1['Applicable Test Limit'].loc[8]
    except:
        df_Portfolio1['Max FM'] = 0

    df_Portfolio1['Qualifies DIP Loan'] = df_Portfolio1.apply(lambda x: qualifiesDIPLoan(x['DIP Loan?']), axis=1)

    df_Portfolio1['Loan Limit FO'] = df_Portfolio1.apply(
        lambda x: loanLimitFO(df_Portfolio1[df_Portfolio1['Qualifies DIP Loan'] == 'Yes'], x['Qualifies DIP Loan'],
                              x['Revised Value FL']), axis=1)

    df_Portfolio1['Excess DIP Loans'] = df_Portfolio1.apply(
        lambda x: excessFP(df_Portfolio1[df_Portfolio1['Qualifies DIP Loan'] == 'Yes'], x['Loan Limit FO'],
                           x['Max FM'],
                           x['Revised Value FL']), axis=1)

    df_Portfolio1['Revised Value FQ'] = df_Portfolio1.apply(
        lambda x: revisedValueFQ(x['Revised Value FL'], x['Excess DIP Loans']), axis=1)

    # Max FR --> Cov Lite Loans
    # =IFERROR('Concentration Limits'!$J$46,0)
    try:
        df_Portfolio1['Max FR'] = df_ExcessConcentration1['Applicable Test Limit'].loc[9]
    except:
        df_Portfolio1['Max FR'] = 0

    df_Portfolio1['Qualifies Cov Lite Loan'] = df_Portfolio1.apply(lambda x: qualifiesCovLiteLoan(x['Cov-Lite?']),
                                                                   axis=1)

    df_Portfolio1['Loan Limit FT'] = df_Portfolio1.apply(
        lambda x: loanLimitFT(df_Portfolio1[df_Portfolio1['Qualifies Cov Lite Loan'] == 'Yes'],
                              x['Qualifies Cov Lite Loan'], x['Revised Value FQ']), axis=1)

    df_Portfolio1['Excess Cov-Lite Loans'] = df_Portfolio1.apply(
        lambda x: excessFU(df_Portfolio1[df_Portfolio1['Qualifies Cov Lite Loan'] == 'Yes'], x['Loan Limit FT'],
                           x['Max FR'], x['Revised Value FQ']), axis=1)

    df_Portfolio1['Revised Value FV'] = df_Portfolio1.apply(
        lambda x: revisedValueFV(x['Revised Value FQ'], x['Excess Cov-Lite Loans']), axis=1)

    # Max FW --> Less than Qtrly Pay
    # =IFERROR('Concentration Limits'!$J$47,0)
    try:
        df_Portfolio1['Max FW'] = df_ExcessConcentration1['Applicable Test Limit'].loc[10]
    except:
        df_Portfolio1['Max FW'] = 0

    df_Portfolio1['Qualifies Less than Qtrly'] = df_Portfolio1.apply(
        lambda x: qualifiesLessThanQtrly(x['Paid Less than Qtrly or Mthly']), axis=1)

    df_Portfolio1['Loan Limit FY'] = df_Portfolio1.apply(
        lambda x: loanLimitFY(df_Portfolio1[df_Portfolio1['Qualifies Less than Qtrly'] == 'Yes'],
                              x['Qualifies Less than Qtrly'], x['Revised Value FV']), axis=1)

    df_Portfolio1['Excess Less than Qtrly Pay'] = df_Portfolio1.apply(
        lambda x: excessFZ(df_Portfolio1[df_Portfolio1['Qualifies Less than Qtrly'] == 'Yes'], x['Loan Limit FY'],
                           x['Max FW'], x['Revised Value FV']), axis=1)

    df_Portfolio1['Revised Value GA'] = df_Portfolio1.apply(
        lambda x: revisedValueGA(x['Revised Value FV'], x['Excess Less than Qtrly Pay']), axis=1)

    # Max GB
    # =IFERROR('Concentration Limits'!$J$48,0)
    try:
        df_Portfolio1['Max GB'] = df_ExcessConcentration1['Applicable Test Limit'].loc[11]
    except:
        df_Portfolio1['Max GB'] = 0

    df_Portfolio1['Qualifies Foreign Currency'] = df_Portfolio1.apply(
        lambda x: qualifiesForeignGC(x['Non-US Approved Currency?']), axis=1)

    df_Portfolio1['Loan Limit GD'] = df_Portfolio1.apply(
        lambda x: loanLimitGD(df_Portfolio1[df_Portfolio1['Qualifies Foreign Currency'] == 'Yes'],
                              x['Qualifies Foreign Currency'], x['Revised Value GA']), axis=1)

    df_Portfolio1['Excess Foreign Currency'] = df_Portfolio1.apply(
        lambda x: excessGE(df_Portfolio1[df_Portfolio1['Qualifies Foreign Currency'] == 'Yes'], x['Loan Limit GD'],
                           x['Max GB'], x['Revised Value GA']), axis=1)

    df_Portfolio1['Revised Value GF'] = df_Portfolio1.apply(
        lambda x: revisedValueGF(x['Revised Value GA'], x['Excess Foreign Currency']), axis=1)

    # Max GG
    # =IFERROR('Concentration Limits'!$J$49,0)
    try:
        df_Portfolio1['Max GG'] = df_ExcessConcentration1['Applicable Test Limit'].loc[12]
    except:
        df_Portfolio1['Max GG'] = 0

    df_Portfolio1['Qualifies Non US Country'] = df_Portfolio1.apply(
        lambda x: qualifiesCountryGH(x['Non-US Approved Country?']), axis=1)

    df_Portfolio1['Loan Limit GI'] = df_Portfolio1.apply(
        lambda x: loanLimitGI(df_Portfolio1[df_Portfolio1['Qualifies Non US Country'] == 'Yes'],
                              x['Qualifies Non US Country'], x['Revised Value GF']), axis=1)

    df_Portfolio1['Excess Aprroved Country'] = df_Portfolio1.apply(
        lambda x: excessGJ(df_Portfolio1[df_Portfolio1['Qualifies Non US Country'] == 'Yes'], x['Loan Limit GI'],
                           x['Max GG'], x['Revised Value GF']), axis=1)

    df_Portfolio1['Revised Value GK'] = df_Portfolio1.apply(
        lambda x: revisedValueGK(x['Revised Value GF'], x['Excess Aprroved Country']), axis=1)

    # Max GL
    # =IFERROR('Concentration Limits'!$J$50,0)
    try:
        df_Portfolio1['Max GL'] = df_ExcessConcentration1['Applicable Test Limit'].loc[13]
    except:
        df_Portfolio1['Max GL'] = 0

    df_Portfolio1['Qualifies DDTL and Revolving Loans'] = df_Portfolio1.apply(
        lambda x: qualifiesDDTLandRevolvingGM(x['Revolving / Delayed Funding?']), axis=1)

    df_Portfolio1['Loan Limit GN'] = df_Portfolio1.apply(
        lambda x: loanLimitGN(df_Portfolio1[df_Portfolio1['Qualifies DDTL and Revolving Loans'] == 'Yes'],
                              x['Qualifies DDTL and Revolving Loans'], x['Revised Value GK']), axis=1)

    df_Portfolio1['Excess DDTL and Revolving Loans'] = df_Portfolio1.apply(
        lambda x: excessGO(df_Portfolio1[df_Portfolio1['Qualifies DDTL and Revolving Loans'] == 'Yes'],
                           x['Loan Limit GN'], x['Max GL'], x['Revised Value GK']), axis=1)

    df_Portfolio1['Revised Value GP'] = df_Portfolio1.apply(
        lambda x: revisedValueGP(x['Revised Value GK'], x['Excess DDTL and Revolving Loans']), axis=1)

    # Max GQ
    # =IFERROR('Concentration Limits'!$J$51,0)
    try:
        df_Portfolio1['Max GQ'] = df_ExcessConcentration1['Applicable Test Limit'].loc[14]
    except:
        df_Portfolio1['Max GQ'] = 0

    df_Portfolio1['Permitted Net Senior Leverage CE'] = df_Portfolio1.apply(
        lambda x: permittedNetSeniorLeverageCE(x['Initial Unrestricted Cash'], x['Initial Senior Debt'],
                                               x['Permitted TTM EBITDA']), axis=1)

    df_Portfolio1['Permitted Net Total Leverage CG'] = df_Portfolio1.apply(
        lambda x: permittedNetTotalLeverageCG(x['Initial Total Debt'], x['Initial Unrestricted Cash'],
                                              x['Permitted TTM EBITDA']), axis=1)

    df_Portfolio1['Initial Multiple'] = df_Portfolio1.apply(
        lambda x: initialMultiple(x['Loan Type'], x['Initial Total Debt'], x['Initial Recurring Revenue']), axis=1)

    df_Portfolio1['Tier'] = df_Portfolio1.apply(
        lambda x: tiers(x['Loan Type'], x['Permitted Net Senior Leverage CE'], x['Permitted Net Total Leverage CG'],
                        x['Initial Multiple'], Tier_1_1L, Tier_2_1L, Tier_1_2L, Tier_2_2L, Tier_1_RR, Tier_2_RR),
        axis=1)

    df_Portfolio1['Qualifies Tier 3 Obligor'] = df_Portfolio1.apply(
        lambda x: qualifiesTier3Obligor(x['Eligibility Check'], x['Tier']), axis=1)

    df_Portfolio1['Loan Limit GS'] = df_Portfolio1.apply(
        lambda x: loanLimitGS(df_Portfolio1[df_Portfolio1['Qualifies Tier 3 Obligor'] == 'Yes'],
                              x['Qualifies Tier 3 Obligor'], x['Revised Value GP']), axis=1)

    df_Portfolio1['Excess Tier 3 Obligors'] = df_Portfolio1.apply(
        lambda x: excessGT(df_Portfolio1[df_Portfolio1['Qualifies Tier 3 Obligor'] == 'Yes'], x['Loan Limit GS'],
                           x['Max GQ'], x['Revised Value GP']), axis=1)

    df_Portfolio1['Revised Value GU'] = df_Portfolio1.apply(
        lambda x: revisedValueGU(x['Revised Value GP'], x['Excess Tier 3 Obligors']), axis=1)

    # Max GV
    # =IFERROR('Concentration Limits'!$J$52,0)
    try:
        df_Portfolio1['Max GV'] = df_ExcessConcentration1['Applicable Test Limit'].loc[15]
    except:
        df_Portfolio1['Max GV'] = 0

    df_Portfolio1['Loan Limit GW'] = df_Portfolio1.apply(
        lambda x: loanLimitGW(df_Portfolio1[df_Portfolio1['Loan Type'] == 'Second Lien'], x['Loan Type'],
                              x['Revised Value GU']), axis=1)

    df_Portfolio1['Excess Second Lien'] = df_Portfolio1.apply(
        lambda x: excessGX(df_Portfolio1[df_Portfolio1['Loan Type'] == x['Loan Type']], x['Loan Limit GW'],
                           x['Max GV'], x['Revised Value GU']), axis=1)

    df_Portfolio1['Revised Value GY'] = df_Portfolio1.apply(
        lambda x: revisedValueGY(x['Revised Value GU'], x['Excess Second Lien']), axis=1)

    # Max GZ (First Lien Last Out)
    # =IFERROR('Concentration Limits'!$J$53,0)
    try:
        df_Portfolio1['Max GZ'] = df_ExcessConcentration1['Applicable Test Limit'].loc[16]
    except:
        df_Portfolio1['Max GZ'] = 0

    df_Portfolio1['Loan Limit HA'] = df_Portfolio1.apply(
        lambda x: loanLimitHA(df_Portfolio1[df_Portfolio1['Loan Type'] == 'Last Out'], x['Loan Type'],
                              x['Revised Value GY']), axis=1)

    df_Portfolio1['Excess First Lien Last Out'] = df_Portfolio1.apply(
        lambda x: excessHB(df_Portfolio1[df_Portfolio1['Loan Type'] == x['Loan Type']], x['Loan Limit HA'],
                           x['Max GZ'], x['Revised Value GY']), axis=1)

    df_Portfolio1['Revised Value HC'] = df_Portfolio1.apply(
        lambda x: revisedValueHC(x['Revised Value GY'], x['Excess First Lien Last Out']), axis=1)

    # Max HD (Loan Maturities Greater than 6 Years)
    # =IFERROR('Concentration Limits'!$J$54,0)
    try:
        df_Portfolio1['Max HD'] = df_ExcessConcentration1['Applicable Test Limit'].loc[17]
    except:
        df_Portfolio1['Max HD'] = 0

    df_Portfolio1['Original Term'] = df_Portfolio1.apply(
        lambda x: originalTerm(x['Acquisition Date'], x['Maturity Date']), axis=1)

    df_Portfolio1['Qualifies HE'] = df_Portfolio1.apply(lambda x: qualifiesHE(x['Original Term']), axis=1)

    df_Portfolio1['Loan Limit HF'] = df_Portfolio1.apply(
        lambda x: loanLimitHF(df_Portfolio1[df_Portfolio1['Qualifies HE'] == 'Yes'], x['Qualifies HE'],
                              x['Revised Value HC']), axis=1)

    df_Portfolio1['Excess Maturity greater than 6 Years'] = df_Portfolio1.apply(
        lambda x: excessHG(df_Portfolio1[df_Portfolio1['Qualifies HE'] == 'Yes'], x['Loan Limit HF'], x['Max HD'],
                           x['Revised Value HC']), axis=1)

    df_Portfolio1['Revised Value HH'] = df_Portfolio1.apply(
        lambda x: revisedValueHH(x['Revised Value HC'], x['Excess Maturity greater than 6 Years']), axis=1)

    # Max HI
    # =IFERROR('Concentration Limits'!$J$55,0)
    try:
        df_Portfolio1['Max HI'] = df_ExcessConcentration1['Applicable Test Limit'].loc[18]
    except:
        df_Portfolio1['Max HI'] = 0

    df_Portfolio1['Qualifies HJ'] = df_Portfolio1.apply(lambda x: qualifiesHJ(x['Gambling Industry?']), axis=1)

    df_Portfolio1['Loan Limit HK'] = df_Portfolio1.apply(
        lambda x: loanLimitHK(df_Portfolio1[df_Portfolio1['Qualifies HJ'] == 'Yes'], x['Qualifies HE'],
                              x['Revised Value HH']), axis=1)

    df_Portfolio1['Excess Gambling Industries'] = df_Portfolio1.apply(
        lambda x: excessHL(df_Portfolio1[df_Portfolio1['Qualifies HJ'] == 'Yes'], x['Loan Limit HK'], x['Max HI'],
                           x['Revised Value HH']), axis=1)

    df_Portfolio1['Revised Value HM'] = df_Portfolio1.apply(
        lambda x: revisedValueHM(x['Revised Value HH'], x['Excess Gambling Industries']), axis=1)

    # Max HN
    # =IFERROR('Concentration Limits'!$J$56,0)
    try:
        df_Portfolio1['Max HN'] = df_ExcessConcentration1['Applicable Test Limit'].loc[19]
    except:
        df_Portfolio1['Max HN'] = 0

    df_Portfolio1['Qualifies HO'] = df_Portfolio1.apply(lambda x: qualifiesHO(x['Loan Type']), axis=1)

    df_Portfolio1['Loan Limit HP'] = df_Portfolio1.apply(
        lambda x: loanLimitHP(df_Portfolio1[df_Portfolio1['Qualifies HO'] == 'Yes'], x['Qualifies HO'],
                              x['Revised Value HM']), axis=1)

    df_Portfolio1['Excess Recurring Revenue Loans'] = df_Portfolio1.apply(
        lambda x: excessHQ(df_Portfolio1[df_Portfolio1['Qualifies HO'] == 'Yes'], x['Loan Limit HP'], x['Max HN'],
                           x['Revised Value HM']), axis=1)

    df_ExcessConcentration1.loc[0, 'Excess Concentration Amount'] = df_Portfolio1[
        'Excess EBITDA not in top 3'].sum()
    df_ExcessConcentration1.loc[1, 'Excess Concentration Amount'] = df_Portfolio1['Excess Largest Obligor'].sum()
    df_ExcessConcentration1.loc[2, 'Excess Concentration Amount'] = df_Portfolio1['Other Excess'].sum()
    df_ExcessConcentration1.loc[3, 'Excess Concentration Amount'] = df_Portfolio1['Excess Largest Industry'].sum()
    df_ExcessConcentration1.loc[4, 'Excess Concentration Amount'] = df_Portfolio1[
        'Excess 2nd Largest Industry'].sum()
    df_ExcessConcentration1.loc[5, 'Excess Concentration Amount'] = df_Portfolio1[
        'Excess 3rd Largest Industry'].sum()
    df_ExcessConcentration1.loc[6, 'Excess Concentration Amount'] = df_Portfolio1['Excess Other Industry'].sum()
    df_ExcessConcentration1.loc[7, 'Excess Concentration Amount'] = df_Portfolio1['Excess EBITDA < 10MM'].sum()
    df_ExcessConcentration1.loc[8, 'Excess Concentration Amount'] = df_Portfolio1['Excess DIP Loans'].sum()
    df_ExcessConcentration1.loc[9, 'Excess Concentration Amount'] = df_Portfolio1['Excess Cov-Lite Loans'].sum()
    df_ExcessConcentration1.loc[10, 'Excess Concentration Amount'] = df_Portfolio1[
        'Excess Less than Qtrly Pay'].sum()
    df_ExcessConcentration1.loc[11, 'Excess Concentration Amount'] = df_Portfolio1['Excess Foreign Currency'].sum()
    df_ExcessConcentration1.loc[12, 'Excess Concentration Amount'] = df_Portfolio1['Excess Aprroved Country'].sum()
    df_ExcessConcentration1.loc[13, 'Excess Concentration Amount'] = df_Portfolio1[
        'Excess DDTL and Revolving Loans'].sum()
    df_ExcessConcentration1.loc[14, 'Excess Concentration Amount'] = df_Portfolio1['Excess Tier 3 Obligors'].sum()
    df_ExcessConcentration1.loc[15, 'Excess Concentration Amount'] = df_Portfolio1['Excess Second Lien'].sum()
    df_ExcessConcentration1.loc[16, 'Excess Concentration Amount'] = df_Portfolio1[
        'Excess First Lien Last Out'].sum()
    df_ExcessConcentration1.loc[17, 'Excess Concentration Amount'] = df_Portfolio1[
        'Excess Maturity greater than 6 Years'].sum()
    df_ExcessConcentration1.loc[18, 'Excess Concentration Amount'] = df_Portfolio1[
        'Excess Gambling Industries'].sum()
    df_ExcessConcentration1.loc[19, 'Excess Concentration Amount'] = df_Portfolio1[
        'Excess Recurring Revenue Loans'].sum()

    # Total Excess Concentration Amount
    Total_Excess_Concentration_Amount = df_ExcessConcentration1['Excess Concentration Amount'].sum()

    global df_Excess
    df_Excess = df_Portfolio1[
        ['Excess EBITDA not in top 3', 'Excess Largest Obligor', 'Other Excess', 'Excess Largest Industry',
         'Excess 2nd Largest Industry', 'Excess 3rd Largest Industry', 'Excess Other Industry',
         'Excess EBITDA < 10MM',
         'Excess DIP Loans', 'Excess Cov-Lite Loans', 'Excess Less than Qtrly Pay', 'Excess Foreign Currency',
         'Excess Aprroved Country', 'Excess DDTL and Revolving Loans', 'Excess Tier 3 Obligors',
         'Excess Second Lien',
         'Excess First Lien Last Out', 'Excess Maturity greater than 6 Years', 'Excess Gambling Industries',
         'Excess Recurring Revenue Loans']]

    # Par Value of Portfolio
    Par_Value_of_Portfolio = df_Portfolio1['Borrower Outstanding Principal Balance'].sum()

    # Minimum credit Enhancement
    # =LARGE('Portfolio '!DZ:DZ,1)+LARGE('Portfolio '!DZ:DZ,2)+LARGE('Portfolio '!DZ:DZ,3)+LARGE('Portfolio '!DZ:DZ,4)+LARGE('Portfolio '!DZ:DZ,5)
    Minimum_credit_enhancemnt = df_Portfolio1['Remove Dupes'].nlargest(1).iloc[-1] + \
                                df_Portfolio1['Remove Dupes'].nlargest(2).iloc[-1] + \
                                df_Portfolio1['Remove Dupes'].nlargest(3).iloc[-1] + \
                                df_Portfolio1['Remove Dupes'].nlargest(4).iloc[-1] + \
                                df_Portfolio1['Remove Dupes'].nlargest(5).iloc[-1]

    df_Portfolio1['Borrower Unfunded Amount'] = df_Portfolio1.apply(
        lambda x: borrowerUnfundedAmount(x['Borrower Outstanding Principal Balance'],
                                         x['Borrower Facility Commitment']), axis=1)

    # Unfunded Exposure Amount
    # =SUMIF('Portfolio '!AQ:AQ,"yes",'Portfolio '!J:J)
    Unfunded_exposure_amount = round(
        df_Portfolio1[df_Portfolio1['Revolving / Delayed Funding?'] == 'Yes']['Borrower Unfunded Amount'].sum())

    df_Portfolio1['Advance Rate'] = df_Portfolio1.apply(lambda x: advanceRate(
        df_BorrowerOutstandings1[df_BorrowerOutstandings1['Loan Category'] == x['Advance Rate Definition']]),
                                                        axis=1)
    # Weighted Average Advance Rate for Unfunded Exposures
    Weighted_Average_Advance_Rate_for_Unfunded_Exposures = \
        df_Portfolio1.groupby('Revolving / Delayed Funding?').apply(
            lambda x: sum(x['Borrower Unfunded Amount'] * x['Advance Rate']))['Yes'] / Unfunded_exposure_amount

    Advance_Rate_Cap_Until_15_Loans_in_Effect = 'Yes' if Weighted_Average_Advance_Rate_for_Unfunded_Exposures < 0.15 else 'No'

    # =IF(G158="Yes",G26,G157)
    Advance_Rate_Applied = df_Availability1['Value'].iloc[
        8] if Advance_Rate_Cap_Until_15_Loans_in_Effect == 'Yes' else Weighted_Average_Advance_Rate_for_Unfunded_Exposures

    # =IF(SUMIF('Portfolio '!$AQ$10:$AQ$85,"yes",'Portfolio '!$J$10:$J$85)=0,0,SUMPRODUCT(--('Portfolio '!$AQ$10:$AQ$85="yes"),'Portfolio '!$J$10:$J$85,'Portfolio '!$T$10:$T$85)/SUMIF('Portfolio '!$AQ$10:$AQ$85,"yes",'Portfolio '!$J$10:$J$85))
    # SUMIF('Portfolio '!$AQ$10:$AQ$85,"yes",'Portfolio '!$J$10:$J$85 = Unfunded_Exposure_Amount
    # SUMPRODUCT(--('Portfolio '!$AQ$10:$AQ$85="yes"),'Portfolio '!$J$10:$J$85,'Portfolio '!$T$10:$T$85)/SUMIF('Portfolio '!$AQ$10:$AQ$85,"yes",'Portfolio '!$J$10:$J$85))
    Weighted_Average_Applicable_Collateral_Value_for_Unfunded_Exposures = \
        df_Portfolio1.groupby('Revolving / Delayed Funding?').apply(
            lambda x: sum(x['Borrower Unfunded Amount'] * x['Assigned Value'])).iloc[1] / Unfunded_exposure_amount

    # Unfunded Equity Exposure Amount =((1-G159)*G155)+((1-G161)*G159*G155)
    Unfunded_Equity_Exposure_Amount = ((1 - Advance_Rate_Applied) * Unfunded_exposure_amount) + ((
                                                                                                         1 - Weighted_Average_Applicable_Collateral_Value_for_Unfunded_Exposures) * Advance_Rate_Applied * Unfunded_exposure_amount)

    # Foreign Currency Adjusted Borrowing Value
    # =SUMIF('Portfolio '!AS11:AS522,"Yes",'Portfolio '!E11:E522)
    Foreign_Currency_Adjusted_Borrowing_Value = df_Portfolio1[df_Portfolio1['Non-US Approved Country?'] == 'Yes'][
        'Adjusted Borrowing Value'].sum()

    Unhedged_Foreign_Currency = Foreign_Currency_Adjusted_Borrowing_Value - df_Availability1['Value'].iloc[4]

    df_Portfolio1['Revised Value HR'] = df_Portfolio1.apply(
        lambda x: revisedValueHR(x['Revised Value HM'], x['Excess Recurring Revenue Loans']), axis=1)

    df_Portfolio1['First Lien'] = df_Portfolio1.apply(
        lambda x: firstLien(x['First Lien Value'], x['Revised Value HR'], x['Second Lien Value']), axis=1)

    df_Portfolio1['Reclassed Second HT'] = df_Portfolio1.apply(
        lambda x: reclassedSecond(x['Second Lien Value'], x['Revised Value HR'], x['First Lien Value']), axis=1)

    df_Portfolio1['Last Out HU'] = df_Portfolio1.apply(
        lambda x: lastOut(x['Loan Type'], x['Revised Value HR'], x['FLLO Value'], x['Second Lien ValueAC']), axis=1)

    df_Portfolio1['Reclassed Second HV'] = df_Portfolio1.apply(
        lambda x: reclassedSecondHV(x['Loan Type'], x['Revised Value HR'], x['Second Lien ValueAC'],
                                    x['FLLO Value']),
        axis=1)

    df_Portfolio1['Recurring Revenue HW'] = df_Portfolio1.apply(
        lambda x: recurringRevenueHW(x['Loan Type'], x['Revised Value HR'], x['Recurring Revenue Value']), axis=1)

    # Create a new column in Borrower Outstanding Dataframe
    df_BorrowerOutstandings1['Base Borrowing Value'] = np.nan

    # =SUMIF('Portfolio '!$C$11:$C$522, 'Concentration Limits'!D5, 'Portfolio '!$HS$11:$HS$522)
    # Base Borrowing Value in Borrower Outstanidings
    df_BorrowerOutstandings1['Base Borrowing Value'].iloc[0] = \
        df_Portfolio1[
            df_Portfolio1['Advance Rate Definition'] == df_BorrowerOutstandings1['Loan Category'].iloc[0]][
            'First Lien'].sum()

    # =SUMIF('Portfolio '!$C$11:$C$522, 'Concentration Limits'!D5, 'Portfolio '!$HS$11:$HS$522)
    # Base Borrowing Value in Borrower Outstanidings
    df_BorrowerOutstandings1['Base Borrowing Value'].iloc[0] = \
        df_Portfolio1[
            df_Portfolio1['Advance Rate Definition'] == df_BorrowerOutstandings1['Loan Category'].iloc[0]][
            'First Lien'].sum()

    # =SUMIF('Portfolio '!$C$11:$C$522, 'Concentration Limits'!D5, 'Portfolio '!$HT$11:$HT$522)
    # Base Borrowing Value in Borrower Outstanidings
    df_BorrowerOutstandings1['Base Borrowing Value'].iloc[1] = \
        df_Portfolio1[
            df_Portfolio1['Advance Rate Definition'] == df_BorrowerOutstandings1['Loan Category'].iloc[0]][
            'Reclassed Second HT'].sum()

    # =SUMIF('Portfolio '!$C$11:$C$522, 'Concentration Limits'!D8, 'Portfolio '!$HS$11:$HS$522)
    # Base Borrowing Value in Borrower Outstanidings
    df_BorrowerOutstandings1['Base Borrowing Value'].iloc[3] = \
        df_Portfolio1[
            df_Portfolio1['Advance Rate Definition'] == df_BorrowerOutstandings1['Loan Category'].iloc[3]][
            'First Lien'].sum()

    # =SUMIF('Portfolio '!$C$11:$C$522, 'Concentration Limits'!D8, 'Portfolio '!$HT$11:$HT$522)
    # Base Borrowing Value in Borrower Outstanidings
    df_BorrowerOutstandings1['Base Borrowing Value'].iloc[4] = \
        df_Portfolio1[
            df_Portfolio1['Advance Rate Definition'] == df_BorrowerOutstandings1['Loan Category'].iloc[3]][
            'Reclassed Second HT'].sum()

    # =SUMIF('Portfolio '!$C$11:$C$522, 'Concentration Limits'!D11, 'Portfolio '!$HS$11:$HS$522)
    # Base Borrowing Value in Borrower Outstanidings
    df_BorrowerOutstandings1['Base Borrowing Value'].iloc[6] = \
        df_Portfolio1[
            df_Portfolio1['Advance Rate Definition'] == df_BorrowerOutstandings1['Loan Category'].iloc[6]][
            'First Lien'].sum()

    # =SUMIF('Portfolio '!$C$11:$C$522, 'Concentration Limits'!D11, 'Portfolio '!$HT$11:$HT$522)
    # Base Borrowing Value in Borrower Outstanidings
    df_BorrowerOutstandings1['Base Borrowing Value'].iloc[7] = \
        df_Portfolio1[
            df_Portfolio1['Advance Rate Definition'] == df_BorrowerOutstandings1['Loan Category'].iloc[6]][
            'Reclassed Second HT'].sum()

    # =SUMIF('Portfolio '!$C$11:$C$522, 'Concentration Limits'!D14, 'Portfolio '!$HS$11:$HS$522)
    # Base Borrowing Value in Borrower Outstanidings
    df_BorrowerOutstandings1['Base Borrowing Value'].iloc[9] = \
        df_Portfolio1[
            df_Portfolio1['Advance Rate Definition'] == df_BorrowerOutstandings1['Loan Category'].iloc[9]][
            'First Lien'].sum()

    # =SUMIF('Portfolio '!$C$11:$C$522, 'Concentration Limits'!D14, 'Portfolio '!$HT$11:$HT$522)
    # Base Borrowing Value in Borrower Outstanidings
    df_BorrowerOutstandings1['Base Borrowing Value'].iloc[10] = \
        df_Portfolio1[
            df_Portfolio1['Advance Rate Definition'] == df_BorrowerOutstandings1['Loan Category'].iloc[9]][
            'Reclassed Second HT'].sum()

    # =SUMIF('Portfolio '!$C$11:$C$522, 'Concentration Limits'!D17, 'Portfolio '!$HU$11:$HU$522)
    # Base Borrowing Value in Borrower Outstanidings
    df_BorrowerOutstandings1['Base Borrowing Value'].iloc[12] = \
        df_Portfolio1[
            df_Portfolio1['Advance Rate Definition'] == df_BorrowerOutstandings1['Loan Category'].iloc[12]][
            'Last Out HU'].sum()

    # =SUMIF('Portfolio '!$C$11:$C$522, 'Concentration Limits'!D19, 'Portfolio '!$HV$11:$HV$522)
    # Base Borrowing Value in Borrower Outstanidings
    df_BorrowerOutstandings1['Base Borrowing Value'].iloc[14] = \
        df_Portfolio1[
            df_Portfolio1['Advance Rate Definition'] == df_BorrowerOutstandings1['Loan Category'].iloc[14]][
            'Reclassed Second HV'].sum()

    # =SUMIF('Portfolio '!$C$11:$C$522, 'Concentration Limits'!D1, 'Portfolio '!$HW$11:$HW$522)
    # Base Borrowing Value in Borrower Outstanidings
    df_BorrowerOutstandings1['Base Borrowing Value'].iloc[16] = \
        df_Portfolio1[
            df_Portfolio1['Advance Rate Definition'] == df_BorrowerOutstandings1['Loan Category'].iloc[16]][
            'Recurring Revenue HW'].sum()

    Total_Borrowing_Base = df_BorrowerOutstandings1['Base Borrowing Value'].sum()

    df_BorrowerOutstandings1['Base Borrowing Percentage'] = df_BorrowerOutstandings1.apply(
        lambda x: baseBorrowingPercentage(x['Base Borrowing Value'], Total_Borrowing_Base), axis=1)

    Weighted_Average_Advance_Rate = (
            df_BorrowerOutstandings1['Advance Rate'] * df_BorrowerOutstandings1['Base Borrowing Percentage']).sum()

    Base_Borrowing_Percentage = df_BorrowerOutstandings1['Base Borrowing Percentage'].sum()

    Approved_Country = 0.03 * Unhedged_Foreign_Currency

    Borrowing_Base = (
            Adjusted_Borrowing_Value_for_Eligible_Loans - Total_Excess_Concentration_Amount - Unhedged_Foreign_Currency)

    # The sum of: (i) the product of (x) the Borrowing Base and (y) the weighted average Advance Rate, minus
    # Aggregate Unfunded Exposure Equity Amount, plus (ii) Cash on deposit in  the principal collection subaccount.
    b = ((Borrowing_Base * Weighted_Average_Advance_Rate) - Unfunded_Equity_Exposure_Amount +
         df_Availability1['Value'].iloc[3] + df_Availability1['Value'].iloc[2])

    # The Adjusted Borrowing Value of Eligible Loans minus the Minimum Credit Enhancement Amount plus
    # the amount on deposit in the Principal Collection Account, minus the Aggregate Unfunded Exposure Equity Amount
    c = (Adjusted_Borrowing_Value_for_Eligible_Loans - Minimum_credit_enhancemnt + df_Availability1['Value'].iloc[
        2] - Unfunded_Equity_Exposure_Amount + df_Availability1['Value'].iloc[3]).round()

    # Availability Amount
    Availability_Amount = min(df_Availability1['Value'].iloc[1], b, c)

    Effective_Advance_Rate = Availability_Amount / Par_Value_of_Portfolio

    Effective_Debt_to_Equity = Effective_Advance_Rate / (1 - Effective_Advance_Rate)

    Proforma_Advances_Outstanding = df_Availability1['Value'].iloc[5] - df_Availability1['Value'].iloc[6] + \
                                    df_Availability1['Value'].iloc[7]

    Availability_Less_Advances_Outstanding = Availability_Amount - Proforma_Advances_Outstanding

    Maximum_Advance_Rate_Test = Availability_Amount >= Proforma_Advances_Outstanding

    Facility_Utilization = Proforma_Advances_Outstanding / df_Availability1['Value'].iloc[1]

    Actual_Advance_Rate = Proforma_Advances_Outstanding / Par_Value_of_Portfolio

    AvailabilityDict = {
        'Terms': ['Availability Amount', 'Effective Advance Rate', 'Effective Debt to Equity',
                  'Par Value of Portfolio',
                  'Adjusted Borrowing Value of Eligible Loans', 'Excess Concentraions', 'Approved Country Reserves',
                  'Borrowing Base ',
                  'Minimum Credit Enhancement', 'Unfunded Exposure Amount', 'Unfunded Equity Exposure Amount',
                  'On Deposit in Unfunded Exposure Account', 'Foreign Currency Adjusted Borrowing Value',
                  'Foreign Currency hedged by Borrower', 'Unhedged Foreign Currency',
                  'Weighted Average Advance Rate',
                  'Cash on deposit in principal collections account', 'Current Advances Outstanding',
                  'Advance Repaid',
                  'Advances Requested', 'Pro Forma Advances Outstanding', 'Availability LESS Advances Outstanding',
                  'Maximum Advance Rate Test', 'Facility Utilization', 'Actual Advance Rate'],
        'Values': [f"${int(Availability_Amount):,}", '{:.2f}%'.format(Effective_Advance_Rate * 100),
                   '{:.2f}'.format(Effective_Debt_to_Equity), f"${int(Par_Value_of_Portfolio):,}",
                   f"${int(Adjusted_Borrowing_Value_for_Eligible_Loans):,}",
                   f"${int(Total_Excess_Concentration_Amount):,}", f"{int(Approved_Country)}",
                   f"${int(Borrowing_Base):,}", f"${int(Minimum_credit_enhancemnt):,}", f"${Unfunded_exposure_amount}",
                   f"${int(Unfunded_Equity_Exposure_Amount):,}",
                   f"${df_Availability1['Value'].iloc[3]:,}", f"{int(Foreign_Currency_Adjusted_Borrowing_Value)}",
                   df_Availability1['Value'].iloc[4], f"{int(Unhedged_Foreign_Currency)}",
                   '{:.2f}%'.format(Weighted_Average_Advance_Rate * 100),
                   f"${int(df_Availability1['Value'].iloc[2]):,}", f"${df_Availability1['Value'].iloc[5]:,}",
                   df_Availability1['Value'].iloc[6],
                   f"${df_Availability1['Value'].iloc[7]:,}", f"${Proforma_Advances_Outstanding:,}",
                   f"${int(Availability_Less_Advances_Outstanding):,}", Maximum_Advance_Rate_Test,
                   '{:.2f}%'.format(Facility_Utilization * 100),
                   '{:.2f}%'.format(Actual_Advance_Rate * 100)]}

    df_Portfolio['Interest Coverage'] = df_Portfolio.apply(
        lambda x: interest_coverage_fun(x["Initial Interest Coverage"], x['Borrower'], measurement_date, df_VAE),
        axis=1)

    df_VAE1['Net Senior Leverage'] = df_VAE1.apply(
        lambda x: Net_Senior_Leverage_fun(x['Senior Debt'], x['Unrestricted Cash'], x['TTM EBITDA']), axis=1)

    df_Portfolio['VAE Net Senior Leverage'] = df_Portfolio.apply(
        lambda x: VAE_Net_Senior_Leverage_fun(x['Permitted Net Senior Leverage CE'], x['Borrower'], measurement_date,
                                              df_VAE), axis=1)

    df_Portfolio['Net Senior Leverage Ratio Test'] = df_Portfolio.apply(
        lambda x: Net_Senior_Leverage_Ratio_Test_fun(x['Loan Type'], x['Permitted Net Senior Leverage'],
                                                     x['VAE Net Senior Leverage']), axis=1)

    df_Portfolio['Cash Interest Coverage Ratio Test'] = df_Portfolio.apply(
        lambda x: Cash_Interest_Coverage_Ratio_Test_fun(x['Loan Type'], x['Current Interest Coverage'],
                                                        x['Interest Coverage']), axis=1)

    df_Portfolio['Permitted Net Total Leverage'] = df_Portfolio.apply(
        lambda x: Permitted_Net_Total_Leverage_fun(x['Initial Total Debt'], x['Initial Unrestricted Cash'],
                                                   x['Permitted TTM EBITDA']), axis=1)

    df_VAE['Net Total Leverage'] = df_VAE.apply(
        lambda x: Net_Total_Leverage_fun(x['Total Debt'], x['Unrestricted Cash'], x['TTM EBITDA']), axis=1)

    df_Portfolio['VAE Net Total Leverage'] = df_Portfolio.apply(
        lambda x: VAE_Net_Total_Leverage_fun(x['Permitted Net Total Leverage'], x['Borrower'], measurement_date,
                                             df_VAE), axis=1)

    df_Portfolio['Net Total Leverage Ratio Test'] = df_Portfolio.apply(
        lambda x: Net_Total_Leverage_Ratio_Test_fun(x['Loan Type'], x['VAE Net Total Leverage'],
                                                    x['Permitted Net Total Leverage']), axis=1)

    df_Portfolio['Initial Multiple'] = df_Portfolio.apply(
        lambda x: Initial_Multiple_fun(x['Loan Type'], x['Initial Total Debt'], x['Initial Recurring Revenue']), axis=1)

    df_Portfolio['VAE Multiple'] = df_Portfolio.apply(
        lambda x: VAE_Multiple_fun(x['Loan Type'], x['Borrower'], measurement_date, x['Initial Multiple'], df_VAE),
        axis=1)

    df_Portfolio['Recurring Revenue Multiple'] = df_Portfolio.apply(
        lambda x: Recurring_Revenue_Multiple_fun(x['Loan Type'], x['Current Multiple'], x['VAE Multiple']), axis=1)

    df_Portfolio['VAE Liquidity'] = df_Portfolio.apply(
        lambda x: VAE_Liquidity_fun(x['Loan Type'], x['Borrower'], measurement_date, x['Initial Liquidity'], df_VAE),
        axis=1)

    df_Portfolio['Liquidity'] = df_Portfolio.apply(
        lambda x: Liquidity_fun(x['Loan Type'], x['Current Liquidity'], x['VAE Liquidity']), axis=1)

    df_Portfolio['VAE Trigger'] = df_Portfolio.apply(
        lambda x: VAE_Trigger_fun(x['Cash Interest Coverage Ratio Test'],
                                  x['Net Senior Leverage Ratio Test'], x['Net Total Leverage Ratio Test'],
                                  x['Recurring Revenue Multiple'], x['Liquidity'],
                                  x['Obligor Payment Default'], x['Default Rights/Remedies Exercised'],
                                  x['Reduces/waives Principal'], x['Extends Maturity/Payment Date'],
                                  x['Waives Interest'], x['Subordinates Loan'],
                                  x['Releases Collateral/Lien'], x['Amends Covenants'],
                                  x['Amends Permitted Lien or Indebtedness'], x['Insolvency Event'],
                                  x['Failure to Deliver Financial Statements']), axis=1)

    columns = {'Borrower': object, 'Event Type': object, 'Date of VAE Decision': str, 'Assigned Value': float,
               'Interest Coverage': float, 'TTM EBITDA': float, 'Senior Debt': float, 'Unrestricted Cash': float,
               'Total Debt': float, 'Liquidity': float}

    df_newVAE = pd.DataFrame(columns=columns)
    df_newVAE['Date of VAE Decision'] = df_newVAE['Date of VAE Decision'].astype('datetime64[ns]')

    condition = df_Portfolio['VAE Trigger'] == 'Yes'
    df_borrowers = df_Portfolio[condition]
    df_borrowers = df_borrowers[['Borrower']]

    global merged_df
    merged_df = pd.merge(df_borrowers, df_newVAE, on='Borrower', how='left')

    return pd.DataFrame(AvailabilityDict)

def serviceDivLayout(df_AdjustedIntermediate,df_Excess,borrower,df_AvailabilityOutput):
    return dbc.Container([
            html.Br(),
            html.Br(),
            dcc.Dropdown(
                id='dropdown',
                options=[
                    {'label': 'Intermediate results for Adjusted Borrowing Value', 'value': 'AdjBorrow'},
                    {'label': 'Intermediate results for Excess Concentration', 'value': 'ExcessC'},
                    {'label': 'Add new borrower', 'value': 'newBorrower'},
                    {'label': 'Remove borrower','value': 'remBorrower'},
                    {'label': 'Change EBITDA current', 'value': 'EBITDA'}
                ],
                value='',
                placeholder='Options',
            ),
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle('Intermediate results for Adjusted Borrowing Value')),
                    dbc.ModalBody([
                        returnDashDatable(df_AdjustedIntermediate, 'df_AdjustedIntermediate')
                    ]),
                    dbc.ModalFooter([
                        dbc.Button(
                            "Close", id="close1", className="ms-auto", n_clicks=0,
                            style={'border': '0', 'color': '#ffffff', 'font-weight': '500',
                                   'background-color': '#1ebea5',
                                   'border-radius': '5px'}
                        )],
                        style={'display': 'flex', 'justify-content': 'center'}
                    ),
                ],
                id="modal1",
                size='xl',
                scrollable=True,
                is_open=False,
            ),
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle('Intermediate results for Excess Concentration')),
                    dbc.ModalBody([
                        returnDashDatable(df_Excess, 'df_Excess')
                    ]),
                    dbc.ModalFooter(
                        dbc.Button(
                            "Close", id="close2", className="ms-auto", n_clicks=0,
                            style={'border': '0', 'color': '#ffffff', 'font-weight': '500',
                                   'background-color': '#1ebea5',
                                   'border-radius': '5px'}
                        )
                    ),
                ],
                id="modal2",
                size='xl',
                scrollable=True,
                is_open=False,
            ),
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Add a new borrower")),
                    dbc.ModalBody([
                        html.Form([html.Button('Download Example', type='submit', id='button',
                                               style={'border': '0', 'color': '#ffffff', 'font-weight': '500',
                                                      'background-color': '#1ebea5', 'padding': '10px',
                                                      'border-radius': '5px'})],
                                  action='download_example', method='get'),
                        html.Br(),
                        html.Form([dcc.Input(type='file', name='file'),
                                   dcc.Input(type='submit', name='Upload', value='Upload',
                                             style={'border': '0', 'color': '#ffffff', 'font-weight': '500',
                                                    'background-color': '#1ebea5', 'padding': '10px',
                                                    'border-radius': '5px'})],
                                  action='/new_borrowers', method='post', encType="multipart/form-data")
                    ]),
                    dbc.ModalFooter(
                        dbc.Button(
                            "Close", id="close3", className="ms-auto", n_clicks=0,
                            style={'border': '0', 'color': '#ffffff', 'font-weight': '500',
                                   'background-color': '#1ebea5',
                                   'border-radius': '5px'}
                        )
                    ),
                ],
                id="modal3",
                size='xl',
                scrollable=True,
                is_open=False,
            ),
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle('Remove Borrower')),
                    dbc.ModalBody([
                        returnDashDatableWithChecklist(borrower, "interactive-checklist"),
                        html.Br(),
                        html.Button(id='SubmitRem', name='Submit', value='Submit', n_clicks=0,
                                             style={'border': '0', 'color': '#ffffff', 'font-weight': '500',
                                                    'background-color': '#1ebea5', 'padding': '10px',
                                                    'border-radius': '5px'}),

                    ]),
                    dbc.ModalFooter(
                        dbc.Button(
                            "Close", id="close5", className="ms-auto", n_clicks=0,
                            style={'border': '0', 'color': '#ffffff', 'font-weight': '500',
                                   'background-color': '#1ebea5',
                                   'border-radius': '5px'}
                        )
                    ),
                ],
                id="modal5",
                size='xl',
                scrollable=True,
                is_open=False,
            ),
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Change EBITDA current")),
                    dbc.ModalBody([
                        html.Form(
                            [
                                html.Label("Current Adjusted TTM EBITDA",
                                           style={'whiteSpace': 'normal', 'display': 'inline-block', 'margin-right': 20,
                                                  'maxWidth': '500px'}),
                                dcc.Input(type="number", min="-99", max="100", id="adjusted_ttm_ebitda_current",
                                          name='Adjusted_TTM_EBITDA_Current',
                                          placeholder='Enter the percentage value'),
                                html.Br(),
                                html.Button("Submit", type='submit', id='button',
                                            style={'border': '0', 'color': '#ffffff', 'font-weight': '500',
                                                   'background-color': '#1ebea5', 'padding': '10px',
                                                   'border-radius': '5px'})
                            ], action='/analysis', method='post',
                            style={'display': 'flex', 'justify-content': 'center'})
                    ]),
                    dbc.ModalFooter(
                        dbc.Button(
                            "Close", id="close4", className="ms-auto", n_clicks=0,
                            style={'border': '0', 'color': '#ffffff', 'font-weight': '500',
                                   'background-color': '#1ebea5',
                                   'border-radius': '5px'}
                        )
                    ),
                ],
                id="modal4",
                size='xl',
                scrollable=True,
                is_open=False,
            ),
            html.Br(),
            html.H4("Availability Data"),

            returnDashDatable(df_AvailabilityOutput, 'df_AvailabilityOutput'),
            html.Br(),
            html.Form([html.Button('Download Results', type='submit', id='button',
                                   style={'background-color': '#1ebea5', 'border': '0px', 'border-radius': '5px',
                                          'padding': '10px',
                                          'color': '#ffffff',
                                          'font-weight': '500'})],
                      action='download_excel', method='get', style={'display': 'flex', 'justify-content': 'center'}),
            html.Br(),
        ])


# def calculate
def returnDashDatableWithChecklist(df, id):
    print(type(df))
    return dash_table.DataTable(
        df.to_dict('records'),
        style_data_conditional=[
            {
                "if": {"state": "selected"},
                "backgroundColor": "rgba(0, 116, 217, 0.3)",
                "border": "1px solid blue",
            },
        ],
        style_data={
            'color': 'black',
            'backgroundColor': 'white',
            'whiteSpace': 'normal',
            'height': 'auto',
        },
        style_header={
            'backgroundColor': 'rgb(30, 190, 165)',
            'color': '#ffffff',
            'text-align': 'center',
            'fontWeight': 'bold'
        },
        # filter_action="native",
        sort_action="native",
        sort_mode="multi",
        tooltip_duration=None,
        style_cell={'height': 'auto',
                    # all three widths are needed
                    'minWidth': '180px', 'width': '180px', 'maxWidth': '180px',
                    'whiteSpace': 'normal',
                    'textAlign': 'center'},
        style_cell_conditional=[
            {
                'if': {'column_id': c},
                'textAlign': 'left',
            } for c in ['Terms', 'Borrower', 'Loan Type']
        ],
        css=[{
            'selector': '.dash-cell div.dash-cell-value',
            'rule': 'display: inline; white-space: inherit; overflow: inherit; text-overflow: inherit;'
        }],
        style_table={'overflowX': 'scroll',
                     'overflowY': 'scroll'},
        row_selectable="multi",
        selected_rows=[],
        id=id)


def returnDashDatable(df, id):
    print(type(df))
    return dash_table.DataTable(
        df.to_dict('records'),
        [{"name": i, "id": i} for i in df.columns],
        style_data_conditional=[
            {
                "if": {"state": "selected"},
                "backgroundColor": "rgba(0, 116, 217, 0.3)",
                "border": "1px solid blue",
            },
        ],

        style_data={
            'color': 'black',
            'backgroundColor': 'white',
            'whiteSpace': 'normal',
            'height': 'auto',

        },
        style_header={
            'backgroundColor': 'rgb(30, 190, 165)',
            'color': '#ffffff',
            'text-align': 'center',
            'fontWeight': 'bold'
        },
        # filter_action="native",
        sort_action="native",
        sort_mode="multi",
        tooltip_duration=None,
        style_cell={'height': 'auto',
                    # all three widths are needed
                    'minWidth': '180px', 'width': '180px', 'maxWidth': '180px',
                    'whiteSpace': 'normal',
                    'textAlign': 'center'},
        style_cell_conditional=[
            {
                'if': {'column_id': c},
                'textAlign': 'left',

            } for c in ['Terms', 'Borrower', 'Loan Type']
        ],
        css=[{
            'selector': '.dash-cell div.dash-cell-value',
            'rule': 'display: inline; white-space: inherit; overflow: inherit; text-overflow: inherit;'
        }],
        style_table={'overflowX': 'scroll',
                     'overflowY': 'scroll'},
        id=id)


# @server.route('/')
# def index():
#     if request.method == 'GET':
#         return render_template('index.html')


swagger = Swagger(server)

upload_app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP], server=server, routes_pathname_prefix="/")

upload_app.layout = dbc.Container([
    html.Title('Upload'),
    html.Div([
        html.Img(src=app.get_asset_url('pepper-logo.svg')),
        html.H1('Leverage Modelling', style={'text-align': 'center', 'color': '#1ebea5', 'margin': '30px 0'}),
        html.Form([dcc.Input(type='file', name='file', ),
                   dcc.Input(type='submit', name='Upload', value='Upload',
                             style={'border': '0', 'padding': '10px', 'color': '#ffffff', 'font-weight': '500',
                                    'background-color': '#1ebea5', 'border-radius': '5px', 'border-radius': '5px'})],
                  action='/Service', method='post', encType="multipart/form-data",
                  )
    ], style={'width': '100%', 'height': '100vh', 'display': 'flex', 'justify-content': 'center',
              'flex-direction': 'column', 'align-items': 'center'}),
])


# @server.route('/', methods=['GET', 'POST'])
# def upload():
#     if request.method == 'GET':
#         return render_template('upload.html')

@server.route('/Service', methods=['POST'])
def service():
    if request.method == 'POST':
        f = request.files['file']
        f.save(f.filename)
    global df_Portfolio
    df_Portfolio = pd.read_excel(f.filename, sheet_name=0)

    global df_Tiers
    df_Tiers = pd.read_excel(f.filename, sheet_name=3)

    global df_Ebitda
    df_Ebitda = pd.read_excel(f.filename, sheet_name=4)

    global df_VAE
    df_VAE = pd.read_excel(f.filename, sheet_name=1)

    global df_Availability
    df_Availability = pd.read_excel(f.filename, sheet_name=2)

    global df_ExcessConcentration
    df_ExcessConcentration = pd.read_excel(f.filename, sheet_name=5)

    global df_Industries
    df_Industries = pd.read_excel(f.filename, sheet_name=6)

    global df_BorrowerOutstandings
    df_BorrowerOutstandings = pd.read_excel(f.filename, sheet_name=7)

    services_app.layout = dbc.Container([
        html.Br(),
        html.Div([
            dcc.Dropdown(
                id='dropdown-menu',
                options=[
                    {'label': 'Permitted TTM EBITDA',
                     'value': 'permittedTTMEBITDA'},
                    {'label': 'Permitted Net Senior Leverage',
                     'value': 'permittedNetSeniorLeverage'},
                    {'label': 'Permitted Net Total Leverage',
                     'value': 'permittedNetTotalLeverage'},
                    {'label': 'Excess concentration for top 5 Industries',
                     'value': 'Top5Industries'},
                    {'label': 'Excess concentration for top 5 Obligors',
                     'value': 'Top5Obligors'},
                    {'label': 'Complete Analysis',
                     'value': 'completeAnalysis'},
                ],
                value='',
                placeholder='Services',
            ),
            html.Div([html.Div([html.Div(id='dropdown-output2')],id='dropdown-output')], id='dropdown-output1')
        ])
    ])
    return redirect(url_for('/services/'))


services_app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP], server=server, routes_pathname_prefix='/services/')
services_app.layout = html.H1('Services')
services_app.config.suppress_callback_exceptions = True


@services_app.callback(
    Output('dropdown-output2', 'children'),
    [Input('dropdown-menu', 'value')])
def callback_services(value):
    # print(value)
    if value == 'completeAnalysis':
        global df_AvailabilityOutput
        df_AvailabilityOutput = calculateAvailability(df_Portfolio, df_Tiers, df_Ebitda, df_VAE, df_Availability,
                                                      df_ExcessConcentration, df_Industries, df_BorrowerOutstandings)
        borrowers = df_Portfolio['Borrower'].to_list()
        if len(merged_df) != 0:
            return dcc.Location(pathname="/updateVAE", id="someid_doesnt_matter")
        else:
            return serviceDivLayout(df_AdjustedIntermediate, df_Excess, df_Portfolio[['Borrower']], df_AvailabilityOutput)

    elif value == 'Top5Industries':
        df_AvailabilityOutput = calculateAvailability(df_Portfolio, df_Tiers, df_Ebitda, df_VAE, df_Availability,
                                                      df_ExcessConcentration, df_Industries, df_BorrowerOutstandings)
        result, df7 = top5LargestIndustries(df_Portfolio)
        return [result, html.Br(), returnDashDatable(df7, 'df7')]
    elif value == 'Top5Obligors':
        df_AvailabilityOutput = calculateAvailability(df_Portfolio, df_Tiers, df_Ebitda, df_VAE, df_Availability,
                                                      df_ExcessConcentration, df_Industries, df_BorrowerOutstandings)
        result1, df8 = Top5LargestExcess(df_Portfolio)
        return [result1, html.Br(), returnDashDatable(df8, 'df8')]
    elif value == 'permittedTTMEBITDA':
        permitted_ttm_ebitda_df = permittedTTMEBITDA_BZ(df_Portfolio, df_Ebitda, df_VAE)

        permitted_ttm_ebitda_df['Permitted TTM EBITDA Current'] = permitted_ttm_ebitda_df[
            'Permitted TTM EBITDA Current'].apply(int).map('${:,d}'.format)
        return returnDashDatable(permitted_ttm_ebitda_df, 'permitted_ttm_ebitda_df')
    elif value == 'permittedNetSeniorLeverage':
        permittedNetSeniorLeverage_df = permittedNetSeniorLeverage_CX(df_Portfolio, df_Ebitda, df_VAE)
        permittedNetSeniorLeverage_df['Permitted Net Senior Leverage'] = permittedNetSeniorLeverage_df[
            'Permitted Net Senior Leverage'].map('{:,.2f}'.format)
        return returnDashDatable(permittedNetSeniorLeverage_df, 'permittedNetSeniorLeverage_df')
    elif value == 'permittedNetTotalLeverage':
        permittedNetTotalLeverage_df = permittedNetTotalLeverage_CZ(df_Portfolio, df_Ebitda, df_VAE)
        permittedNetTotalLeverage_df['Permitted Net Total Leverage'] = permittedNetTotalLeverage_df[
            'Permitted Net Total Leverage'].map('{:,.2f}'.format)
        return returnDashDatable(permittedNetTotalLeverage_df, 'permittedNetTotalLeverage_df')


@services_app.callback(
    Output("modal1", "is_open"),
    [dependencies.Input('dropdown', 'value'), Input("close1", "n_clicks")],
    [State("modal1", "is_open")],
)
def toggle_modal1(value, n1, is_open):
    if value == 'AdjBorrow':
        return True
    elif n1:
        return False


@services_app.callback(
    Output("modal2", "is_open"),
    [dependencies.Input('dropdown', 'value'), Input("close2", "n_clicks")],
    [State("modal2", "is_open")],
)
def toggle_modal2(value, n1, is_open):
    if value == 'ExcessC':
        return True
    elif n1:
        return False




@services_app.callback(
    Output("modal3", "is_open"),
    [dependencies.Input('dropdown', 'value'), Input("close3", "n_clicks")],
    [State("modal3", "is_open")],
)
def toggle_modal3(value, n1, is_open):
    if value == 'newBorrower':
        return True
    elif n1:
        return False


@services_app.callback(
    Output("modal4", "is_open"),
    [dependencies.Input('dropdown', 'value'), Input("close4", "n_clicks")],
    [State("modal4", "is_open")],
)
def toggle_modal4(value, n1, is_open):
    if value == 'EBITDA':
        return True
    elif n1:
        return False


@services_app.callback(
    [Output('dropdown-output3', 'children')],
    [Input('SubmitRem', "n_clicks"),
     Input('interactive-checklist', "derived_virtual_data"),
     Input('interactive-checklist', "derived_virtual_selected_rows")])
def update_df(n, rows, derived_virtual_selected_rows):
    if n:
        if derived_virtual_selected_rows is None:
            derived_virtual_selected_rows = []
        # print(rows)
        remove_borrower_list = []
        for i in derived_virtual_selected_rows:
            remove_borrower_list.append(rows[i]['Borrower'])

        global df_Portfolio
        df_Portfolio = df_Portfolio[~df_Portfolio['Borrower'].isin(remove_borrower_list)]
        print("shape of dataframes: ",df_Portfolio.shape,df_Portfolio.shape)
        df_AvailabilityOutputRemBorrower = calculateAvailability(df_Portfolio, df_Tiers, df_Ebitda, df_VAE,
                                                                 df_Availability,
                                                                 df_ExcessConcentration, df_Industries,
                                                                 df_BorrowerOutstandings)

        df_AvailabilityOutputRemBorrower.rename(
            columns={'Values': 'Availability after removing a Borrower'}, inplace=True)
        global df_AvailabilityOutput
        df_AvailabilityOutput = df_AvailabilityOutput.merge(df_AvailabilityOutputRemBorrower, on='Terms')
        print(df_Portfolio[['Borrower']])
        return [serviceDivLayout(df_AdjustedIntermediate, df_Excess, df_Portfolio[['Borrower']], df_AvailabilityOutput)]


# def remove_borrower_update_layout(remove_borrower_list, df_Portfolio):
#     df_Portfolio_Updated = df_Portfolio[~df_Portfolio['Borrower'].isin(remove_borrower_list)]
#     df_AvailabilityOutputRemBorrower = calculateAvailability(df_Portfolio_Updated, df_Tiers, df_Ebitda, df_VAE,
#                                                              df_Availability,
#                                                              df_ExcessConcentration, df_Industries,
#                                                              df_BorrowerOutstandings)
#     return returnDashDatable(df_AvailabilityOutputRemBorrower, "df_AvailabilityOutputRemBorrower")


@services_app.callback(
    Output("modal5", "is_open"),
    [dependencies.Input('dropdown', 'value'), Input("close5", "n_clicks")],
    [State("modal5", "is_open")],
)
def toggle_modal5(value, n1, is_open):
    if value == 'remBorrower':
        return True
    elif n1:
        return False



# @server.route('/remove_borrowers', methods=['GET','POST'])
# def removBorrowers():
#     print(request.form)
#     dictBorrowers = request.form['interactive-checklist']
#     print(dictBorrowers)

@server.route('/permittedTTMEBITDA', methods=['GET', 'POST'])
def permittedTTMEBITDAservice():
    df_permittedTTMEBITDA = permittedTTMEBITDA_BZ(df_Portfolio, df_Ebitda, df_VAE)
    returnDashDatable(df_permittedTTMEBITDA, 'df_permittedTTMEBITDA')
    return redirect(url_for('/services'))


@server.route('/permittedNetSeniorLeverageService', methods=['GET', 'POST'])
def permittedNetSeniorLeverageService():
    df_permittedNetSeniorLeverageService = permittedNetSeniorLeverage_CX(df_Portfolio, df_Ebitda, df_VAE)
    returnDashDatable(df_permittedNetSeniorLeverageService, 'df_permittedNetSeniorLeverageService')
    return redirect(url_for('/services'))


@server.route('/permittedNetTotalLeverageService', methods=['GET', 'POST'])
def permittedNetTotalLeverageService():
    df_permittedNetTotalLeverage_CZ = permittedNetTotalLeverage_CZ(df_Portfolio, df_Ebitda, df_VAE)
    returnDashDatable(df_permittedNetTotalLeverage_CZ, 'df_permittedNetTotalLeverage_CZ')
    return redirect(url_for('/services'))


@server.route('/ExcessConcentrationTop5Industires', methods=['GET', 'POST'])
def ExcessConcentrationTop5IndustiresService():
    df_permittedNetTotalLeverage_CZ = permittedNetTotalLeverage_CZ(df_Portfolio, df_Ebitda, df_VAE)
    returnDashDatable(df_permittedNetTotalLeverage_CZ, 'df_permittedNetTotalLeverage_CZ')
    return redirect(url_for('/services'))


@server.route('/UpdateData', methods=['GET', 'POST'])
def updateData():
    update_app.layout = dbc.Container([
        html.Form(
            [
                html.Label("Current Adjusted TTM EBITDA"
                           # style={'whiteSpace': 'normal', 'display': 'inline-block', 'margin-right': 20,
                           #        'maxWidth': '500px'}
                           ),
                dcc.Input(type="number", min="-99", max="100", id="adjusted_ttm_ebitda_current",
                          name='Adjusted_TTM_EBITDA_Current',
                          placeholder='Enter the percentage value'),
                html.Br(),
                html.Br(),
                html.Button("Submit", type='submit', id='button',
                            style={'border': '0', 'color': '#ffffff', 'font-weight': '500',
                                   'background-color': '#1ebea5', 'padding': '10px', 'border-radius': '5px'})
            ], action='/analysis', method='post')
    ])

    return redirect(url_for('/UpdateData/'))


update_app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP], server=server, routes_pathname_prefix='/UpdatedData/')
update_app.layout = html.H1('Updated values page')


@server.route('/updateVAE')
def updateVAE():
    updateVAE_app.layout = dbc.Container([
        html.Br(),
        html.Div(id='temp_div'),
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Update the Borrower details")),
                dbc.ModalBody([
                    html.Form([html.Button('Change VAE', type='submit', id='button',
                                           style={'border': '0', 'color': '#ffffff', 'font-weight': '500',
                                                  'background-color': '#1ebea5', 'padding': '10px',
                                                  'border-radius': '5px'})],
                              action='download_VAE', method='get'),
                    # html.Br(),
                    # html.Form([html.Button('Continue without change', type='submit', id='button',)],
                    #           action='/dash/', method='get'),
                    html.Br(),
                    html.Form([dcc.Input(type='file', name='file'),
                               dcc.Input(type='submit', name='Upload', value='Upload',
                                         style={'border': '0', 'color': '#ffffff', 'font-weight': '500',
                                                'background-color': '#1ebea5', 'padding': '10px',
                                                'border-radius': '5px'})],
                              action='/newVAE', method='post', encType="multipart/form-data"),
                    html.Br(),
                    returnDashDatable(merged_df, 'merged_df'),
                ]),
                dbc.ModalFooter(
                    [html.Button('Continue without change', type='submit', id='continue',
                                           style={'border': '0', 'color': '#ffffff', 'font-weight': '500',
                                                  'background-color': '#1ebea5', 'padding': '10px',
                                                  'border-radius': '5px'})],
                              ),
            ],
            id="modal5",
            size='xl',
            scrollable=True,
            is_open=True,
        ),
    ])

    return redirect(url_for('/updatedVAE/'))


updateVAE_app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP], server=server, routes_pathname_prefix='/updatedVAE/')
updateVAE_app.layout = html.H1('Updated VAE')

@updateVAE_app.callback(
    Output('temp_div', 'children'),
    [Input('continue', "n_clicks")])
def update_services_app(n):
    if n:
        return dcc.Location(pathname="/redirect_services", id="someid_doesnt_matter")
@server.route('/redirect_services')
def temp_service_redirect():
    # print('In redirect')
    services_app.layout = dbc.Container([
        html.Br(),
        html.Div([
            dcc.Dropdown(
                id='dropdown-menu',
                options=[
                    {'label': 'Permitted TTM EBITDA',
                     'value': 'permittedTTMEBITDA'},
                    {'label': 'Permitted Net Senior Leverage',
                     'value': 'permittedNetSeniorLeverage'},
                    {'label': 'Permitted Net Total Leverage',
                     'value': 'permittedNetTotalLeverage'},
                    {'label': 'Excess concentration for top 5 Industries',
                     'value': 'Top5Industries'},
                    {'label': 'Excess concentration for top 5 Obligors',
                     'value': 'Top5Obligors'},
                    {'label': 'Complete Analysis',
                     'value': 'completeAnalysis'},
                ],
                value='',
                placeholder='Services',
            ),
            html.Div([serviceDivLayout(df_AdjustedIntermediate, df_Excess, df_Portfolio[['Borrower']], df_AvailabilityOutput)], id='dropdown-output3'),
            html.Div(children=[html.Div([html.Div(id='dropdown-output2')],id='dropdown-output')], id='dropdown-output1'),

        ])
    ])
    return redirect(url_for('/services/'))




@app.callback(
    Output("modal5", "is_open"),
    [Input("close5", "n_clicks")],
    [State("modal5", "is_open")],
)
def toggle_modal5(value, n1, is_open):
    if n1:
        return not is_open


@server.route('/view_file', methods=['POST'])
@swag_from("api_doc.yml")
def view():
    # if request.method == 'POST':
    #     f = request.files['file']
    #     f.save(f.filename)
    #     # print(f)
    # Dict = {}
    # Dict['df_Portfolio'] = df_Portfolio.to_dict
    # Universal Values used in computation
    # global df_AvailabilityOutput
    global df_AvailabilityOutput
    df_AvailabilityOutput = calculateAvailability(df_Portfolio, df_Tiers, df_Ebitda, df_VAE, df_Availability,
                                                  df_ExcessConcentration, df_Industries, df_BorrowerOutstandings)
    borrowers = df_Portfolio["Borrower"].to_list()
    app.layout = dbc.Container([
        html.Br(),
        html.Div([
            html.Button("Open Checklist", id="open-checklist-button", n_clicks=0),
            html.Div(id="checklist-modal", style={"display": "none"})
        ]),
        html.Br(),
        dcc.Dropdown(
            id='dropdown',
            options=[
                {'label': 'Intermediate results for Adjusted Borrowing Value', 'value': 'AdjBorrow'},
                {'label': 'Intermediate results for Excess Concentration', 'value': 'ExcessC'},
                {'label': 'Add new borrower', 'value': 'newBorrower'},
                {'label': 'Change EBITDA current', 'value': 'EBITDA'},
                {'label': 'Remove borrower', 'value': 'remBorrower'}
            ],
            value='',
            placeholder='Options',
        ),
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle('Intermediate results for Adjusted Borrowing Value')),
                dbc.ModalBody([
                    returnDashDatable(df_AdjustedIntermediate, 'df_AdjustedIntermediate')
                ]),
                dbc.ModalFooter([
                    dbc.Button(
                        "Close", id="close1", className="ms-auto", n_clicks=0,
                        style={'border': '0', 'color': '#ffffff', 'font-weight': '500', 'background-color': '#1ebea5',
                               'border-radius': '5px'}
                    )],
                    style={'display': 'flex', 'justify-content': 'center'}
                ),
            ],
            id="modal1",
            size='xl',
            scrollable=True,
            is_open=False,
        ),
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle('Intermediate results for Excess Concentration')),
                dbc.ModalBody([
                    returnDashDatable(df_Excess, 'df_Excess')
                ]),
                dbc.ModalFooter(
                    dbc.Button(
                        "Close", id="close2", className="ms-auto", n_clicks=0,
                        style={'border': '0', 'color': '#ffffff', 'font-weight': '500', 'background-color': '#1ebea5',
                               'border-radius': '5px'}
                    )
                ),
            ],
            id="modal2",
            size='xl',
            scrollable=True,
            is_open=False,
        ),
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Add a new borrower")),
                dbc.ModalBody([
                    html.Form([html.Button('Download Example', type='submit', id='button',
                                           style={'border': '0', 'color': '#ffffff', 'font-weight': '500',
                                                  'background-color': '#1ebea5', 'padding': '10px',
                                                  'border-radius': '5px'})],
                              action='download_example', method='get'),
                    html.Br(),
                    html.Form([dcc.Input(type='file', name='file'),
                               dcc.Input(type='submit', name='Upload', value='Upload',
                                         style={'border': '0', 'color': '#ffffff', 'font-weight': '500',
                                                'background-color': '#1ebea5', 'padding': '10px',
                                                'border-radius': '5px'})],
                              action='/new_borrowers', method='post', encType="multipart/form-data")
                ]),
                dbc.ModalFooter(
                    dbc.Button(
                        "Close", id="close3", className="ms-auto", n_clicks=0,
                        style={'border': '0', 'color': '#ffffff', 'font-weight': '500', 'background-color': '#1ebea5',
                               'border-radius': '5px'}
                    )
                ),
            ],
            id="modal3",
            size='xl',
            scrollable=True,
            is_open=False,
        ),
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Change EBITDA current")),
                dbc.ModalBody([
                    html.Form(
                        [
                            html.Label("Current Adjusted TTM EBITDA",
                                       style={'whiteSpace': 'normal', 'display': 'inline-block', 'margin-right': 20,
                                              'maxWidth': '500px'}),
                            dcc.Input(type="number", min="-99", max="100", id="adjusted_ttm_ebitda_current",
                                      name='Adjusted_TTM_EBITDA_Current',
                                      placeholder='Enter the percentage value'),
                            html.Br(),
                            html.Button("Submit", type='submit', id='button',
                                        style={'border': '0', 'color': '#ffffff', 'font-weight': '500',
                                               'background-color': '#1ebea5', 'padding': '10px',
                                               'border-radius': '5px'})
                        ], action='/analysis', method='post', style={'display': 'flex', 'justify-content': 'center'})
                ]),
                dbc.ModalFooter(
                    dbc.Button(
                        "Close", id="close4", className="ms-auto", n_clicks=0,
                        style={'border': '0', 'color': '#ffffff', 'font-weight': '500', 'background-color': '#1ebea5',
                               'border-radius': '5px'}
                    )
                ),
            ],
            id="modal4",
            size='xl',
            scrollable=True,
            is_open=False,
        ),
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle('Remove Borrower')),
                dbc.ModalBody([
                    dash_table.DataTable(
                        id='datatable-interactivity',
                        columns=[
                            {"name": 'Borrower', "id": 'Borrower', "deletable": True, "selectable": True}
                        ],

                        row_selectable="multi",
                        row_deletable=True,
                        selected_rows=[],

                    ),
                ]),
                dbc.ModalFooter(
                    dbc.Button(
                        "Close", id="close5", className="ms-auto", n_clicks=0,
                        style={'border': '0', 'color': '#ffffff', 'font-weight': '500', 'background-color': '#1ebea5',
                               'border-radius': '5px'}
                    )
                ),
            ],
            id="modal6",
            size='xl',
            scrollable=True,
            is_open=False,
        ),
        html.Br(),
        html.H4("Availability Data"),

        returnDashDatable(df_AvailabilityOutput, 'df_AvailabilityOutput'),
        html.Br(),
        html.Form([html.Button('Download Results', type='submit', id='button',
                               style={'background-color': '#1ebea5', 'border': '0px', 'border-radius': '5px',
                                      'padding': '10px',
                                      'color': '#ffffff',
                                      'font-weight': '500'})],
                  action='download_excel', method='get', style={'display': 'flex', 'justify-content': 'center'}),
        html.Br(),
    ])
    # return html_string
    # output = BytesIO()
    # writer = pd.ExcelWriter(output, engine='xlsxwriter')
    # # print(df_Portfolio.head())
    # df_AvailabilityOutput.to_excel(writer, index=False, sheet_name='Availability')
    # writer.save()
    # writer.close()
    # output.seek(0)
    # #send_file(output, download_name='Availability.xlsx', as_attachment=True)
    # return dumps(df_AvailabilityOutput.to_dict(orient='records'), indent=4)
    if len(merged_df) != 0:
        return redirect('/updateVAE')
    return redirect(url_for('/dash/'))


@app.callback(
    Output("modal1", "is_open"),
    [dependencies.Input('dropdown', 'value'), Input("close1", "n_clicks")],
    [State("modal1", "is_open")],
)
def toggle_modal1(value, n1, is_open):
    if value == 'AdjBorrow' or n1:
        return not is_open


@app.callback(
    Output("modal2", "is_open"),
    [dependencies.Input('dropdown', 'value'), Input("close2", "n_clicks")],
    [State("modal2", "is_open")],
)
def toggle_modal2(value, n1, is_open):
    if value == 'ExcessC' or n1:
        return not is_open


@app.callback(
    Output("modal3", "is_open"),
    [dependencies.Input('dropdown', 'value'), Input("close3", "n_clicks")],
    [State("modal3", "is_open")],
)
def toggle_modal3(value, n1, is_open):
    if value == 'newBorrower' or n1:
        return not is_open


@app.callback(
    Output("modal4", "is_open"),
    [dependencies.Input('dropdown', 'value'), Input("close4", "n_clicks")],
    [State("modal4", "is_open")],
)
def toggle_modal4(value, n1, is_open):
    if value == 'EBITDA' or n1:
        return not is_open


@server.route('/analysis', methods=['POST'])
def updateAvailability():
    percentage_change1 = float(request.form['Adjusted_TTM_EBITDA_Current'])
    percentage_change = 1 + (percentage_change1 / 100)
    print(percentage_change)
    updated_df_Portfolio = df_Portfolio.copy(deep=True)
    updated_df_Portfolio['Adjusted TTM EBITDA_Current'] = df_Portfolio[
                                                              'Adjusted TTM EBITDA_Current'] * percentage_change
    Updated_df_AvailabilityOutput = calculateAvailability(updated_df_Portfolio, df_Tiers, df_Ebitda, df_VAE,
                                                          df_Availability,
                                                          df_ExcessConcentration, df_Industries,
                                                          df_BorrowerOutstandings)

    Updated_df_AvailabilityOutput.rename(
        columns={'Values': f'{round(percentage_change1, 2)} % Change in EBITDA'}, inplace=True)
    global df_AvailabilityOutput
    df_AvailabilityOutput = df_AvailabilityOutput.merge(Updated_df_AvailabilityOutput, on='Terms')
    # df_AvailabilityOutput.merge(Updated_df_AvailabilityOutput, on='Terms')

    services_app.layout = dbc.Container([
        html.Br(),
        html.Div([
            dcc.Dropdown(
                id='dropdown-menu',
                options=[
                    {'label': 'Permitted TTM EBITDA',
                     'value': 'permittedTTMEBITDA'},
                    {'label': 'Permitted Net Senior Leverage',
                     'value': 'permittedNetSeniorLeverage'},
                    {'label': 'Permitted Net Total Leverage',
                     'value': 'permittedNetTotalLeverage'},
                    {'label': 'Excess concentration for top 5 Industries',
                     'value': 'Top5Industries'},
                    {'label': 'Excess concentration for top 5 Obligors',
                     'value': 'Top5Obligors'},
                    {'label': 'Complete Analysis',
                     'value': 'completeAnalysis'},
                ],
                value='',
                placeholder='Services',
            ),
            html.Div([serviceDivLayout(df_AdjustedIntermediate, df_Excess, df_Portfolio[['Borrower']],
                                       df_AvailabilityOutput)], id='dropdown-output5'),
            html.Div(children=[html.Div([html.Div(id='dropdown-output2')], id='dropdown-output')],
                     id='dropdown-output1'),

        ])
    ])

    return redirect(url_for('/services/'))


@server.route('/new_borrowers', methods=['POST'])
def newBorrower():
    f1 = request.files['file']
    f1.save(f1.filename)
    df_newPortfolio = pd.read_excel(f1.filename, sheet_name=0)
    df_newVAE = pd.read_excel(f1.filename, sheet_name=1)

    df_UpdatedPortfolio = df_Portfolio.copy(deep=True)
    df_UpdatedVAE = df_VAE.copy(deep=True)

    df_UpdatedPortfolio = pd.concat([df_UpdatedPortfolio, df_newPortfolio], ignore_index=True, sort=False)
    df_UpdatedVAE = pd.concat([df_UpdatedVAE, df_newVAE], ignore_index=True, sort=False)

    df_NewAvailabilityOutput = calculateAvailability(df_UpdatedPortfolio, df_Tiers, df_Ebitda, df_UpdatedVAE,
                                                     df_Availability,
                                                     df_ExcessConcentration, df_Industries,
                                                     df_BorrowerOutstandings)
    df_NewAvailabilityOutput.rename(
        columns={'Values': 'Availability with new Borrower'}, inplace=True)
    global df_AvailabilityOutput
    df_AvailabilityOutput = df_AvailabilityOutput.merge(df_NewAvailabilityOutput, on='Terms')

    services_app.layout = dbc.Container([
        html.Br(),
        html.Div([
            dcc.Dropdown(
                id='dropdown-menu',
                options=[
                    {'label': 'Permitted TTM EBITDA',
                     'value': 'permittedTTMEBITDA'},
                    {'label': 'Permitted Net Senior Leverage',
                     'value': 'permittedNetSeniorLeverage'},
                    {'label': 'Permitted Net Total Leverage',
                     'value': 'permittedNetTotalLeverage'},
                    {'label': 'Excess concentration for top 5 Industries',
                     'value': 'Top5Industries'},
                    {'label': 'Excess concentration for top 5 Obligors',
                     'value': 'Top5Obligors'},
                    {'label': 'Complete Analysis',
                     'value': 'completeAnalysis'},
                ],
                value='',
                placeholder='Services',
            ),
            html.Div([serviceDivLayout(df_AdjustedIntermediate, df_Excess, df_Portfolio[['Borrower']],
                                       df_AvailabilityOutput)], id='dropdown-output4'),
            html.Div(children=[html.Div([html.Div(id='dropdown-output2')], id='dropdown-output')],
                     id='dropdown-output1'),

        ])
    ])

    return redirect(url_for('/services/'))


@server.route('/newVAE', methods=['POST'])
def newVAE():
    f2 = request.files['file']
    f2.save(f2.filename)
    # df_newPortfolio = pd.read_excel(f2.filename, sheet_name=0)
    df_newVAEDetails = pd.read_excel(f2.filename, sheet_name=0)

    # df_UpdatedPortfolio = df_Portfolio.copy(deep=True)
    df_UpdatedVAE = df_VAE.copy(deep=True)

    # df_UpdatedPortfolio = pd.concat([df_UpdatedPortfolio, df_newPortfolio], ignore_index=True, sort=False)
    df_newVAEDetails = pd.concat([df_UpdatedVAE, df_newVAEDetails], ignore_index=True, sort=False)
    print(df_newVAEDetails)
    df_newVAEDetails = df_newVAEDetails.drop(['Net Senior Leverage', 'Net Total Leverage'], axis=1)
    print(df_newVAEDetails)
    df_NewAvailabilityVAE = calculateAvailability(df_Portfolio, df_Tiers, df_Ebitda, df_newVAEDetails,
                                                  df_Availability,
                                                  df_ExcessConcentration, df_Industries,
                                                  df_BorrowerOutstandings)

    df_NewAvailabilityVAE.rename(
        columns={'Values': 'Updated after VAE trigger'}, inplace=True)
    global df_AvailabilityOutput
    df_AvailabilityOutput = df_AvailabilityOutput.merge(df_NewAvailabilityVAE, on='Terms')

    services_app.layout = dbc.Container([
        html.Br(),
        html.Div([
            dcc.Dropdown(
                id='dropdown-menu',
                options=[
                    {'label': 'Permitted TTM EBITDA',
                     'value': 'permittedTTMEBITDA'},
                    {'label': 'Permitted Net Senior Leverage',
                     'value': 'permittedNetSeniorLeverage'},
                    {'label': 'Permitted Net Total Leverage',
                     'value': 'permittedNetTotalLeverage'},
                    {'label': 'Excess concentration for top 5 Industries',
                     'value': 'Top5Industries'},
                    {'label': 'Excess concentration for top 5 Obligors',
                     'value': 'Top5Obligors'},
                    {'label': 'Complete Analysis',
                     'value': 'completeAnalysis'},
                ],
                value='',
                placeholder='Services',
            ),
            html.Div([serviceDivLayout(df_AdjustedIntermediate, df_Excess, df_Portfolio[['Borrower']],
                                       df_AvailabilityOutput)], id='dropdown-output3'),
            html.Div(children=[html.Div([html.Div(id='dropdown-output2')], id='dropdown-output')],
                     id='dropdown-output1'),

        ])
    ])

    return redirect(url_for('/services/'))


@server.route("/services/download_excel", methods=['GET', 'POST'])
def downloadExcel():
    if request.method == 'GET':
        # df = session.get('df', None)
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        # print(df_Portfolio.head())
        df_AvailabilityOutput.to_excel(writer, index=False, sheet_name='Availability')
        df_Portfolio.to_excel(writer, index=False, sheet_name='Portfolio')
        df_ExcessConcentration.to_excel(writer, index=False, sheet_name='Excess Concentration')
        df_Availability.to_excel(writer, index=False, sheet_name='Availability values')
        df_Tiers.to_excel(writer, index=False, sheet_name='Tiers')
        df_Ebitda.to_excel(writer, index=False, sheet_name='EBITDA Values')
        df_Industries.to_excel(writer, index=False, sheet_name='Industries')
        df_VAE.to_excel(writer, index=False, sheet_name='VAE')
        # writer.save()
        writer.close()
        output.seek(0)
        # xlsx_data = output.getvalue()
        return send_file(output, download_name='Availability.xlsx', as_attachment=True)


@server.route("/services/download_example", methods=['GET', 'POST'])
def downloadExample():
    if request.method == 'GET':
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df_newBorrowerPortfolio.to_excel(writer, index=False, sheet_name='Portfolio_Example')
        df_newBorrowerVAE.to_excel(writer, index=False, sheet_name='VAE_Example')
        writer.close()
        output.seek(0)
        return send_file(output, download_name='PortfolioExample.xlsx', as_attachment=True)


@server.route("/updatedVAE/download_VAE", methods=['GET', 'POST'])
def downloadVAE():
    if request.method == 'GET':
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        merged_df.to_excel(writer, index=False, sheet_name='VAE Details')
        writer.close()
        output.seek(0)
        return send_file(output, download_name='NewBorrowerVAEDetails.xlsx', as_attachment=True)


if __name__ == '__main__':
    server.run(host='0.0.0.0', debug=True)
