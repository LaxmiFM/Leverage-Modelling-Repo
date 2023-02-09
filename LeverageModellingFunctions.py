import numpy as np
import pandas as pd
import yearfrac as yf
from datetime import datetime


# Add Back Percentage
def Add_Back_Percentage(COl_AdjTTMEbitda, Col_EbitdaAddback):
    if (COl_AdjTTMEbitda - Col_EbitdaAddback) < 0:
        return 'N/A'
    elif Col_EbitdaAddback == 0:
        return 0
    else:
        return Col_EbitdaAddback / (COl_AdjTTMEbitda - Col_EbitdaAddback)


# Capped add Back Percentage
def Capped_Addback_Percentage(Col_LoanType, Col_Rated_B, Col_AdjTTMEbitda, Col_EbitdaAddback,
                              Col_InitialDebtToCashRatio, EBITDA_Addback_3, EBITDA_Addback_1, Add_Backs_10MM,
                              Add_Backs_10_50MM, Add_Backs_50MM):
    if (Col_LoanType == 'Recurring Revenue') or (
            (Col_Rated_B == 'Yes' and (Col_AdjTTMEbitda - Col_EbitdaAddback > EBITDA_Addback_3))):
        return None
    elif ((Col_AdjTTMEbitda - Col_EbitdaAddback) < EBITDA_Addback_1) and (
            np.isnan(Col_InitialDebtToCashRatio) == False) and (Col_InitialDebtToCashRatio <= 0.35):
        return Add_Backs_10MM
    elif ((Col_AdjTTMEbitda - Col_EbitdaAddback) < EBITDA_Addback_1) and (
            np.isnan(Col_InitialDebtToCashRatio) or Col_InitialDebtToCashRatio > 0.35):
        return 0.15
    elif ((Col_AdjTTMEbitda - Col_EbitdaAddback) > EBITDA_Addback_1) and (
            Col_AdjTTMEbitda - Col_EbitdaAddback) < EBITDA_Addback_3 and np.isnan(
        Col_InitialDebtToCashRatio) == False and Col_InitialDebtToCashRatio <= 0.50:
        return Add_Backs_10_50MM
    elif ((Col_AdjTTMEbitda - Col_EbitdaAddback) > EBITDA_Addback_1) and (
            Col_AdjTTMEbitda - Col_EbitdaAddback) < EBITDA_Addback_3 and (
            np.isnan(Col_InitialDebtToCashRatio) or Col_InitialDebtToCashRatio > 0.50):
        return 0.20
    elif ((Col_AdjTTMEbitda - Col_EbitdaAddback) >= EBITDA_Addback_3) and np.isnan(
            Col_InitialDebtToCashRatio) == False and Col_InitialDebtToCashRatio <= 0.50:
        return Add_Backs_50MM
    elif ((Col_AdjTTMEbitda - Col_EbitdaAddback) >= EBITDA_Addback_3) and (
            np.isnan(Col_InitialDebtToCashRatio) or (Col_InitialDebtToCashRatio > 0.50)):
        return 0.25


# Calculates Excess Add Backs
def Excess_AddBacks(Col_AdjTTMEbitda, Col_EbitdaAddback, Col_AddBackPercentage, Col_CappedAddBack):
    if Col_AdjTTMEbitda - Col_EbitdaAddback < 0:
        return Col_EbitdaAddback
    elif Col_AddBackPercentage >= Col_CappedAddBack:
        return Col_EbitdaAddback - ((Col_AdjTTMEbitda - Col_EbitdaAddback) * Col_CappedAddBack)
    else:
        return 0


# To calculate Permitted TTM EBITDA
def Permitted_TTM_EBITDA(Col_AdjTTMEbitda, Col_ExcessAddBacks, Col_AgentAddBacks):
    return Col_AdjTTMEbitda - Col_ExcessAddBacks + Col_AgentAddBacks


# EBITDA Haircut
def EBITDA_Haircut(Col_Permitted_TTM_EBITDA, Col_AdjTTMEbitda):
    return 1 - (Col_Permitted_TTM_EBITDA / Col_AdjTTMEbitda)


def Inclusion_EBITDA_Haircut(Col_Borrower, VAE_dataframe, Col_EBITDA_Haircut):
    EventType = "(A) Credit Quality Deterioration Event"
    VAE_dataframe = VAE_dataframe[VAE_dataframe['Event Type'] == EventType]
    count = len(VAE_dataframe)
    if count >= 1:
        return 0
    else:
        return Col_EBITDA_Haircut


# Permitted TTM EBITDA Current (BZ)
def Permitted_TTM_EBITDA_Current(Col_AgentPostInclAdjHaircut, Col_InclusionEBITDAHaircut, Col_AdjustedTTMEBITDACurrent,
                                 Col_AgentAdjAddbackHaircut):
    if Col_AgentPostInclAdjHaircut == 'N':
        return (1 - Col_InclusionEBITDAHaircut) * Col_AdjustedTTMEBITDACurrent
    else:
        return (1 - Col_AgentAdjAddbackHaircut) * Col_AdjustedTTMEBITDACurrent


# Permitted Net Senior Leverage (CX)
def Permitted_Net_senior_Leverage(Col_SeniorDebt, Col_CurrentUnrestrictedCash, Col_Permitted_EBITDATTMCurrent):
    try:
        return (Col_SeniorDebt - Col_CurrentUnrestrictedCash) / Col_Permitted_EBITDATTMCurrent
    except:
        return '-'


# Amounts in excess of Tier 3 Reclassified as zero value (V)

def Amounts_in_excess_of_Tier_3(Col_LoanType, Col_PermittedNetSeniorLeverage, Col_BorrowerOtstandingPrincipalBalance,
                                Tier_3_2L):
    try:
        if (Col_LoanType == 'Second Lien' or Col_LoanType == 'Last Out' or Col_LoanType == 'Recurring Revenue'):
            return 0
        elif Col_PermittedNetSeniorLeverage > Tier_3_2L:
            return ((
                            Col_PermittedNetSeniorLeverage - Tier_3_2L) / Col_PermittedNetSeniorLeverage) * Col_BorrowerOtstandingPrincipalBalance
        else:
            return 0
    except:
        return '-'


# Amounts in excess of Tier 3 Reclassified as 2nd Lien (U)

def Amounts_excess_of_Tier3_Reclassified_2nd_Lien(Col_LoanType, Col_AmountsExcessTier3ReclassifiedZeroValue,
                                                  Col_PermittedNetSeniorLeverage,
                                                  Col_BorrowerOtstandingPrincipalBalance, Tier_3_1L):
    try:
        if (Col_LoanType == 'Second Lien' or Col_LoanType == 'Last Out' or Col_LoanType == 'Recurring Revenue'):
            return 0 - Col_AmountsExcessTier3ReclassifiedZeroValue
        elif Col_PermittedNetSeniorLeverage > Tier_3_1L:
            return (((
                             Col_PermittedNetSeniorLeverage - Tier_3_1L) / Col_PermittedNetSeniorLeverage) * Col_BorrowerOtstandingPrincipalBalance) - Col_AmountsExcessTier3ReclassifiedZeroValue
        else:
            return 0 - Col_AmountsExcessTier3ReclassifiedZeroValue
    except:
        return '-'


# First Lien Amount (W)
def First_Lien_Amount(Col_LoanType, Col_BorrowerOtstandingPrincipalBalance, Col_AmountsExcessTier3Reclassified2ndLien,
                      Col_AmountsExcessTier3ReclassifiedZeroValue):
    try:
        if Col_LoanType == 'Second Lien' or Col_LoanType == 'Last Out' or Col_LoanType == 'Recurring Revenue':
            return 0
        else:
            return Col_BorrowerOtstandingPrincipalBalance - Col_AmountsExcessTier3Reclassified2ndLien - Col_AmountsExcessTier3ReclassifiedZeroValue
    except:
        return '-'


# Calculations for Assigned Value (T) start from here.
# T--> S--> AL--> AU
# EBITDA > $5MM (AU)

def EBITDA_5MM(Col_Permitted_TTM_EBITDA):
    try:
        if Col_Permitted_TTM_EBITDA > 5000000:
            return 'Yes'
        else:
            return 'No'
    except:
        return '-'


# Second Lien or FLLO EBITDA >$10MM
def Second_Lien_Or_FLLO_EBITDA(Col_LoanType, Col_Permitted_TTM_EBITDA):
    try:
        if Col_LoanType == 'Second Lien' or Col_LoanType == 'Last Out':
            if Col_Permitted_TTM_EBITDA > 10000000:
                return 'Yes'
            else:
                return 'No'
        else:
            return 'na'
    except:
        return '-'


# Eligible Cov-Lite (AW)
def Eligible_Cov_Lite(Col_Cov_Lite, Col_Permitted_TTM_EBITDA, Col_Initial_Senior_Debt, Col_RatedBOrBetter):
    try:
        if Col_Cov_Lite == 'Yes':
            if Col_Permitted_TTM_EBITDA > 50000000 and Col_Initial_Senior_Debt > 200000000 and Col_RatedBOrBetter == 'Yes':
                return 'Yes'
            else:
                return 'No'
        else:
            return 'na'
    except:
        return '-'


# Eligible Recurring Revenue (AX)
def Eligible_recurring_revenue(Col_LoanType, Col_InitialRecurringRevenue, Col_InitialTotalDebt):
    try:
        if Col_LoanType == 'Recurring Revenue':
            if (Col_InitialRecurringRevenue > 200000000) and (((
                    Col_InitialTotalDebt / Col_InitialRecurringRevenue) if Col_LoanType == 'Recurring Revenue' else 0) < 2.5):
                return 'Yes'
            else:
                return 'No'
        else:
            return 'na'
    except:
        return '-'


# Eligibility Check (AL)

def Eligibility_Check(Col_EligibleLoan, Col_EBITDA_5MM, Col_SecondLienOrFLLOEBITDA10MM, Col_EligibleCovLite,
                      Col_EligibleRecurringRevenue, Col_PermittedTTMEBITDACurrent):
    if Col_EligibleLoan == 'No':
        return 'No'
    elif Col_EBITDA_5MM == 'No' or Col_SecondLienOrFLLOEBITDA10MM or Col_EligibleCovLite == 'No' or Col_EligibleRecurringRevenue == 'No':
        return 'No'
    elif Col_PermittedTTMEBITDACurrent < 0:
        return 'No'
    else:
        return 'Yes'


# Eligibility Check (AL)

def Eligibility_Check(Col_EligibleLoan, Col_EBITDA_5MM, Col_SecondLienOrFLLOEBITDA10MM, Col_EligibleCovLite,
                      Col_EligibleRecurringRevenue, Col_PermittedTTMEBITDACurrent):
    if Col_EligibleLoan == 'No':
        return 'No'
    elif (
            Col_EBITDA_5MM == 'No' or Col_SecondLienOrFLLOEBITDA10MM == 'No' or Col_EligibleCovLite == 'No' or Col_EligibleRecurringRevenue == 'No'):
        return 'No'
    elif Col_PermittedTTMEBITDACurrent < 0:
        return 'No'
    else:
        return 'Yes'


# Permitted Net Total Leverage (CZ)
def permittedNetTotalLeverage(Col_TotalDebt, Col_CurrentUnrestrictedCash, Col_PermittedTTMEBITDACurrent):
    try:
        return (Col_TotalDebt - Col_CurrentUnrestrictedCash) / Col_PermittedTTMEBITDACurrent
    except:
        return '-'


# Current Multiple (CO)

def currentMultiple(Col_LoanType, Col_TotalDebt, Col_CurrentRecurringRevenue):
    if Col_LoanType == 'Recurring Revenue':
        return Col_TotalDebt / Col_CurrentRecurringRevenue
    else:
        return 0


# Applicable Collateral value (S)

def applicableCollateralValue(Col_EligibilityCheck, Col_LoanType, Col_PermittedNetSeniorLeverage,
                              Col_PermittedNetTotalLeverage, Col_CurrentMultiple, Tier_1_1L, Tier_1_ApplicableValue,
                              Tier_2_1L, Tier_2_ApplicableValue, Tier_3_ApplicableValue, Tier_1_2L, Tier_2_2L,
                              Tier_1_RR, Tier_2_RR):
    if Col_EligibilityCheck == 'No':
        return 0
    elif Col_LoanType == 'First Lien':
        if Col_PermittedNetSeniorLeverage < Tier_1_1L:
            return Tier_1_ApplicableValue
        elif Col_PermittedNetSeniorLeverage < Tier_2_1L:
            return Tier_2_ApplicableValue
        else:
            return Tier_3_ApplicableValue
    elif Col_LoanType == 'Second Lien' or Col_LoanType == 'Last Out':
        if Col_PermittedNetTotalLeverage < Tier_1_2L:
            return Tier_1_ApplicableValue
        elif Col_PermittedNetTotalLeverage < Tier_2_2L:
            return Tier_2_ApplicableValue
        else:
            return Tier_3_ApplicableValue
    elif Col_LoanType == 'Recurring Revenue':
        if Col_CurrentMultiple < Tier_1_RR:
            return Tier_1_ApplicableValue
        elif Col_CurrentMultiple < Tier_2_RR:
            return Tier_2_ApplicableValue
        else:
            return Tier_3_ApplicableValue


def funcVAE(VAE_dataframe, Measurement_Date):
    VAE_dataframe = VAE_dataframe[VAE_dataframe['Date of VAE Decision'] <= Measurement_Date]
    count = len(VAE_dataframe)
    if count >= 1:
        VAE_dataframe = VAE_dataframe[
            VAE_dataframe['Date of VAE Decision'] == max(VAE_dataframe['Date of VAE Decision'])]
        return 'Yes', VAE_dataframe['Event Type'].iloc[0], VAE_dataframe['Date of VAE Decision'].iloc[0], \
               VAE_dataframe['Assigned Value'].iloc[0]
    else:
        return '-', '-', '-', '-'


# Assigned Values (T)

def assignedValues(Col_VAE, Col_ActualPurchasePrice, Col_AgentAssignedValue, Col_ApplicableCollateralValue):
    if Col_VAE == 'Yes':
        if Col_ActualPurchasePrice < 0.95:
            x = Col_ActualPurchasePrice
        else:
            x = 1
        if Col_AgentAssignedValue == '-':
            return min(x, Col_ApplicableCollateralValue)
        else:
            return min(Col_AgentAssignedValue, x, Col_ApplicableCollateralValue)
    elif Col_ActualPurchasePrice < 0.95:
        y = Col_ActualPurchasePrice
    else:
        y = 1
    return min(y, Col_ApplicableCollateralValue)


# First Lien Value (X)
def firstLienValue(Col_AssignedValue, Col_FirstLienAmount):
    try:
        return Col_AssignedValue * Col_FirstLienAmount
    except:
        return '-'


# Second Lien Value (Y)
def secondLienValue(Col_AmountsExcessTier3Reclassified2ndLien, Col_AssignedValue):
    try:
        return Col_AmountsExcessTier3Reclassified2ndLien * Col_AssignedValue
    except:
        return '-'


# Amounts in excess of Tier 3 Reclassified as zero value

def amountExcessTier3ReclassifiedZeroValue(Col_LoanType, Col_BorrowerOtstandingPrincipalBalance,
                                           Col_PermittedNetTotalLeverage, Tier_3_2L):
    try:
        if Col_LoanType == 'First Lien' or Col_LoanType == 'Recurring Revenue':
            return 0
        elif Col_BorrowerOtstandingPrincipalBalance == 0:
            return 0
        elif Col_PermittedNetTotalLeverage > Tier_3_2L:
            return ((
                            Col_PermittedNetTotalLeverage - Tier_3_2L) / Col_PermittedNetTotalLeverage) * Col_BorrowerOtstandingPrincipalBalance
        else:
            return 0
    except:
        return '-'


# Last Out or 2nd Lien Amount (AA)
def lastOutorSecondLienAmount(Col_LoanType, Col_BorrowerOtstandingPrincipalBalance,
                              Col_AmountsExcessTier3ReclassifiedZeroValueZ):
    try:
        if Col_LoanType == 'First Lien' or Col_LoanType == 'Recurring Revenue':
            return 0
        else:
            return Col_BorrowerOtstandingPrincipalBalance - Col_AmountsExcessTier3ReclassifiedZeroValueZ
    except:
        return '-'


# FLLO Value (AB)
def FLLOValue(Col_LoanType, Col_LastOrSecondLienAmount, Col_AssignedValue):
    try:
        if Col_LoanType == 'Last Out':
            return Col_LastOrSecondLienAmount * Col_AssignedValue
        else:
            return 0
    except:
        return '-'


# Second Lien value (AC)
def secondLienValueAC(Col_LoanType, Col_LastOrSecondLienAmount, Col_AssignedValue):
    try:
        if Col_LoanType == 'Second Lien':
            return Col_LastOrSecondLienAmount * Col_AssignedValue
        else:
            return 0
    except:
        return '-'


# Amounts in excess of 2.5x RR Multiple Reclassified as zero value (AD)
def amountsExcess25RRMultipleReclassifiedZero(Col_LoanType, Col_CurrentMultiple, Col_BorrowerOtstandingPrincipalBalance,
                                              Tier_3_RR):
    if Col_LoanType == 'Recurring Revenue':
        if Col_CurrentMultiple > Tier_3_RR:
            return ((Col_CurrentMultiple - Tier_3_RR) / Col_CurrentMultiple) * Col_BorrowerOtstandingPrincipalBalance
        else:
            return 0
    else:
        return 0


# Recurring Revenue Amount (AE)

def recurringRevenueAmount(Col_LoanType, Col_BorrowerOtstandingPrincipalBalance,
                           Col_AmountsExcess25xRRMultiplReclassifiedZero):
    if Col_LoanType == 'Recurring Revenue':
        return Col_BorrowerOtstandingPrincipalBalance - Col_AmountsExcess25xRRMultiplReclassifiedZero
    else:
        return 0


# Recurring Revenue Value (AF)

def recurringRevenueValue(Col_LoanType, Col_RecurringRevenueAmount, Col_AssignedValue):
    if Col_LoanType == 'Recurring Revenue':
        return Col_RecurringRevenueAmount * Col_AssignedValue
    else:
        return 0


# Adjusted Borrowing Value
def adjustedBorrowingValue(Col_FirstLienValue, Col_SecondLienValue, Col_FLLOValue, Col_SecondLienValueAC,
                           Col_RecurringRevenueValue):
    try:
        return Col_FirstLienValue + Col_SecondLienValue + Col_FLLOValue + Col_SecondLienValueAC + Col_RecurringRevenueValue
    except:
        return '-'


# Rank (EB)
def rankEB(Col_RemoveDupes, Col_rank, filtered_df):
    try:
        if Col_RemoveDupes > 0:
            return Col_rank + len(filtered_df) - 1
        else:
            return 0
    except:
        return 0


# Advance Rate Class (DV)
# IFERROR(IF(BZ11=0,0,IF(BZ11<10000000,"< $10MM",IF(BZ11<50000000,"< $50MM",IF(BH11="yes","> $50MM & B- or better","> $50MM & Unrated")))),"-")
def advanceRateClass(Col_PermittedTTMEBITDACurrent, Col_RatedBorBetter):
    try:
        if Col_PermittedTTMEBITDACurrent == 0:
            return 0
        elif Col_PermittedTTMEBITDACurrent < 10000000:
            return '< $10MM'
        elif Col_PermittedTTMEBITDACurrent < 50000000:
            return '< $50MM'
        elif Col_RatedBorBetter == 'Yes':
            return '> $50MM & B- or better'
        else:
            return '> $50MM & Unrated'
    except:
        return '-'


# Advance Rate Definition (C)
# =IF(A11="","-",IF(OR(B11="Last Out",B11="Second Lien",B11="Recurring Revenue"),B11,CONCATENATE(B11," ",DV11)))
def advanceRateDefinition(Col_Borrower, Col_LoanType, Col_AdvanceRateClass):
    if Col_Borrower == '':
        return '-'
    elif Col_LoanType == 'Last Out' or Col_LoanType == 'Second Lien' or Col_LoanType == 'Recurring Revenue':
        return Col_LoanType
    else:
        return Col_LoanType + ' ' + Col_AdvanceRateClass


def qualifies(Col_LoanType, Col_AdvanceRateDefinition, Col_Rank_EA):
    try:
        if (
                Col_LoanType == 'Last Out' or Col_LoanType == 'Second Lien' or Col_AdvanceRateDefinition == 'First Lien < $10MM') and Col_Rank_EA < 4:
            return 'Yes'
        else:
            return 'No'
    except:
        return 0


# Excess_EC (EC)
# IFERROR(IF(DX11="yes",(DY11-@INDEX(DY:DY-0.01,MATCH(4,$EA$10:$EA$85,0)))*(DW11/SUMIF($A:$A,A11,$DW:$DW)),0),0)
def excessEC(filtered_df, rank_value, obligor_DY, borrowing_value_DW, qualifies):
    try:
        if qualifies.lower() == 'yes':
            if rank_value == 4:
                sum_if_value = borrowing_value_DW / filtered_df['Adjusted Borrowing Value_DW'].sum()
                obligor_value = obligor_DY - filtered_df[filtered_df['Rank_EA'] == rank_value]['Obligor_DY'].iloc[0]
                return obligor_value * sum_if_value
            else:
                return 0
        else:
            return 0
    except:
        return 0


# Rank (EJ)
def rankEJ(Col_RemoveDupesEH, Col_rank, filtered_df):
    try:
        if Col_RemoveDupesEH > 0:
            return Col_rank + len(filtered_df) - 1
        else:
            return 0
    except:
        return 0


# Largest Excess (EK)
# =IF(EI11<4,IF(EG11>EE11,(EG11-EE11)*(ED11/SUMIF($A:$A,A11,$ED:$ED)),0),0)

def largestExcess(filtered_df, Col_RankEI, Col_ObligorEG, Col_Top3Max, Col_RevisedValaue):
    if Col_RankEI < 4:
        if Col_ObligorEG > Col_Top3Max:
            sumif_value = (Col_ObligorEG - Col_Top3Max) * Col_RevisedValaue / filtered_df['Revised Value ED'].sum()
            return sumif_value
        else:
            return 0
    else:
        return 0


# Other Excess (EL) =IF(EI28>3,IF(EG28>EF28,(EG28-EF28)*(ED28/(SUMIF($A:$A,$A28,$ED:$ED))),0),0)
def otherExcess(filtered_df, Col_RankEI, Col_ObligorEG, Col_OtherMax, Col_RevisedValaue):
    if Col_RankEI > 3:
        if Col_ObligorEG > Col_OtherMax:
            sumif_value = (Col_ObligorEG - Col_OtherMax) * Col_RevisedValaue / filtered_df['Revised Value ED'].sum()
            return sumif_value
        else:
            return 0
    else:
        return 0


# O/S Value for Industries DataFrame
def osValue(filterd_df):
    try:
        return filterd_df['Adjusted Borrowing Value'].sum()
    except:
        return 0


# Largest Industry (EP)
def largestIndustry(filtered_df):
    try:
        return filtered_df['Industry Rank'].iloc[0]
    except:
        return 0


def excessEQ(filtered_df, Col_LargestIndustry, Col_LoanLimit, Col_MaxEN, Col_RevisedValueEM):
    try:
        if Col_LargestIndustry == 1:
            sumif_value = (Col_LoanLimit - Col_MaxEN) * Col_RevisedValueEM / filtered_df['Revised Value EM'].sum()
            return max(0, sumif_value)
        else:
            return 0
    except:
        return 0


# Revised Value (ER) =IFERROR(MAX(0,EM11-EQ11),0)
def revisedValueER(Col_RevisedValueEM, Col_ExcessLargestIndustry):
    try:
        return max(0, Col_RevisedValueEM - Col_ExcessLargestIndustry)
    except:
        return 0


# Loan Limit (ET)
# =IFERROR(SUMIF($AZ:$AZ,$AZ11,ER:ER),0)
def loanLimit(filtered_df, Col_GICS, Col_RevisedValueER):
    try:
        sumif_value = filtered_df['Revised Value ER'].sum()
        return sumif_value
    except:
        return 0


# 2nd Largest Industry (EU)
# =IFERROR(VLOOKUP(AZ11,'Concentration Limits'!$E$62:$H$130,4,FALSE),0)
def secondLargestIndustry(filtered_df):
    try:
        return filtered_df['Industry Rank'].iloc[0]
    except:
        return 0


# 2nd Largest Industry Excess (EV)
# =IFERROR(MAX(0,IF(EU19=2,(ET19-ES19)*(ER19/SUMIF($AZ:$AZ,AZ19,ER:ER)),0)),0)
def excessEV(filtered_df, Col_2LargestIndustry, Col_LoanLimitET, Col_MaxES, Col_RevisedValueER):
    try:
        if Col_2LargestIndustry == 2:
            sumif_value = (Col_LoanLimitET - Col_MaxES) * (Col_RevisedValueER / filtered_df['Revised Value ER'].sum())
            return max(0, sumif_value)
        else:
            return 0
    except:
        return 0


# Revised Value (EW) --> for 3rd largest industry
# =IFERROR(MAX(0,ER11-EV11),0)
def thirdLargestIndustry(Col_RevisedValueER, Col_ExcessEV):
    try:
        value = Col_RevisedValueER - Col_ExcessEV
        return max(0, value)
    except:
        return 0


# Loan Limit (EY)
# =IFERROR(SUMIF($AZ:$AZ,$AZ11,EW:EW),0)
def loanLimitEY(filtered_df, Col_GICS, Col_RevisedValueEW):
    try:
        sumif_value = filtered_df['Revised Value EW'].sum()
        return sumif_value
    except:
        return 0


# 3rd Largest Industry Excess (FA)
# =IFERROR(MAX(0,IF(EZ11=3,(EY11-EX11)*(EW11/SUMIF($AZ:$AZ,AZ11,EW:EW)),0)),0)
# Using rank derived for largest industry here (EP instead of EZ)
def excessFA(filtered_df, Col_LargestIndustry, Col_LoanLimitEY, Col_MaxEX, Col_RevisedValueEW):
    try:
        if Col_LargestIndustry == 3:
            sumif_value = (Col_LoanLimitEY - Col_MaxEX) * (Col_RevisedValueEW / filtered_df['Revised Value EW'].sum())
            return max(0, sumif_value)
        else:
            return 0
    except:
        return 0


# Excess FF (All other Industry Classification)
# Revised Value FB ---> All other industry classification
# =IFERROR(MAX(0,EW11-FA11),0)

def otherIndustry(Col_RevisedValueEW, Col_ExcessFA):
    try:
        value = Col_RevisedValueEW - Col_ExcessFA
        return max(0, value)
    except:
        return 0


# Loan Limit FD
# =IFERROR(SUMIF($AZ:$AZ,$AZ11,FB:FB),0)
def loanLimitFD(filtered_df, Col_GICS, Col_RevisedValueFB):
    try:
        sumif_value = filtered_df['Revised Value FB'].sum()
        return sumif_value
    except:
        return 0


# Excess FF --> All other industry classification
# =IFERROR(IF(FB11=0,0,MAX(0,IF(FE11<4,0,(FD11-FC11)*($FB11/SUMIF($AZ:$AZ,AZ11,FB:FB))))),0)
# Rank from EP used instead of FE
def excessFF(filtered_df, Col_LargestIndustry, Col_LoanLimitFD, Col_MaxFC, Col_RevisedValueFB):
    try:
        if Col_LargestIndustry == 0:
            sumif_value = (Col_LoanLimitFD - Col_MaxFC) * (Col_RevisedValueFB / filtered_df['Revised Value FB'].sum())
            return max(0, sumif_value)
        else:
            return 0
    except:
        return 0


# Revised Value FG ---> EBITDA < $10MM
# =IFERROR(MAX(0,FB11-FF11),0)
def revisedValueFG(Col_RevisedValueFB, Col_ExcessFF):
    try:
        value = Col_RevisedValueFB - Col_ExcessFF
        return max(0, value)
    except:
        return 0


# Qualifies if EBITDA < $10MM (FI)
# =IFERROR(IF(BZ11<10000000, "Yes", "No"),0)
def qualifiesEbitdaLess10MM(Col_PermittedTTMEBITDACurrent):
    try:
        if Col_PermittedTTMEBITDACurrent < 10000000:
            return 'Yes'
        else:
            return 'No'
    except:
        return 0


# Loan Limit (FJ)
# =IFERROR(IF(FI11="Yes",SUMIF(FI:FI,"Yes",FG:FG),0),0)
def loanLimitFJ(filtered_df, Col_Qualifies, Col_RevisedValueFG):
    try:
        if Col_Qualifies == 'Yes':
            sumif_value = filtered_df['Revised Value FG'].sum()
            return sumif_value
        else:
            return 0
    except:
        return 0


# Excess FK ---> EBITDA < $10MM
# =IFERROR(IF(FJ11>FH11,(FJ11-FH11)*(FG11/SUMIF(FI:FI,"Yes",FG:FG)),0),0)
def excessFK(filtered_df, Col_LoanLimitFJ, Col_MaxFH, Col_RevisedValueFG):
    try:
        if Col_LoanLimitFJ > Col_MaxFH:
            sumif_value = (Col_LoanLimitFJ - Col_MaxFH) * (Col_RevisedValueFG / filtered_df['Revised Value FG'].sum())
            return sumif_value
        else:
            return 0
    except:
        return 0


# Revised Value FL --->DIP Loans
# =IFERROR(MAX(0,FG11-FK11),0)
def revisedValueFL(Col_RevisedValueFG, Col_ExcessFK):
    try:
        value = Col_RevisedValueFG - Col_ExcessFK
        return max(0, value)
    except:
        return 0


# Qualifies FN ---> DIP Loans
# =IFERROR(IF(AO11="Yes", "Yes", "No"),0)
def qualifiesDIPLoan(Col_DIPLoan):
    try:
        if Col_DIPLoan == 'Yes':
            return 'Yes'
        else:
            return 'No'
    except:
        return 0


# Loan Limit FO ---> DIP Loans
# =IFERROR(IF(FN11="Yes",SUMIF(FN:FN,"Yes",FL:FL),0),0)
def loanLimitFO(filtered_df, Col_QualifiesDIP, Col_RevisedValueFL):
    try:
        if Col_QualifiesDIP == 'Yes':
            sumif_value = filtered_df['Revised Value FL'].sum()
            return sumif_value
        else:
            return 0
    except:
        return 0


# Excess FP ---> DIP Loans
# =IFERROR(IF(FO11>FM11,(FO11-FM11)*(FL11/SUMIF(FN:FN,"Yes",FL:FL)),0),0)
def excessFP(filtered_df, Col_LoanLimitFO, Col_MaxFM, Col_RevisedValueFL):
    try:
        if Col_LoanLimitFO > Col_MaxFM:
            sumif_value = (Col_LoanLimitFO - Col_MaxFM) * (Col_RevisedValueFL / filtered_df['Revised Value FL'].sum())
            return sumif_value
        else:
            return 0
    except:
        return 0


# Revised Value FQ ---> Cov Lite Loans
# =IFERROR(MAX(0,FL11-FP11),0)
def revisedValueFQ(Col_RevisedValueFL, Col_ExcessFP):
    try:
        value = Col_RevisedValueFL - Col_ExcessFP
        return max(0, value)
    except:
        return 0


# Qualifies Cov Lite FS
# =IFERROR(IF(AN11="Yes", "Yes", "No"),0)
def qualifiesCovLiteLoan(Col_CovLite):
    try:
        if Col_CovLite == 'Yes':
            return 'Yes'
        else:
            return 'No'
    except:
        return 0


# Loan Limit FT
# =IFERROR(IF(FS11="Yes",SUMIF(FS:FS,"Yes",FQ:FQ),0),0)
def loanLimitFT(filtered_df, Col_QualifiesCovLite, Col_RevisedValueFL):
    try:
        if Col_QualifiesCovLite == 'Yes':
            sumif_value = filtered_df['Revised Value FQ'].sum()
            return sumif_value
        else:
            return 0
    except:
        return 0


# Excess FU --> Cov Lite Loans excess
# =IFERROR(IF(FT11>FR11,(FT11-FR11)*(FQ11/SUMIF(FS:FS,"Yes",FQ:FQ)),0),0)
def excessFU(filtered_df, Col_LoanLimitFT, Col_MaxFR, Col_RevisedValueFQ):
    try:
        if Col_LoanLimitFT > Col_MaxFR:
            sumif_value = (Col_LoanLimitFT - Col_MaxFR) * (Col_RevisedValueFQ / filtered_df['Revised Value FQ'].sum())
            return sumif_value
        else:
            return 0
    except:
        return 0


# Revised Value FV --> Less than Quarterly Pay
# =IFERROR(MAX(0,FQ11-FU11),0)
def revisedValueFV(Col_RevisedValueFQ, Col_ExcessFU):
    try:
        value = Col_RevisedValueFQ - Col_ExcessFU
        return max(0, value)
    except:
        return 0


# Qualifies Less than Qtrly FX -->
# =IFERROR(IF(BE11="Yes","Yes", "No"),0)
def qualifiesLessThanQtrly(Col_LessThanQtrly):
    try:
        if Col_LessThanQtrly == 'Yes':
            return 'Yes'
        else:
            return 'No'
    except:
        return 0


# Loan Limit FY
# =IFERROR(IF(FX11="Yes",SUMIF(FX:FX,"Yes",FV:FV),0),0)
def loanLimitFY(filtered_df, Col_QualifiesLessThanQtrly, Col_RevisedValueFV):
    try:
        if Col_QualifiesLessThanQtrly == 'Yes':
            sumif_value = filtered_df['Revised Value FV'].sum()
            return sumif_value
        else:
            return 0
    except:
        return 0


# Excess FZ --> Quarterly
# =IFERROR(IF(FY11>FW11,(FY11-FW11)*(FV11/SUMIF(FX:FX,"Yes",FV:FV)),0),0)
def excessFZ(filtered_df, Col_LoanLimitFY, Col_MaxFW, Col_RevisedValueFV):
    try:
        if Col_LoanLimitFY > Col_MaxFW:
            sumif_value = (Col_LoanLimitFY - Col_MaxFW) * (Col_RevisedValueFV / filtered_df['Revised Value FW'].sum())
            return sumif_value
        else:
            return 0
    except:
        return 0


# Foreign Currency
# Revised Value GA -->
# =IFERROR(MAX(0,FV11-FZ11),0)
def revisedValueGA(Col_RevisedValueFV, Col_ExcessFZ):
    try:
        value = Col_RevisedValueFV - Col_ExcessFZ
        return max(0, value)
    except:
        return 0


# Qualifies GC --> Foreign Currency
# =IFERROR(IF(AR11="Yes","Yes", "No"),0)
def qualifiesForeignGC(Col_NonUSApprovedCurrency):
    try:
        if Col_NonUSApprovedCurrency == 'Yes':
            return 'Yes'
        else:
            return 'No'
    except:
        return 0


# Loan Limit GD
# =IFERROR(IF(GC11="Yes",SUMIF(GC:GC,"Yes",GA:GA),0),0)
def loanLimitGD(filtered_df, Col_QualifiesForeign, Col_RevisedValueGA):
    try:
        if Col_QualifiesForeign == 'Yes':
            sumif_value = filtered_df['Revised Value GA'].sum()
            return sumif_value
        else:
            return 0
    except:
        return 0


# Excess GE
# =IFERROR(IF(GD11>GB11,(GD11-GB11)*(GA11/SUMIF(GC:GC,"Yes",GA:GA)),0),0)
def excessGE(filtered_df, Col_LoanLimitGD, Col_MaxGB, Col_RevisedValueGA):
    try:
        if Col_LoanLimitGD > Col_MaxGB:
            sumif_value = (Col_LoanLimitGD - Col_MaxGB) * (Col_RevisedValueGA / filtered_df['Revised Value GA'].sum())
            return sumif_value
        else:
            return 0
    except:
        return 0


# Approved Country
# Revised Value GF
# =IFERROR(MAX(0,GA11-GE11),0)
def revisedValueGF(Col_RevisedValueGA, Col_ExcessGE):
    try:
        value = Col_RevisedValueGA - Col_ExcessGE
        return max(0, value)
    except:
        return 0


# GH Qualifies Approved Country
# =IFERROR(IF(AS11="Yes","Yes", "No"),0)
def qualifiesCountryGH(Col_NonUSApprovedCountry):
    try:
        if Col_NonUSApprovedCountry == 'Yes':
            return 'Yes'
        else:
            return 'No'
    except:
        return 0


# Loan Limit GI
# =IFERROR(IF(GH11="Yes",SUMIF(GH:GH,"Yes",GF:GF),0),0)
def loanLimitGI(filtered_df, Col_QualifiesCountry, Col_RevisedValueGF):
    try:
        if Col_QualifiesCountry == 'Yes':
            sumif_value = filtered_df['Revised Value GF'].sum()
            return sumif_value
        else:
            return 0
    except:
        return 0


# Excess GJ
# =IFERROR(IF(GI11>GG11,(GI11-GG11)*(GF11/SUMIF(GH:GH,"Yes",GF:GF)),0),0)
def excessGJ(filtered_df, Col_LoanLimitGI, Col_MaxGG, Col_RevisedValueGF):
    try:
        if Col_LoanLimitGI > Col_MaxGG:
            sumif_value = (Col_LoanLimitGI - Col_MaxGG) * (Col_RevisedValueGF / filtered_df['Revised Value GF'].sum())
            return sumif_value
        else:
            return 0
    except:
        return 0


# DDTL and Revolving Loans
# Revised Value GK
# =IFERROR(MAX(0,GF11-GJ11),0)
def revisedValueGK(Col_RevisedValueGF, Col_ExcessGJ):
    try:
        value = Col_RevisedValueGF - Col_ExcessGJ
        return max(0, value)
    except:
        return 0


# Qualifies DDTL and Revolving Loans GM
# =IFERROR(IF(AQ11="Yes","Yes", "No"),0)
def qualifiesDDTLandRevolvingGM(Col_RevolvingOrDelayedFunding):
    try:
        if Col_RevolvingOrDelayedFunding == 'Yes':
            return 'Yes'
        else:
            return 'No'
    except:
        return 0


# Loan Limit GN
# =IFERROR(IF(GM11="Yes",SUMIF(GM:GM,"Yes",GK:GK),0),0)
def loanLimitGN(filtered_df, Col_QualifiesDDTLandRevolving, Col_RevisedValueGK):
    try:
        if Col_QualifiesDDTLandRevolving == 'Yes':
            sumif_value = filtered_df['Revised Value GK'].sum()
            return sumif_value
        else:
            return 0
    except:
        return 0


# Excess GO --> DDTL or Revolving Loans Excess
# =IFERROR(IF(GN11>GL11,(GN11-GL11)*(GK11/SUMIF(GM:GM,"Yes",GK:GK)),0),0)
def excessGO(filtered_df, Col_LoanLimitGN, Col_MaxGL, Col_RevisedValueGK):
    try:
        if Col_LoanLimitGN > Col_MaxGL:
            sumif_value = (Col_LoanLimitGN - Col_MaxGL) * (Col_RevisedValueGK / filtered_df['Revised Value GK'].sum())
            return sumif_value
        else:
            return 0
    except:
        return 0


# Tier 3 Obligors
# Revised Value GP
# =IFERROR(MAX(0,GK11-GO11),0)
def revisedValueGP(Col_RevisedValueGK, Col_ExcessGO):
    try:
        value = Col_RevisedValueGK - Col_ExcessGO
        return max(0, value)
    except:
        return 0


# Permitted Net Senior Leverage CE
# =IFERROR(IF(CA11="",0,(CB11-CA11)/BS11),"-")
def permittedNetSeniorLeverageCE(Col_InitialUnrestricetdCash, Col_InitialSeniorDebt, Col_PermittedTTMEBITDA):
    try:
        if Col_InitialUnrestricetdCash == '':
            return 0
        else:
            return (Col_InitialSeniorDebt - Col_InitialUnrestricetdCash) / Col_PermittedTTMEBITDA
    except:
        return '-'


# Permitted Net Total Leverage (CG)
# =IFERROR((CC11-CA11)/BS11,"-")
def permittedNetTotalLeverageCG(Col_InitialTotalDebt, Col_InitialUnrestricetdCash, Col_PermittedTTMEBITDA):
    try:
        return (Col_InitialTotalDebt - Col_InitialUnrestricetdCash) / Col_PermittedTTMEBITDA
    except:
        return '-'


# Initial Multiple CM
# =IF(B11="Recurring Revenue",CC11/CK11,0)
def initialMultiple(Col_LoanType, Col_InitialTotalDebt, Col_InitialRecurringRevenue):
    if Col_LoanType == 'Recurring Revenue':
        return Col_InitialTotalDebt / Col_InitialRecurringRevenue
    else:
        return 0


# Calculating Tier(AY) to be used to decide if Tier 3 obligor qualifies
def tiers(Col_LoanType, Col_PermittedNetSeniorLeverageCE, Col_PermittedNetTotalLeverageCG, Col_InitialMultiple,
          Tier_1_1L, Tier_2_1L, Tier_1_2L, Tier_2_2L, Tier_1_RR, Tier_2_RR):
    if Col_LoanType == "First Lien":
        if Col_PermittedNetSeniorLeverageCE < Tier_1_1L:
            return 'Tier 1'  # Tier_1_ApplicableValue
        elif Col_PermittedNetSeniorLeverageCE < Tier_2_1L:
            return 'Tier 2'  # Tier_2_ApplicableValue
        else:
            return 'Tier 3'  # Tier_3_ApplicableValue
    elif Col_LoanType == "Second Lien" or Col_LoanType == "Last Out":
        if Col_PermittedNetSeniorLeverageCE < Tier_1_2L:
            return 'Tier 1'  # Tier_1_ApplicableValue
        elif permittedNetTotalLeverageCG < Tier_2_2L:
            return 'Tier 2'  # Tier_2_ApplicableValue
        else:
            return 'Tier 3'  # Tier_3_ApplicableValue
    elif Col_LoanType == "Recurring Revenue":
        if Col_InitialMultiple < Tier_1_RR:
            return 'Tier 1'  # Tier_1_ApplicableValue
        elif Col_InitialMultiple < Tier_2_RR:
            return 'Tier 2'  # Tier_2_ApplicableValue
        else:
            return 'Tier 3'


# QualifiesTier3Obligor (GR)
# =IFERROR(IF(AND(AL11="Yes",AY11="Tier 3"),"Yes", "No"),0)
def qualifiesTier3Obligor(Col_EligibilityCheck, Col_Tier):
    try:
        if Col_EligibilityCheck == 'Yes' and Col_Tier == 'Tier 3':
            return 'Yes'
        else:
            return 'No'
    except:
        return 0


# Loan Limit GS (Tier 3 Obligor)
# =IFERROR(IF(GR11="Yes",SUMIF(GR:GR,"Yes",GP:GP),0),0)
def loanLimitGS(filtered_df, Col_QualifiesTier3, Col_RevisedValueGP):
    try:
        if Col_QualifiesTier3 == 'Yes':
            return filtered_df['Revised Value GP'].sum()
        else:
            return 0
    except:
        return 0


# Excess Tier 3 Obligor (GT)
# =IFERROR(IF(GS11>GQ11,(GS11-GQ11)*(GP11/SUMIF(GR:GR,"Yes",GP:GP)),0),0)
def excessGT(filtered_df, Col_LoanLimitGS, Col_MaxGQ, Col_RevisedValueGP):
    try:
        if Col_LoanLimitGS > Col_MaxGQ:
            sumif_value = (Col_LoanLimitGS - Col_MaxGQ) * (Col_RevisedValueGP / filtered_df['Revised Value GP'].sum())
            return max(0, sumif_value)
        else:
            return 0
    except:
        return 0


# Second Lien
# Revised Value (GU)
# =IFERROR(MAX(0,GP11-GT11),0)
def revisedValueGU(Col_RevisedValueGP, Col_ExcessGT):
    try:
        value = Col_RevisedValueGP - Col_ExcessGT
        return max(0, value)
    except:
        return 0


# Loan Limit Second Lien (GW)
# =IFERROR(IF(B11="Second Lien",SUMIF(B:B,B11,GU:GU),0),0)
def loanLimitGW(filtered_df, Col_LoanType, Col_RevisedValueGU):
    try:
        if Col_LoanType == 'Second Lien':
            return filtered_df['Revised Value GU'].sum()
        else:
            return 0
    except:
        return 0


# Excess Second Lien (GX)
# =IFERROR(MAX(0,(GW11-GV11)*(GU11/SUMIF($B:$B,B11,GU:GU ))),0)
def excessGX(filtered_df, Col_LoanLimitGW, Col_MaxGV, Col_RevisedValueGU):
    try:
        sumif_value = (Col_LoanLimitGW - Col_MaxGV) * (Col_RevisedValueGU / filtered_df['Revised Value GU'].sum())
        return max(0, sumif_value)
    except:
        return 0


# First Lien Last Out
# Revised Value GY
# =IFERROR(MAX(0,GU11-GX11),0)
def revisedValueGY(Col_RevisedValueGU, Col_ExcessGX):
    try:
        value = Col_RevisedValueGU - Col_ExcessGX
        return max(0, value)
    except:
        return 0


# Loan Limit (HA)
# =IFERROR(IF(B11="Last Out",SUMIF(B:B,B11,GY:GY),0),0)
def loanLimitHA(filtered_df, Col_LoanType, Col_RevisedValueGY):
    try:
        if Col_LoanType == 'Last Out':
            return filtered_df['Revised Value GY'].sum()
        else:
            return 0
    except:
        return 0


# Excess HB (First Lien Last Out)
# =IFERROR(MAX(0,(HA11-GZ11)*(GY11/SUMIF($B:$B,B11,GY:GY))),0)
def excessHB(filtered_df, Col_LoanLimitHA, Col_MaxGZ, Col_RevisedValueGY):
    try:
        sumif_value = (Col_LoanLimitHA - Col_MaxGZ) * (Col_RevisedValueGY / filtered_df['Revised Value GY'].sum())
        return max(0, sumif_value)
    except:
        return 0


# Loan Maturities Greater than 6 Years
# Revised Value (HC)
# =IFERROR(MAX(0,GY11-HB11),0)
def revisedValueHC(Col_RevisedValueGY, Col_ExcessHB):
    try:
        value = Col_RevisedValueGY - Col_ExcessHB
        return max(0, value)
    except:
        return 0


# Qualifies HE (Loan Maturities Greater than 6 Years)
# =IFERROR(IF(AK11>6, "Yes", "No"),0)----> Original Term(AK) --> =ROUND(YEARFRAC(AI11,AJ11,1),2)
# AK --> =ROUND(YEARFRAC(AI11,AJ11,1),2)
def originalTerm(Col_AcquisitionDate, Col_MaturityDate):
    d1 = Col_AcquisitionDate
    d2 = Col_MaturityDate
    x = yf.yearfrac(d1, d2, 'act_isda')
    return round(x, 2)


# Qualifies HE (Loan Maturities Greater than 6 Years)
# =IFERROR(IF(AK11>6, "Yes", "No"),0)
def qualifiesHE(Col_OriginalTerm):
    try:
        if Col_OriginalTerm > 6:
            return 'Yes'
        else:
            return 'No'
    except:
        return 0


# Loan Limit HF (Loan Maturities Greater than 6 Years)
# =IFERROR(IF(HE11="Yes",SUMIF(HE:HE,"Yes",HC:HC),0),0)
def loanLimitHF(filtered_df, Col_qualifiesHE, Col_RevisedValueHC):
    try:
        if Col_qualifiesHE == 'Yes':
            return filtered_df['Revised Value HC'].sum()
        else:
            return 0
    except:
        return 0


# Excess HG (Loan Maturities Greater than 6 Years)
# Loan Maturities Greater than 6 Years
# =IFERROR(IF(HF11>HD11,(HF11-HD11)*(HC11/SUMIF(HE:HE,"Yes",HC:HC)),0),0)
def excessHG(filtered_df, Col_LoanLimitHF, Col_MaxHD, Col_RevisedValueHC):
    try:
        if Col_LoanLimitHF > Col_MaxHD:
            sumif_value = (Col_LoanLimitHF - Col_MaxHD) * (Col_RevisedValueHC / filtered_df['Revised Value HC'].sum())
            return sumif_value
        else:
            return 0
    except:
        return 0


# Gambling Industries
# Revised Value (HH)
# =IFERROR(MAX(0,HC11-HG11),0)
def revisedValueHH(Col_RevisedValueHC, Col_ExcessHG):
    try:
        value = Col_RevisedValueHC - Col_ExcessHG
        return max(0, value)
    except:
        return 0


# Qualifies Gambling Industry (HJ)
# =IFERROR(IF(AT11="Yes", "Yes", "No"),0)
def qualifiesHJ(Col_GamblingIndustry):
    try:
        if Col_GamblingIndustry == 'Yes':
            return 'Yes'
        else:
            return 'No'
    except:
        return 0


# Loan Limit HK (Gambling Industry)
# =IFERROR(IF(HJ11="Yes",SUMIF(HJ:HJ,"Yes",HH:HH),0),0)
def loanLimitHK(filtered_df, Col_qualifiesHJ, Col_RevisedValueHH):
    try:
        if Col_qualifiesHJ == 'Yes':
            return filtered_df['Revised Value HH'].sum()
        else:
            return 0
    except:
        return 0


# Excess HL (Gambling Industry Excess)
# =IFERROR(IF(HK11>HI11,(HK11-HI11)*(HH11/SUMIF(HJ:HJ,"Yes",HH:HH)),0),0)
def excessHL(filtered_df, Col_LoanLimitHK, Col_MaxHI, Col_RevisedValueHH):
    try:
        if Col_LoanLimitHK > Col_MaxHI:
            sumif_value = (Col_LoanLimitHK - Col_MaxHI) * (Col_RevisedValueHH / filtered_df['Revised Value HH'].sum())
            return sumif_value
        else:
            return 0
    except:
        return 0


# Recurring Revenue Loans
# Revised Value (HM)
# =IFERROR(MAX(0,HH11-HL11),0)
def revisedValueHM(Col_RevisedValueHH, Col_ExcessHL):
    try:
        value = Col_RevisedValueHH - Col_ExcessHL
        return max(0, value)
    except:
        return 0


# Qualifies Recurring Revenue Loan (HO)
# =IFERROR(IF(B11="Recurring Revenue","Yes", "No"),0)
def qualifiesHO(Col_LoanType):
    try:
        if Col_LoanType == 'Recurring Revenue':
            return 'Yes'
        else:
            return 'No'
    except:
        return 0


# Loan Limit HP
# =IFERROR(IF(HO11="Yes",SUMIF(HO:HO,"Yes",HM:HM),0),0)
def loanLimitHP(filtered_df, Col_qualifiesHO, Col_RevisedValueHM):
    try:
        if Col_qualifiesHO == 'Yes':
            return filtered_df['Revised Value HH'].sum()
        else:
            return 0
    except:
        return 0


# Excess HQ Recurring Revenue Loans
# =IFERROR(IF(HP12>HN12,(HP12-HN12)*(HM12/SUMIF(HO:HO,"Yes",HM:HM)),0),0)
def excessHQ(filtered_df, Col_LoanLimitHP, Col_MaxHN, Col_RevisedValueHM):
    try:
        if Col_LoanLimitHP > Col_MaxHN:
            sumif_value = (Col_LoanLimitHP - Col_MaxHN) * (Col_RevisedValueHM / filtered_df['Revised Value HM'].sum())
            return sumif_value
        else:
            return 0
    except:
        return 0


# To calculate Unfunded Exposure AMount in Availability
def borrowerUnfundedAmount(Col_BorrowerOtstandingPrincipalBalance, Col_BorrowerFacilityCommitment):
    try:
        return Col_BorrowerFacilityCommitment - Col_BorrowerOtstandingPrincipalBalance
    except:
        return 0


# Advance Rate (D) (to calculate weighted average advance rate for unfunded exposures)
# =IFERROR(VLOOKUP(C11,'Concentration Limits'!$D$5:$G$22,4,FALSE),"-")
def advanceRate(filtered_df):
    try:
        return filtered_df['Advance Rate'].iloc[0]
    except:
        return 0


# Revised Value HR
# =IFERROR(MAX(0,HM11-HQ11),0)
def revisedValueHR(Col_RevisedValueHM, Col_ExcessHQ):
    try:
        value = Col_RevisedValueHM - Col_ExcessHQ
        return max(0, value)
    except:
        return 0


# First Lien HS
# =IFERROR(IF(X11=0,0,HR11*X11/(X11+Y11)),0)
def firstLien(Col_1stLien, Col_RevisedValueHR, Col_2ndLien):
    try:
        if Col_1stLien == 0:
            return 0
        else:
            return Col_RevisedValueHR * Col_1stLien / (Col_1stLien + Col_2ndLien)
    except:
        return 0


# Reclassed Second HT
# =IFERROR(IF(Y11=0,0,HR11*Y11/(X11+Y11)),0)
def reclassedSecond(Col_SecondLienValue, Col_RevisedValaueHR, Col_FirstLienValue):
    try:
        if Col_SecondLienValue == 0:
            return 0
        else:
            return Col_RevisedValaueHR * Col_SecondLienValue / (Col_FirstLienValue + Col_SecondLienValue)
    except:
        return 0


# Last Out HU
# =IFERROR(IF(OR(B11="First Lien",B11="Recurring Revenue"),"n/a",IFERROR(HR11*AB11/(AB11+AC11),0)),0)
def lastOut(Col_LoanType, Col_RevisedValueHR, Col_FLLOValue, Col_SecondLienValueAC):
    try:
        if Col_LoanType == 'First Lien' or Col_LoanType == 'Recurring Revenue':
            return 'n/a'
        else:
            try:
                return (Col_RevisedValueHR * Col_FLLOValue) / (Col_FLLOValue + Col_SecondLienValueAC)
            except:
                return 0
    except:
        return 0


# Reclassed Second HV
# =IFERROR(IF(OR(B11="First Lien",B11="Recurring Revenue"),"n/a",IFERROR(HR11*AC11/(AB11+AC11),0)),0)
def reclassedSecondHV(Col_LoanType, Col_RevisedValueHR, Col_SecondLienValueAC, Col_FLLOValue):
    try:
        if Col_LoanType == 'First Lien' or Col_LoanType == 'Recurring Revenue':
            return 'n/a'
        else:
            try:
                return Col_RevisedValueHR * Col_SecondLienValueAC / (Col_FLLOValue + Col_SecondLienValueAC)
            except:
                return 0
    except:
        return 0


# Recurring Revenue HW
# =IFERROR(IF(B11="Recurring Revenue",IFERROR(HR11*AF11/AF11,0),"n/a"),0)
def recurringRevenueHW(Col_LoanType, Col_RevisedValueHR, Col_RecurringRevenueValue):
    try:
        if Col_LoanType == 'Recurring Revenue':
            try:
                return Col_RevisedValueHR * Col_RecurringRevenueValue / Col_RecurringRevenueValue
            except:
                return 0
        else:
            return 'n/a'
    except:
        return 0


# Base Borrowing Percentage in Borrower Outstandinga dataframe
# =K5/K$23

def baseBorrowingPercentage(Col_BaseBorrowingValue, Total_Borrowing_Base):
    try:
        return Col_BaseBorrowingValue / Total_Borrowing_Base
    except:
        return np.nan


# VAE Trigger calculations
# =IFERROR(INDEX(VAE,MATCH(A11&MAX(IF(VAE!$C$5:$C$100=A11,IF(VAE!$F$5:$F$100<=Availability!$F$12,IF(VAE!$D$5:$D$100="(A) Credit Quality Deterioration Event",VAE!$F$5:$F$100)))),VAE!$C$5:$C$100&VAE!$F$5:$F$100,0),MATCH("Interest Coverage",VAE!$H$4:$S$4,0)),DB11)
def interest_coverage_fun(Col_InitialInterestCoverage, Borrower, Measurement_Date, VAE_dataframe):
    try:
        VAE_df = VAE_dataframe[VAE_dataframe['Borrower'] == Borrower]
        # print(VAE_df.columns)
        VAE_df = VAE_df[VAE_df['Date of VAE Decision'] <= Measurement_Date]

        VAE_df = VAE_df[VAE_df['Event Type'] == "(A) Credit Quality Deterioration Event"]
        date = VAE_df['Date of VAE Decision'].max()
        return VAE_df[VAE_df['Date of VAE Decision'] == date]['Interest Coverage'].iloc[0]
    except Exception as e:
        # print(e)
        return Col_InitialInterestCoverage


# =IFERROR((J5-L5)/H5,"-") Net Senior Leverage column from VAE
def Net_Senior_Leverage_fun(Senior_Debt, Unrestricted_Cash, TTM_EBITDA):
    try:
        return (Senior_Debt - Unrestricted_Cash) / TTM_EBITDA
    except:
        return "-"


# CH - VAE Net Senior Leverage
def VAE_Net_Senior_Leverage_fun(VAE_df, Permitted_Net_Senior_Leverage_CE, Measurement_Date, VAE_dataframe):
    try:
        VAE_df = VAE_dataframe[VAE_dataframe['Date of VAE Decision'] <= Measurement_Date]
        VAE_df = VAE_df[VAE_df['Event Type'] == "(A) Credit Quality Deterioration Event"]
        date = VAE_df['Date of VAE Decision'].max()
        return VAE_df[VAE_df['Date of VAE Decision'] == date]['Net Senior Leverage'].iloc[0]

    except:
        return Permitted_Net_Senior_Leverage_CE


# DG((a)(ii)=IF(OR(B12="First Lien",B12="Last Out"),IF(AND((CX12-CH12)>0.5,CX12>4),"Yes","No"),"No")
def Net_Senior_Leverage_Ratio_Test_fun(Loan_Type, current_Permitted_Net_Senior_Leverage, VAE_Net_Senior_Leverage):
    if Loan_Type == "First Lien" or Loan_Type == "Last Out":
        if (
                current_Permitted_Net_Senior_Leverage - VAE_Net_Senior_Leverage) > 0.5 and current_Permitted_Net_Senior_Leverage > 4:
            return "Yes"
        else:
            return "No"
    else:
        return "No"


# =IFERROR(IF(AND(B12<>"Recurring Revenue",DD12/DC12<0.85,DD12<1.5),"Yes","No"),"-")
def Cash_Interest_Coverage_Ratio_Test_fun(Loan_Type, Current_Interest_Coverage, Interest_Coverage):
    try:
        if np.isnan(Current_Interest_Coverage):
            return "-"
        if Loan_Type != 'Recurring Revenue' and (
                Current_Interest_Coverage / Interest_Coverage) < 0.85 and Current_Interest_Coverage < 1.5:
            return "Yes"
        else:
            return "No"
    except:
        return "-"


# CG Columns--->Permitted_Net_Total_Leverage
# =IFERROR((CC11-CA11)/BS11,"-")
def Permitted_Net_Total_Leverage_fun(Initial_Total_Debt, Initial_Unrestricted_Cash, Permitted_TTM_EBITDA):
    try:
        return (Initial_Total_Debt - Initial_Unrestricted_Cash) / Permitted_TTM_EBITDA

    except:
        return "-"


# VAE--->Net Total Leverage =IFERROR((K5-L5)/H5,"-")
def Net_Total_Leverage_fun(Total_Debt, Unrestricted_Cash, TTM_EBITDA):
    try:
        return (Total_Debt - Unrestricted_Cash) / TTM_EBITDA
    except:
        return "-"


# CI Column--->VAE Net Total Leverage
# =IFERROR(INDEX(VAE,MATCH(A11&MAX(IF(VAE!$C$5:$C$100=A11,IF(VAE!$F$5:$F$100<=Availability!$F$12,IF(VAE!$D$5:$D$100="(A) Credit Quality Deterioration Event",VAE!$F$5:$F$100)))),VAE!$C$5:$C$100&VAE!$F$5:$F$100,0),MATCH("Net Total Leverage",VAE!$H$4:$S$4,0)),CG11)
def VAE_Net_Total_Leverage_fun(Permitted_Net_Total_Leverage, Borrower, Measurement_Date, VAE_dataframe):
    try:
        VAE_df = VAE_dataframe[VAE_dataframe['Borrower'] == Borrower]
        VAE_df = VAE_df[VAE_df['Date of VAE Decision'] <= Measurement_Date]
        VAE_df = VAE_df[VAE_df['Event Type'] == "(A) Credit Quality Deterioration Event"]
        date = VAE_df['Date of VAE Decision'].max()
        return VAE_df[VAE_df['Date of VAE Decision'] == date]['Net Total Leverage'].iloc[0]
    except:
        return Permitted_Net_Total_Leverage


# DH column--->(a) (iii) Net Total Leverage Ratio Test = IF(B12="Second Lien",IF(AND((CZ12-CI12)>0.5,CZ12>5),"Yes","No"),"No")
def Net_Total_Leverage_Ratio_Test_fun(Loan_Type, VAE_Net_Total_Leverage, Permitted_Net_Total_Leverage):
    if Loan_Type == "Second Lien":
        if ((Permitted_Net_Total_Leverage - VAE_Net_Total_Leverage) > 0.5 and Permitted_Net_Total_Leverage > 5):
            return "Yes"
        else:
            return "No"
    else:
        return "No"


# CM Column--->Initial Multiple = IF(B11="Recurring Revenue",CC11/CK11,0)
def Initial_Multiple_fun(Loan_Type, Initial_Total_Debt, Initial_Recurring_Revenue):
    if Loan_Type == "Recurring Revenue":
        return Initial_Total_Debt / Initial_Recurring_Revenue
    else:
        return 0


# CN column--->VAE Multiple = IFERROR(IF(B11<>"Recurring Revenue",0,INDEX(VAE,MATCH(A11&MAX(IF(VAE!$C$5:$C$100=A11,IF(VAE!$F$5:$F$100<=Availability!$F$12,IF(VAE!$D$5:$D$100="(A) Credit Quality Deterioration Event",VAE!$F$5:$F$100)))),VAE!$C$5:$C$100&VAE!$F$5:$F$100,0),MATCH("Recurring Revenue Multiple",VAE!$H$4:$S$4,0))),CM11)
def VAE_Multiple_fun(Loan_type, Borrower, Measurement_Date, Initial_Multiple, VAE_dataframe):
    try:
        if Loan_type == "Recurring Revenue":
            return 0
        else:
            VAE_df = VAE_dataframe[VAE_dataframe['Borrower'] == Borrower]
            VAE_df = VAE_df[VAE_df['Date of VAE Decision'] <= Measurement_Date]
            VAE_df = VAE_df[VAE_df['Event Type'] == "(A) Credit Quality Deterioration Event"]
            date = VAE_df['Date of VAE Decision'].max()
        return VAE_df[VAE_df['Date of VAE Decision'] == date]['Recurring Revenue Multiple'].iloc[0]
    except:
        return Initial_Multiple


# DI column--->(b) (i) Recurring Revenue Multiple = IF(B11="Recurring Revenue",IF(AND((CO11-CN11)>0.25,CO11>1),"Yes","No"),"No")
def Recurring_Revenue_Multiple_fun(Loan_Type, Current_Multiple, VAE_Multiple):
    if Loan_Type == "Recurring Revenue":
        if (Current_Multiple - VAE_Multiple) > 0.25 and Current_Multiple > 1:
            return "Yes"
        else:
            return "No"
    else:
        return "No"


# CQ column--->VAE Liquidity = IFERROR(IF(B11<>"Recurring Revenue",0,INDEX(VAE,MATCH(A11&MAX(IF(VAE!$C$5:$C$100=A11,IF(VAE!$F$5:$F$100<=Availability!$F$12,IF(VAE!$D$5:$D$100="(A) Credit Quality Deterioration Event",VAE!$F$5:$F$100)))),VAE!$C$5:$C$100&VAE!$F$5:$F$100,0),MATCH("Liquidity",VAE!$H$4:$S$4,0))),CP11)
def VAE_Liquidity_fun(Loan_Type, Borrower, Measurement_Date, Initial_Liquidity, VAE_dataframe):
    try:
        if Loan_Type != "Recurring Revenue":
            return 0
        else:
            VAE_df = VAE_dataframe[VAE_dataframe['Borrower'] == Borrower]
            VAE_df = VAE_df[VAE_df['Date of VAE Decision'] <= Measurement_Date]
            VAE_df = VAE_df[VAE_df['Event Type'] == "(A) Credit Quality Deterioration Event"]
            date = VAE_df['Date of VAE Decision'].max()
            return VAE_df[VAE_df['Date of VAE Decision'] == date]['Liquidity'].iloc[0]
    except:
        return Initial_Liquidity


# DJ Column -->(b) (ii) Liquidity = IF(B11="Recurring Revenue",IF((CR11/CQ11)<=0.85,"Yes","No"),"No")
def Liquidity_fun(Loan_Type, Current_Liquidity, VAE_Liquidity):
    if Loan_Type == "Recurring Revenue":
        if (Current_Liquidity / VAE_Liquidity) <= 0.85:
            return "Yes"
        else:
            return "No"
    else:
        return "No"


# VAE Trigger-- Column
# =IF(OR(DF11="Yes",DG11="Yes",DH11="Yes",DI11="Yes",DJ11="Yes",DK11="Yes",DL11="Yes",DM11="Yes",DN11="Yes",DO11="Yes",DP11="Yes",DQ11="Yes",
# DR11="Yes",DS11="Yes",DT11="Yes",DU11="Yes"),"Yes","-")
def VAE_Trigger_fun(Cash_Interest_Coverage_Ratio_Test_DF, Net_Senior_Leverage_Ratio_Test_DG,
                    Net_Total_Leverage_Ratio_Test_DH, Recurring_Revenue_Multiple_DI, Liquidity_DJ,
                    Obligor_Payment_Default_DK, Default_Rights_Remedies_Exercised_DL,
                    Reduces_waives_Principal_DM, Extends_Maturity_Payment_Date_DN, Waives_Interest_DO,
                    Subordinates_Loan_DP, Releases_Collateral_Lien_DQ, Amends_Covenants_DR,
                    Amends_Permitted_Lien_or_Indebtedness_DS, Insolvency_Event_DT,
                    Failure_to_Deliver_Financial_Statements_DU):
    if (
            Cash_Interest_Coverage_Ratio_Test_DF == "Yes" or Net_Senior_Leverage_Ratio_Test_DG == "Yes" or Net_Total_Leverage_Ratio_Test_DH == "Yes" or Recurring_Revenue_Multiple_DI == "Yes" or
            Liquidity_DJ == "Yes" or Obligor_Payment_Default_DK == "Yes" or Default_Rights_Remedies_Exercised_DL == "Yes" or Reduces_waives_Principal_DM == "Yes" or Extends_Maturity_Payment_Date_DN == "Yes" or
            Waives_Interest_DO == "Yes" or Subordinates_Loan_DP == "Yes" or Releases_Collateral_Lien_DQ == "Yes" or Amends_Covenants_DR == "Yes" or Amends_Permitted_Lien_or_Indebtedness_DS == "Yes" or Insolvency_Event_DT == "Yes" or Failure_to_Deliver_Financial_Statements_DU == "Yes"):
        return "Yes"
    else:
        return "No"


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
    return df_Portfolio1[['Borrower', 'Loan Type', 'Permitted TTM EBITDA Current']]


def permittedNetSeniorLeverage_CX(df_Portfolio1, df_Ebitda1, df_VAE1):
    df_Portfolio1['Permitted TTM EBITDA Current'] = permittedTTMEBITDA_BZ(df_Portfolio1, df_Ebitda1, df_VAE1)[
        'Permitted TTM EBITDA Current']
    df_Portfolio1['Permitted Net Senior Leverage'] = df_Portfolio1.apply(
        lambda x: Permitted_Net_senior_Leverage(x['Senior Debt'], x['Current Unrestricted Cash'],
                                                x['Permitted TTM EBITDA Current']), axis=1)
    return df_Portfolio1[['Borrower', 'Loan Type', 'Permitted Net Senior Leverage']]


def permittedNetTotalLeverage_CZ(df_Portfolio1, df_Ebitda1, df_VAE1):
    df_Portfolio1['Permitted TTM EBITDA Current'] = permittedTTMEBITDA_BZ(df_Portfolio1, df_Ebitda1, df_VAE1)[
        'Permitted TTM EBITDA Current']
    df_Portfolio1['Permitted Net Total Leverage'] = df_Portfolio1.apply(
        lambda x: permittedNetTotalLeverage(x['Total Debt'], x['Current Unrestricted Cash'],
                                            x['Permitted TTM EBITDA Current']), axis=1)
    return df_Portfolio1[['Borrower', 'Loan Type', 'Permitted Net Total Leverage']]


def returnExcess(Borrower, ExcessEQ, LargestIndustry):
    print(LargestIndustry)
    if int(LargestIndustry) <= 5:
        return Borrower, ExcessEQ
    return None, None


def top5LargestIndustries(df_Portfolio1):
    df_Portfolio1['Borrower_largestIndustry'], df_Portfolio1['Excess_EQ_largestIndustry'] = zip(
        *df_Portfolio1.apply(lambda x: returnExcess(x['Borrower'], x['Excess Largest Industry'], x['Largest Industry']),
                             axis=1))
    df = df_Portfolio1[['Borrower_largestIndustry', 'Excess_EQ_largestIndustry']].copy()
    df_Portfolio1 = df_Portfolio1.drop(columns=['Borrower_largestIndustry', 'Excess_EQ_largestIndustry'])
    df = df[~((df['Borrower_largestIndustry'].isnull()) & (df['Excess_EQ_largestIndustry'].isnull()))]
    df = df.rename(
        columns={'Borrower_largestIndustry': 'Borrower', 'Excess_EQ_largestIndustry': 'Excess for the Industry'})
    df.reset_index(inplace=True)
    res = sum(df['Excess for the Industry'])
    return 'Total Excess concentration for top 5 Industries:   {}'.format(res), df.drop(columns=['index'])


def returnExcessObligor(Borrower, Rank_EJ, LargestExcess):
    if Rank_EJ <= 5 and Rank_EJ > 0:
        return Borrower, LargestExcess
    return None, None


def Top5LargestExcess(df_Portfolio1):

    df_Portfolio1['Borrower_Rank'], df_Portfolio1['Largest_Excess_Rank'] = zip(
        *df_Portfolio1.apply(lambda x: returnExcessObligor(x['Borrower'], x['Rank EJ'], x['Excess Largest Obligor']), axis=1))
    df = df_Portfolio1[['Borrower_Rank', 'Largest_Excess_Rank']].copy()
    df_Portfolio1 = df_Portfolio1.drop(columns=['Borrower_Rank', 'Largest_Excess_Rank'])
    df_Portfolio1.columns
    df = df[~((df['Borrower_Rank'].isnull()) & (df['Largest_Excess_Rank'].isnull()))]
    df = df.rename(columns={'Borrower_Rank': 'Borrower', 'Largest_Excess_Rank': 'Largest Excess'})
    df.reset_index(drop=True, inplace=True)
    res = sum(df['Largest Excess'])
    return 'Total Excess concentration for top 5 Obligors:   {}'.format(res), df

# def calculateAvailability(df_Portfolio1, df_Tiers1, df_Ebitda1, df_VAE1, df_Availability1, df_ExcessConcentration1,
#                           df_Industries1, df_BorrowerOutstandings1):
#     measurement_date = df_Availability1['Value'].iloc[0]
#     Tier_1_1L = df_Tiers1['First Lien Loans'].values[0]
#     Tier_2_1L = df_Tiers1['First Lien Loans'].values[1]
#     Tier_3_1L = df_Tiers1['First Lien Loans'].values[2]
#     Tier_1_2L = df_Tiers1['FLLO/2nd Lien Loans'].values[0]
#     Tier_2_2L = df_Tiers1['FLLO/2nd Lien Loans'].values[1]
#     Tier_3_2L = df_Tiers1['FLLO/2nd Lien Loans'].values[2]
#     Tier_1_ApplicableValue = df_Tiers1['Applicable Collateral Value'].values[0]
#     Tier_2_ApplicableValue = df_Tiers1['Applicable Collateral Value'].values[1]
#     Tier_3_ApplicableValue = df_Tiers1['Applicable Collateral Value'].values[2]
#     EBITDA_Addback_1 = df_Ebitda1['EBITDA'].values[0]
#     EBITDA_Addback_2 = df_Ebitda1['EBITDA'].values[1]
#     EBITDA_Addback_3 = df_Ebitda1['EBITDA'].values[2]
#     Add_Backs_10MM = df_Ebitda1['Permitted Add-Backs'].values[1]
#     Add_Backs_10_50MM = df_Ebitda1['Permitted Add-Backs'].values[3]
#     Add_Backs_50MM = df_Ebitda1['Permitted Add-Backs'].values[5]
#     Tier_1_RR = df_Tiers1['Recurring Revenue'].values[0]
#     Tier_2_RR = df_Tiers1['Recurring Revenue'].values[1]
#     Tier_3_RR = df_Tiers1['Recurring Revenue'].values[2]
#     global df_newBorrowerPortfolio
#     df_newBorrowerPortfolio = df_Portfolio1.tail(1)
#     global df_newBorrowerVAE
#     df_newBorrowerVAE = df_VAE1.tail(1)
#     # graphvizAdjusted = GraphvizOutput()
#     # graphvizAdjusted.output_type = 'pdf'
#     # graphvizAdjusted.output_file = 'AdjustedBorrowingFlow.pdf'
#     #
#     # with PyCallGraph(output=graphvizAdjusted):
#
#     df_Portfolio1['Add Back Percentage'] = df_Portfolio1.apply(
#         lambda x: Add_Back_Percentage(x['Adjusted TTM EBITDA_Initial'], x['EBITDA Addbacks']), axis=1)
#
#     df_Portfolio1['Capped AddBack Percentage'] = df_Portfolio1.apply(
#         lambda x: Capped_Addback_Percentage(x['Loan Type'], x['Rated B- or better'],
#                                             x['Adjusted TTM EBITDA_Initial'],
#                                             x['EBITDA Addbacks'],
#                                             x['Initial Debt-to Cash Capitalization Ratio of Obligor'],
#                                             EBITDA_Addback_3,
#                                             EBITDA_Addback_1, Add_Backs_10MM, Add_Backs_10_50MM, Add_Backs_50MM),
#         axis=1)
#
#     df_Portfolio1['Excess Add-Backs'] = df_Portfolio1.apply(
#         lambda x: Excess_AddBacks(x['Adjusted TTM EBITDA_Initial'], x['EBITDA Addbacks'], x['Add Back Percentage'],
#                                   x['Capped AddBack Percentage']), axis=1)
#
#     df_Portfolio1['Permitted TTM EBITDA'] = df_Portfolio1.apply(
#         lambda x: Permitted_TTM_EBITDA(x['Adjusted TTM EBITDA_Initial'], x['Excess Add-Backs'],
#                                        x['Agent Approved Add-Backs']), axis=1)
#
#     df_Portfolio1['EBITDA Haircut'] = df_Portfolio1.apply(
#         lambda x: EBITDA_Haircut(x['Permitted TTM EBITDA'], x['Adjusted TTM EBITDA_Initial']), axis=1)
#
#     df_Portfolio1['Inclusion EBITDA Haircut'] = df_Portfolio1.apply(
#         lambda x: Inclusion_EBITDA_Haircut(x['Borrower'], df_VAE1[df_VAE1['Borrower'] == x['Borrower']],
#                                            x['EBITDA Haircut']), axis=1)
#
#     df_Portfolio1['Permitted TTM EBITDA Current'] = df_Portfolio1.apply(
#         lambda x: Permitted_TTM_EBITDA_Current(x['Agent Post-Inclusion Adj. Haircut'],
#                                                x['Inclusion EBITDA Haircut'],
#                                                x['Adjusted TTM EBITDA_Current'],
#                                                x['Agent Adjusted Addback Haircut']),
#         axis=1)
#
#     df_Portfolio1['Permitted Net Senior Leverage'] = df_Portfolio1.apply(
#         lambda x: Permitted_Net_senior_Leverage(x['Senior Debt'], x['Current Unrestricted Cash'],
#                                                 x['Permitted TTM EBITDA Current']), axis=1)
#
#     df_Portfolio1['Amounts in excess of Tier 3 Reclassified as zero value'] = df_Portfolio1.apply(
#         lambda x: Amounts_in_excess_of_Tier_3(x['Loan Type'], x['Permitted Net Senior Leverage'],
#                                               x['Borrower Outstanding Principal Balance'], Tier_3_2L), axis=1)
#
#     df_Portfolio1['Amounts in excess of Tier 3 Reclassified as 2nd Lien'] = df_Portfolio1.apply(
#         lambda x: Amounts_excess_of_Tier3_Reclassified_2nd_Lien(x['Loan Type'], x[
#             'Amounts in excess of Tier 3 Reclassified as zero value'], x['Permitted Net Senior Leverage'],
#                                                                 x['Borrower Outstanding Principal Balance'],
#                                                                 Tier_3_1L),
#         axis=1)
#
#     df_Portfolio1['First Lien Amount'] = df_Portfolio1.apply(
#         lambda x: First_Lien_Amount(x['Loan Type'], x['Borrower Outstanding Principal Balance'],
#                                     x['Amounts in excess of Tier 3 Reclassified as 2nd Lien'],
#                                     x['Amounts in excess of Tier 3 Reclassified as zero value']), axis=1)
#
#     df_Portfolio1['EBITDA > $5MM'] = df_Portfolio1.apply(lambda x: EBITDA_5MM(x['Permitted TTM EBITDA']), axis=1)
#
#     df_Portfolio1['Second Lien or FLLO EBITDA >$10MM'] = df_Portfolio1.apply(
#         lambda x: Second_Lien_Or_FLLO_EBITDA(x['Loan Type'], x['Permitted TTM EBITDA']), axis=1)
#
#     df_Portfolio1['Eligible Cov-Lite'] = df_Portfolio1.apply(
#         lambda x: Eligible_Cov_Lite(x['Cov-Lite?'], x['Permitted TTM EBITDA'], x['Initial Senior Debt'],
#                                     x['Rated B- or better']), axis=1)
#
#     df_Portfolio1['Eligible Recurring Revenue'] = df_Portfolio1.apply(
#         lambda x: Eligible_recurring_revenue(x['Loan Type'], x['Initial Recurring Revenue'],
#                                              x['Initial Total Debt']),
#         axis=1)
#
#     df_Portfolio1['Eligibility Check'] = df_Portfolio1.apply(
#         lambda x: Eligibility_Check(x['Eligible Loan'], x['EBITDA > $5MM'], x['Second Lien or FLLO EBITDA >$10MM'],
#                                     x['Eligible Cov-Lite'], x['Eligible Recurring Revenue'],
#                                     x['Permitted TTM EBITDA Current']), axis=1)
#
#     df_Portfolio1['Permitted Net Total Leverage'] = df_Portfolio1.apply(
#         lambda x: permittedNetTotalLeverage(x['Total Debt'], x['Current Unrestricted Cash'],
#                                             x['Permitted TTM EBITDA Current']), axis=1)
#
#     df_Portfolio1['Current Multiple'] = df_Portfolio1.apply(
#         lambda x: currentMultiple(x['Loan Type'], x['Total Debt'], x['Current Recurring Revenue']), axis=1)
#
#     df_Portfolio1['Applicable Collateral Value'] = df_Portfolio1.apply(
#         lambda x: applicableCollateralValue(x['Eligibility Check'], x['Loan Type'],
#                                             x['Permitted Net Senior Leverage'], x['Permitted Net Total Leverage'],
#                                             x['Current Multiple'], Tier_1_1L, Tier_1_ApplicableValue, Tier_2_1L,
#                                             Tier_2_ApplicableValue, Tier_3_ApplicableValue, Tier_1_2L, Tier_2_2L,
#                                             Tier_1_RR, Tier_2_RR), axis=1)
#
#     df_Portfolio1['VAE'], df_Portfolio1['Event Type'], df_Portfolio1['VAE Effective Date'], df_Portfolio1[
#         'Agent Assigned Value'] = zip(*df_Portfolio1.apply(
#         lambda x: funcVAE(df_VAE1[df_VAE1['Borrower'] == x['Borrower']], measurement_date),
#         axis=1))
#
#     df_Portfolio1['Assigned Value'] = df_Portfolio1.apply(
#         lambda x: assignedValues(x['VAE'], x['Actual Purchase Price'], x['Agent Assigned Value'],
#                                  x['Applicable Collateral Value']), axis=1)
#
#     df_Portfolio1['First Lien Value'] = df_Portfolio1.apply(
#         lambda x: firstLienValue(x['Assigned Value'], x['First Lien Amount']), axis=1)
#
#     df_Portfolio1['Second Lien Value'] = df_Portfolio1.apply(
#         lambda x: secondLienValue(x['Amounts in excess of Tier 3 Reclassified as 2nd Lien'], x['Assigned Value']),
#         axis=1)
#
#     df_Portfolio1['Amounts in excess of Tier 3 Reclassified as zero valueZ'] = df_Portfolio1.apply(
#         lambda x: amountExcessTier3ReclassifiedZeroValue(x['Loan Type'],
#                                                          x['Borrower Outstanding Principal Balance'],
#                                                          x['Permitted Net Total Leverage'], Tier_3_2L), axis=1)
#
#     df_Portfolio1['Last Out or 2nd Lien Amount'] = df_Portfolio1.apply(
#         lambda x: lastOutorSecondLienAmount(x['Loan Type'], x['Borrower Outstanding Principal Balance'],
#                                             x['Amounts in excess of Tier 3 Reclassified as zero valueZ']), axis=1)
#
#     df_Portfolio1['FLLO Value'] = df_Portfolio1.apply(
#         lambda x: FLLOValue(['Loan Type'], x['Last Out or 2nd Lien Amount'], x['Assigned Value']), axis=1)
#
#     df_Portfolio1['Second Lien ValueAC'] = df_Portfolio1.apply(
#         lambda x: secondLienValueAC(x['Loan Type'], x['Last Out or 2nd Lien Amount'], x['Assigned Value']), axis=1)
#
#     df_Portfolio1['Amounts in excess of 2.5x RR Multiple Reclassified as zero value'] = df_Portfolio1.apply(
#         lambda x: amountsExcess25RRMultipleReclassifiedZero(x['Loan Type'], x['Current Multiple'],
#                                                             x['Borrower Outstanding Principal Balance'], Tier_3_RR),
#         axis=1)
#
#     df_Portfolio1['Recurring Revenue Amount'] = df_Portfolio1.apply(
#         lambda x: recurringRevenueAmount(x['Loan Type'], x['Borrower Outstanding Principal Balance'],
#                                          x['Amounts in excess of 2.5x RR Multiple Reclassified as zero value']),
#         axis=1)
#
#     df_Portfolio1['Recurring Revenue Value'] = df_Portfolio1.apply(
#         lambda x: recurringRevenueValue(x['Loan Type'], x['Recurring Revenue Amount'], x['Assigned Value']), axis=1)
#
#     df_Portfolio1['Adjusted Borrowing Value'] = df_Portfolio1.apply(
#         lambda x: adjustedBorrowingValue(x['First Lien Value'], x['Second Lien Value'], x['FLLO Value'],
#                                          x['Second Lien ValueAC'], x['Recurring Revenue Value']), axis=1)
#
#     # Output Adjusted Borrowing values
#     Adjusted_Borrowing_Value_for_Eligible_Loans = df_Portfolio1['Adjusted Borrowing Value'].sum()
#     # df_Portfolio1.to_excel('OutputAdjustedBorrowing.xlsx', index=False)
#
#     global df_AdjustedIntermediate
#     df_AdjustedIntermediate = df_Portfolio1[
#         ['First Lien Value', 'Second Lien Value', 'FLLO Value', 'Second Lien ValueAC', 'Recurring Revenue Value',
#          'Recurring Revenue Amount', 'Amounts in excess of Tier 3 Reclassified as 2nd Lien',
#          'Assigned Value', 'Applicable Collateral Value', 'Current Multiple', 'Permitted Net Total Leverage',
#          'Permitted Net Senior Leverage', 'Permitted TTM EBITDA', 'Permitted TTM EBITDA Current',
#          'Excess Add-Backs', 'Capped AddBack Percentage', 'Add Back Percentage', 'Adjusted Borrowing Value']]
#
#     # graphvizExcessConc = GraphvizOutput()
#     # graphvizExcessConc.output_type = 'pdf'
#     # graphvizExcessConc.output_file = 'ExcessConcentrationFlow.pdf'
#     #
#     # with PyCallGraph(output=graphvizExcessConc):
#     # Calculations for Excess concentration
#     try:
#         df_Portfolio1['Adjusted Borrowing Value_DW'] = df_Portfolio1['Adjusted Borrowing Value']
#     except:
#         df_Portfolio1['Adjusted Borrowing Value_DW'] = 0
#
#     # Calculating Obligor for (a) First Lien Last Out, Second Lien Loan, EBITDA <$10MM not in Top Three Obligors
#     df_Portfolio1['Obligor_DY'] = df_Portfolio1.groupby('Borrower')['Adjusted Borrowing Value_DW'].transform('sum')
#
#     # Remove dupes DZ
#     df_Portfolio1['Remove Dupes'] = df_Portfolio1['Obligor_DY']
#     is_duplicate = df_Portfolio1['Borrower'].duplicated(keep='first')
#     df_Portfolio1['Remove Dupes'] = df_Portfolio1['Obligor_DY'].where(~is_duplicate, 0)
#
#     # Rank column to be used as a reference for other rank coulmns
#     df_Portfolio1['rank'] = df_Portfolio1['Remove Dupes'].rank(ascending=False, method='first')
#     df_Portfolio1['Rank_EB'] = df_Portfolio1.apply(
#         lambda x: rankEB(x['Remove Dupes'], x['rank'],
#                          df_Portfolio1[df_Portfolio1['Remove Dupes'] == x['Remove Dupes']]),
#         axis=1)
#
#     # Rank EA
#     # =IFERROR(INDEX(EB:EB,MATCH(A11,A:A,0)),0)
#     df_Portfolio1['Rank_EA'] = df_Portfolio1.apply(
#         lambda x: df_Portfolio1[df_Portfolio1['Borrower'] == x['Borrower']]['Rank_EB'].max(), axis=1)
#
#     df_Portfolio1['Advance Rate Class'] = df_Portfolio1.apply(
#         lambda x: advanceRateClass(x['Permitted TTM EBITDA Current'], x['Rated B- or better']), axis=1)
#
#     df_Portfolio1['Advance Rate Definition'] = df_Portfolio1.apply(
#         lambda x: advanceRateDefinition(x['Borrower'], x['Loan Type'], x['Advance Rate Class']), axis=1)
#
#     df_Portfolio1['Qualifies?'] = df_Portfolio1.apply(
#         lambda x: qualifies(x['Loan Type'], x['Advance Rate Definition'], x['Rank_EA']), axis=1)
#
#     df_Portfolio1['Excess EBITDA not in top 3'] = df_Portfolio1.apply(
#         lambda x: excessEC(df_Portfolio1[df_Portfolio1['Borrower'] == x['Borrower']],
#                            x['Rank_EA'], x['Obligor_DY'], x['Adjusted Borrowing Value_DW'], x['Qualifies?']),
#         axis=1)
#
#     # Calculating Applicable Test LImit for Excess Concentration Limit table
#     df_ExcessConcentration1['Applicable Test Limit'] = df_ExcessConcentration1.apply(
#         lambda x: max(x['Concentration Limit Percentage'] * Adjusted_Borrowing_Value_for_Eligible_Loans,
#                       x['Concentration Limit Values']), axis=1)
#
#     # Calculate Excess Largest Obligor (EK)
#     # EK --> EI, EG, EE, ED, A
#     # EI --> EJ(EH-->EG-->ED-->(DW,EC))
#     # ED (Revised Value)  =IFERROR(MAX(0,DW11-EC11),0)
#
#     try:
#         df_Portfolio1['Revised Value ED'] = df_Portfolio1.apply(
#             lambda x: max(0, x['Adjusted Borrowing Value_DW'] - x['Excess EBITDA not in top 3']), axis=1)
#     except:
#         df_Portfolio1['Revised Value ED'] = 0
#
#     # Top 3 MAX (EE) =IFERROR('Concentration Limits'!$J$38,0)
#     try:
#         df_Portfolio1['Top 3 Max'] = df_ExcessConcentration1['Applicable Test Limit'].loc[1]
#     except:
#         df_Portfolio1['Top 3 Max'] = 0
#
#     # Obligor (EG) =IFERROR(SUMIF($A:$A,$A11,$ED:$ED),0)
#     try:
#         df_Portfolio1['Obligor EG'] = df_Portfolio1.groupby('Borrower')['Revised Value ED'].transform('sum')
#     except:
#         df_Portfolio1['Obligor EG'] = 0
#
#     # Remove Dupes (EH) = IFERROR(IF(MATCH($A11,$A:$A,0)=ROW(),$EG11,0),0)--> for Largest Obligor
#     # match the value of A in column A to the value of B in column B
#     # df['match'] = df['A'].map(df.set_index('B')['A'])
#     df_Portfolio1['Remove Dupes EH'] = df_Portfolio1['Obligor EG']
#     is_duplicate = df_Portfolio1['Borrower'].duplicated(keep='first')
#     df_Portfolio1['Remove Dupes EH'] = df_Portfolio1['Obligor EG'].where(~is_duplicate, 0)
#
#     df_Portfolio1['Rank EJ'] = df_Portfolio1.apply(lambda x: rankEJ(x['Remove Dupes EH'], x['rank'], df_Portfolio1[
#         df_Portfolio1['Remove Dupes EH'] == x['Remove Dupes EH']]), axis=1)
#
#     # Rank EI
#     # =IFERROR(INDEX(EJ:EJ,MATCH(A11,A:A,0)),0)
#     df_Portfolio1['Rank_EI'] = df_Portfolio1.apply(
#         lambda x: df_Portfolio1[df_Portfolio1['Borrower'] == x['Borrower']]['Rank EJ'].max(), axis=1)
#
#     df_Portfolio1['Excess Largest Obligor'] = df_Portfolio1.apply(
#         lambda x: largestExcess(df_Portfolio1[df_Portfolio1['Borrower'] == x['Borrower']],
#                                 x['Rank_EI'], x['Obligor EG'], x['Top 3 Max'], x['Revised Value ED']), axis=1)
#
#     # Other Max (EF)
#     try:
#         df_Portfolio1['Other Max'] = df_ExcessConcentration1['Applicable Test Limit'].loc[2]
#     except:
#         df_Portfolio1['Other Max'] = 0
#
#     df_Portfolio1['Other Excess'] = df_Portfolio1.apply(
#         lambda x: otherExcess(df_Portfolio1[df_Portfolio1['Borrower'] == x['Borrower']],
#                               x['Rank_EI'], x['Obligor EG'], x['Other Max'], x['Revised Value ED']), axis=1)
#
#     df_Industries1['O/S Value'] = df_Industries1.apply(
#         lambda x: osValue(df_Portfolio1[df_Portfolio1['GICS \nIndustry'] == x['S&P Industry Classification ']])
#         , axis=1)
#     # Percentage column for Industries Dataframe
#     df_Industries1['Percentage'] = df_Industries1['O/S Value'] / df_Industries1['O/S Value'].sum()
#
#     df_Industries1['Industry Rank'] = df_Industries1['O/S Value'].rank(ascending=False, method='min')
#
#     df_Industries1['Industry Rank'] = df_Industries1.apply(
#         lambda x: 0 if x['O/S Value'] == 0 else x['Industry Rank'],
#         axis=1)
#
#     df_Portfolio1['Largest Industry'] = df_Portfolio1.apply(
#         lambda x: largestIndustry(
#             df_Industries1[df_Industries1['S&P Industry Classification '] == x['GICS \nIndustry']]),
#         axis=1)
#
#     # Revised Value EM
#     # =IFERROR(MAX(0,ED11-EK11-EL11),0)
#     try:
#         df_Portfolio1['Revised Value EM'] = df_Portfolio1.apply(
#             lambda x: max(0, (x['Revised Value ED'] - x['Excess Largest Obligor'] - x['Other Excess'])), axis=1)
#     except:
#         df_Portfolio1['Revised Value EM'] = 0
#
#     # Loan Limit (EO)
#     # =IFERROR(SUMIF($AZ:$AZ,$AZ11,EM:EM),0)
#     try:
#         df_Portfolio1['Loan Limit'] = df_Portfolio1.groupby('GICS \nIndustry')['Revised Value EM'].transform('sum')
#     except:
#         df_Portfolio1['Loan Limit'] = 0
#
#     # Max (EN)
#     # Concentraion limit J40
#     df_Portfolio1['Max EN'] = df_ExcessConcentration1['Applicable Test Limit'].loc[3]
#
#     df_Portfolio1['Excess Largest Industry'] = df_Portfolio1.apply(
#         lambda x: excessEQ(df_Portfolio1[df_Portfolio1['GICS \nIndustry'] == x['GICS \nIndustry']],
#                            x['Largest Industry'], x['Loan Limit'], x['Max EN'], x['Revised Value EM']), axis=1)
#
#     df_Portfolio1['Revised Value ER'] = df_Portfolio1.apply(
#         lambda x: revisedValueER(x['Revised Value EM'], x['Excess Largest Industry']), axis=1)
#
#     # Max (ES)
#     try:
#         df_Portfolio1['Max ES'] = df_ExcessConcentration1['Applicable Test Limit'].loc[4]
#     except:
#         df_Portfolio1['Max ES'] = 0
#
#     df_Portfolio1['Loan Limit ET'] = df_Portfolio1.apply(
#         lambda x: loanLimit(df_Portfolio1[df_Portfolio1['GICS \nIndustry'] == x['GICS \nIndustry']],
#                             x['GICS \nIndustry'],
#                             x['Revised Value ER']), axis=1)
#
#     df_Portfolio1['2nd Largest Industry'] = df_Portfolio1.apply(lambda x: secondLargestIndustry(
#         df_Industries1[df_Industries1['S&P Industry Classification '] == x['GICS \nIndustry']]), axis=1)
#
#     df_Portfolio1['Excess 2nd Largest Industry'] = df_Portfolio1.apply(
#         lambda x: excessEV(df_Portfolio1[df_Portfolio1['GICS \nIndustry'] == x['GICS \nIndustry']],
#                            x['2nd Largest Industry'], x['Loan Limit ET'], x['Max ES'], x['Revised Value ER']),
#         axis=1)
#
#     df_Portfolio1['Revised Value EW'] = df_Portfolio1.apply(
#         lambda x: thirdLargestIndustry(x['Revised Value ER'], x['Excess 2nd Largest Industry']), axis=1)
#
#     # Max EX -->
#     try:
#         df_Portfolio1['Max EX'] = df_ExcessConcentration1['Applicable Test Limit'].loc[5]
#     except:
#         df_Portfolio1['Max EX'] = 0
#
#     df_Portfolio1['Loan Limit EY'] = df_Portfolio1.apply(
#         lambda x: loanLimit(df_Portfolio1[df_Portfolio1['GICS \nIndustry'] == x['GICS \nIndustry']],
#                             x['GICS \nIndustry'],
#                             x['Revised Value EW']), axis=1)
#
#     df_Portfolio1['Excess 3rd Largest Industry'] = df_Portfolio1.apply(
#         lambda x: excessFA(df_Portfolio1[df_Portfolio1['GICS \nIndustry'] == x['GICS \nIndustry']],
#                            x['Largest Industry'],
#                            x['Loan Limit EY'], x['Max EX'], x['Revised Value EW']), axis=1)
#
#     df_Portfolio1['Revised Value FB'] = df_Portfolio1.apply(
#         lambda x: otherIndustry(x['Revised Value EW'], x['Excess 3rd Largest Industry']), axis=1)
#
#     df_Portfolio1['Loan Limit FD'] = df_Portfolio1.apply(
#         lambda x: loanLimitFD(df_Portfolio1[df_Portfolio1['GICS \nIndustry'] == x['GICS \nIndustry']],
#                               x['GICS \nIndustry'], x['Revised Value FB']), axis=1)
#
#     # Max FC
#     # =IFERROR('Concentration Limits'!$J$43,0)
#     try:
#         df_Portfolio1['Max FC'] = df_ExcessConcentration1['Applicable Test Limit'].loc[6]
#     except:
#         df_Portfolio1['Max FC'] = 0
#
#     df_Portfolio1['Excess Other Industry'] = df_Portfolio1.apply(
#         lambda x: excessFF(df_Portfolio1[df_Portfolio1['GICS \nIndustry'] == x['GICS \nIndustry']],
#                            x['Largest Industry'],
#                            x['Loan Limit FD'], x['Max FC'], x['Revised Value FB']), axis=1)
#
#     df_Portfolio1['Revised Value FG'] = df_Portfolio1.apply(
#         lambda x: revisedValueFG(x['Revised Value FB'], x['Excess Other Industry']), axis=1)
#
#     # Max FH
#     # =IFERROR('Concentration Limits'!$J$44,0)
#     try:
#         df_Portfolio1['Max FH'] = df_ExcessConcentration1['Applicable Test Limit'].loc[7]
#     except:
#         df_Portfolio1['Max FH'] = 0
#
#     df_Portfolio1['Qualifies < $10MM'] = df_Portfolio1.apply(
#         lambda x: qualifiesEbitdaLess10MM(x['Permitted TTM EBITDA Current']), axis=1)
#
#     df_Portfolio1['Loan Limit FJ'] = df_Portfolio1.apply(
#         lambda x: loanLimitFJ(df_Portfolio1[df_Portfolio1['Qualifies < $10MM'] == 'Yes'], x['Qualifies < $10MM'],
#                               x['Revised Value FG']), axis=1)
#
#     df_Portfolio1['Excess EBITDA < 10MM'] = df_Portfolio1.apply(
#         lambda x: excessFK(df_Portfolio1[df_Portfolio1['Qualifies < $10MM'] == 'Yes'], x['Loan Limit FJ'],
#                            x['Max FH'],
#                            x['Revised Value FG']), axis=1)
#
#     df_Portfolio1['Revised Value FL'] = df_Portfolio1.apply(
#         lambda x: revisedValueFL(x['Revised Value FG'], x['Excess EBITDA < 10MM']), axis=1)
#
#     # Max FM -->DIP Loans
#     # =IFERROR('Concentration Limits'!$J$45,0)
#     try:
#         df_Portfolio1['Max FM'] = df_ExcessConcentration1['Applicable Test Limit'].loc[8]
#     except:
#         df_Portfolio1['Max FM'] = 0
#
#     df_Portfolio1['Qualifies DIP Loan'] = df_Portfolio1.apply(lambda x: qualifiesDIPLoan(x['DIP Loan?']), axis=1)
#
#     df_Portfolio1['Loan Limit FO'] = df_Portfolio1.apply(
#         lambda x: loanLimitFO(df_Portfolio1[df_Portfolio1['Qualifies DIP Loan'] == 'Yes'], x['Qualifies DIP Loan'],
#                               x['Revised Value FL']), axis=1)
#
#     df_Portfolio1['Excess DIP Loans'] = df_Portfolio1.apply(
#         lambda x: excessFP(df_Portfolio1[df_Portfolio1['Qualifies DIP Loan'] == 'Yes'], x['Loan Limit FO'],
#                            x['Max FM'],
#                            x['Revised Value FL']), axis=1)
#
#     df_Portfolio1['Revised Value FQ'] = df_Portfolio1.apply(
#         lambda x: revisedValueFQ(x['Revised Value FL'], x['Excess DIP Loans']), axis=1)
#
#     # Max FR --> Cov Lite Loans
#     # =IFERROR('Concentration Limits'!$J$46,0)
#     try:
#         df_Portfolio1['Max FR'] = df_ExcessConcentration1['Applicable Test Limit'].loc[9]
#     except:
#         df_Portfolio1['Max FR'] = 0
#
#     df_Portfolio1['Qualifies Cov Lite Loan'] = df_Portfolio1.apply(lambda x: qualifiesCovLiteLoan(x['Cov-Lite?']),
#                                                                    axis=1)
#
#     df_Portfolio1['Loan Limit FT'] = df_Portfolio1.apply(
#         lambda x: loanLimitFT(df_Portfolio1[df_Portfolio1['Qualifies Cov Lite Loan'] == 'Yes'],
#                               x['Qualifies Cov Lite Loan'], x['Revised Value FQ']), axis=1)
#
#     df_Portfolio1['Excess Cov-Lite Loans'] = df_Portfolio1.apply(
#         lambda x: excessFU(df_Portfolio1[df_Portfolio1['Qualifies Cov Lite Loan'] == 'Yes'], x['Loan Limit FT'],
#                            x['Max FR'], x['Revised Value FQ']), axis=1)
#
#     df_Portfolio1['Revised Value FV'] = df_Portfolio1.apply(
#         lambda x: revisedValueFV(x['Revised Value FQ'], x['Excess Cov-Lite Loans']), axis=1)
#
#     # Max FW --> Less than Qtrly Pay
#     # =IFERROR('Concentration Limits'!$J$47,0)
#     try:
#         df_Portfolio1['Max FW'] = df_ExcessConcentration1['Applicable Test Limit'].loc[10]
#     except:
#         df_Portfolio1['Max FW'] = 0
#
#     df_Portfolio1['Qualifies Less than Qtrly'] = df_Portfolio1.apply(
#         lambda x: qualifiesLessThanQtrly(x['Paid Less than Qtrly or Mthly']), axis=1)
#
#     df_Portfolio1['Loan Limit FY'] = df_Portfolio1.apply(
#         lambda x: loanLimitFY(df_Portfolio1[df_Portfolio1['Qualifies Less than Qtrly'] == 'Yes'],
#                               x['Qualifies Less than Qtrly'], x['Revised Value FV']), axis=1)
#
#     df_Portfolio1['Excess Less than Qtrly Pay'] = df_Portfolio1.apply(
#         lambda x: excessFZ(df_Portfolio1[df_Portfolio1['Qualifies Less than Qtrly'] == 'Yes'], x['Loan Limit FY'],
#                            x['Max FW'], x['Revised Value FV']), axis=1)
#
#     df_Portfolio1['Revised Value GA'] = df_Portfolio1.apply(
#         lambda x: revisedValueGA(x['Revised Value FV'], x['Excess Less than Qtrly Pay']), axis=1)
#
#     # Max GB
#     # =IFERROR('Concentration Limits'!$J$48,0)
#     try:
#         df_Portfolio1['Max GB'] = df_ExcessConcentration1['Applicable Test Limit'].loc[11]
#     except:
#         df_Portfolio1['Max GB'] = 0
#
#     df_Portfolio1['Qualifies Foreign Currency'] = df_Portfolio1.apply(
#         lambda x: qualifiesForeignGC(x['Non-US Approved Currency?']), axis=1)
#
#     df_Portfolio1['Loan Limit GD'] = df_Portfolio1.apply(
#         lambda x: loanLimitGD(df_Portfolio1[df_Portfolio1['Qualifies Foreign Currency'] == 'Yes'],
#                               x['Qualifies Foreign Currency'], x['Revised Value GA']), axis=1)
#
#     df_Portfolio1['Excess Foreign Currency'] = df_Portfolio1.apply(
#         lambda x: excessGE(df_Portfolio1[df_Portfolio1['Qualifies Foreign Currency'] == 'Yes'], x['Loan Limit GD'],
#                            x['Max GB'], x['Revised Value GA']), axis=1)
#
#     df_Portfolio1['Revised Value GF'] = df_Portfolio1.apply(
#         lambda x: revisedValueGF(x['Revised Value GA'], x['Excess Foreign Currency']), axis=1)
#
#     # Max GG
#     # =IFERROR('Concentration Limits'!$J$49,0)
#     try:
#         df_Portfolio1['Max GG'] = df_ExcessConcentration1['Applicable Test Limit'].loc[12]
#     except:
#         df_Portfolio1['Max GG'] = 0
#
#     df_Portfolio1['Qualifies Non US Country'] = df_Portfolio1.apply(
#         lambda x: qualifiesCountryGH(x['Non-US Approved Country?']), axis=1)
#
#     df_Portfolio1['Loan Limit GI'] = df_Portfolio1.apply(
#         lambda x: loanLimitGI(df_Portfolio1[df_Portfolio1['Qualifies Non US Country'] == 'Yes'],
#                               x['Qualifies Non US Country'], x['Revised Value GF']), axis=1)
#
#     df_Portfolio1['Excess Aprroved Country'] = df_Portfolio1.apply(
#         lambda x: excessGJ(df_Portfolio1[df_Portfolio1['Qualifies Non US Country'] == 'Yes'], x['Loan Limit GI'],
#                            x['Max GG'], x['Revised Value GF']), axis=1)
#
#     df_Portfolio1['Revised Value GK'] = df_Portfolio1.apply(
#         lambda x: revisedValueGK(x['Revised Value GF'], x['Excess Aprroved Country']), axis=1)
#
#     # Max GL
#     # =IFERROR('Concentration Limits'!$J$50,0)
#     try:
#         df_Portfolio1['Max GL'] = df_ExcessConcentration1['Applicable Test Limit'].loc[13]
#     except:
#         df_Portfolio1['Max GL'] = 0
#
#     df_Portfolio1['Qualifies DDTL and Revolving Loans'] = df_Portfolio1.apply(
#         lambda x: qualifiesDDTLandRevolvingGM(x['Revolving / Delayed Funding?']), axis=1)
#
#     df_Portfolio1['Loan Limit GN'] = df_Portfolio1.apply(
#         lambda x: loanLimitGN(df_Portfolio1[df_Portfolio1['Qualifies DDTL and Revolving Loans'] == 'Yes'],
#                               x['Qualifies DDTL and Revolving Loans'], x['Revised Value GK']), axis=1)
#
#     df_Portfolio1['Excess DDTL and Revolving Loans'] = df_Portfolio1.apply(
#         lambda x: excessGO(df_Portfolio1[df_Portfolio1['Qualifies DDTL and Revolving Loans'] == 'Yes'],
#                            x['Loan Limit GN'], x['Max GL'], x['Revised Value GK']), axis=1)
#
#     df_Portfolio1['Revised Value GP'] = df_Portfolio1.apply(
#         lambda x: revisedValueGP(x['Revised Value GK'], x['Excess DDTL and Revolving Loans']), axis=1)
#
#     # Max GQ
#     # =IFERROR('Concentration Limits'!$J$51,0)
#     try:
#         df_Portfolio1['Max GQ'] = df_ExcessConcentration1['Applicable Test Limit'].loc[14]
#     except:
#         df_Portfolio1['Max GQ'] = 0
#
#     df_Portfolio1['Permitted Net Senior Leverage CE'] = df_Portfolio1.apply(
#         lambda x: permittedNetSeniorLeverageCE(x['Initial Unrestricted Cash'], x['Initial Senior Debt'],
#                                                x['Permitted TTM EBITDA']), axis=1)
#
#     df_Portfolio1['Permitted Net Total Leverage CG'] = df_Portfolio1.apply(
#         lambda x: permittedNetTotalLeverageCG(x['Initial Total Debt'], x['Initial Unrestricted Cash'],
#                                               x['Permitted TTM EBITDA']), axis=1)
#
#     df_Portfolio1['Initial Multiple'] = df_Portfolio1.apply(
#         lambda x: initialMultiple(x['Loan Type'], x['Initial Total Debt'], x['Initial Recurring Revenue']), axis=1)
#
#     df_Portfolio1['Tier'] = df_Portfolio1.apply(
#         lambda x: tiers(x['Loan Type'], x['Permitted Net Senior Leverage CE'], x['Permitted Net Total Leverage CG'],
#                         x['Initial Multiple'], Tier_1_1L, Tier_2_1L, Tier_1_2L, Tier_2_2L, Tier_1_RR, Tier_2_RR),
#         axis=1)
#
#     df_Portfolio1['Qualifies Tier 3 Obligor'] = df_Portfolio1.apply(
#         lambda x: qualifiesTier3Obligor(x['Eligibility Check'], x['Tier']), axis=1)
#
#     df_Portfolio1['Loan Limit GS'] = df_Portfolio1.apply(
#         lambda x: loanLimitGS(df_Portfolio1[df_Portfolio1['Qualifies Tier 3 Obligor'] == 'Yes'],
#                               x['Qualifies Tier 3 Obligor'], x['Revised Value GP']), axis=1)
#
#     df_Portfolio1['Excess Tier 3 Obligors'] = df_Portfolio1.apply(
#         lambda x: excessGT(df_Portfolio1[df_Portfolio1['Qualifies Tier 3 Obligor'] == 'Yes'], x['Loan Limit GS'],
#                            x['Max GQ'], x['Revised Value GP']), axis=1)
#
#     df_Portfolio1['Revised Value GU'] = df_Portfolio1.apply(
#         lambda x: revisedValueGU(x['Revised Value GP'], x['Excess Tier 3 Obligors']), axis=1)
#
#     # Max GV
#     # =IFERROR('Concentration Limits'!$J$52,0)
#     try:
#         df_Portfolio1['Max GV'] = df_ExcessConcentration1['Applicable Test Limit'].loc[15]
#     except:
#         df_Portfolio1['Max GV'] = 0
#
#     df_Portfolio1['Loan Limit GW'] = df_Portfolio1.apply(
#         lambda x: loanLimitGW(df_Portfolio1[df_Portfolio1['Loan Type'] == 'Second Lien'], x['Loan Type'],
#                               x['Revised Value GU']), axis=1)
#
#     df_Portfolio1['Excess Second Lien'] = df_Portfolio1.apply(
#         lambda x: excessGX(df_Portfolio1[df_Portfolio1['Loan Type'] == x['Loan Type']], x['Loan Limit GW'],
#                            x['Max GV'], x['Revised Value GU']), axis=1)
#
#     df_Portfolio1['Revised Value GY'] = df_Portfolio1.apply(
#         lambda x: revisedValueGY(x['Revised Value GU'], x['Excess Second Lien']), axis=1)
#
#     # Max GZ (First Lien Last Out)
#     # =IFERROR('Concentration Limits'!$J$53,0)
#     try:
#         df_Portfolio1['Max GZ'] = df_ExcessConcentration1['Applicable Test Limit'].loc[16]
#     except:
#         df_Portfolio1['Max GZ'] = 0
#
#     df_Portfolio1['Loan Limit HA'] = df_Portfolio1.apply(
#         lambda x: loanLimitHA(df_Portfolio1[df_Portfolio1['Loan Type'] == 'Last Out'], x['Loan Type'],
#                               x['Revised Value GY']), axis=1)
#
#     df_Portfolio1['Excess First Lien Last Out'] = df_Portfolio1.apply(
#         lambda x: excessHB(df_Portfolio1[df_Portfolio1['Loan Type'] == x['Loan Type']], x['Loan Limit HA'],
#                            x['Max GZ'], x['Revised Value GY']), axis=1)
#
#     df_Portfolio1['Revised Value HC'] = df_Portfolio1.apply(
#         lambda x: revisedValueHC(x['Revised Value GY'], x['Excess First Lien Last Out']), axis=1)
#
#     # Max HD (Loan Maturities Greater than 6 Years)
#     # =IFERROR('Concentration Limits'!$J$54,0)
#     try:
#         df_Portfolio1['Max HD'] = df_ExcessConcentration1['Applicable Test Limit'].loc[17]
#     except:
#         df_Portfolio1['Max HD'] = 0
#
#     df_Portfolio1['Original Term'] = df_Portfolio1.apply(
#         lambda x: originalTerm(x['Acquisition Date'], x['Maturity Date']), axis=1)
#
#     df_Portfolio1['Qualifies HE'] = df_Portfolio1.apply(lambda x: qualifiesHE(x['Original Term']), axis=1)
#
#     df_Portfolio1['Loan Limit HF'] = df_Portfolio1.apply(
#         lambda x: loanLimitHF(df_Portfolio1[df_Portfolio1['Qualifies HE'] == 'Yes'], x['Qualifies HE'],
#                               x['Revised Value HC']), axis=1)
#
#     df_Portfolio1['Excess Maturity greater than 6 Years'] = df_Portfolio1.apply(
#         lambda x: excessHG(df_Portfolio1[df_Portfolio1['Qualifies HE'] == 'Yes'], x['Loan Limit HF'], x['Max HD'],
#                            x['Revised Value HC']), axis=1)
#
#     df_Portfolio1['Revised Value HH'] = df_Portfolio1.apply(
#         lambda x: revisedValueHH(x['Revised Value HC'], x['Excess Maturity greater than 6 Years']), axis=1)
#
#     # Max HI
#     # =IFERROR('Concentration Limits'!$J$55,0)
#     try:
#         df_Portfolio1['Max HI'] = df_ExcessConcentration1['Applicable Test Limit'].loc[18]
#     except:
#         df_Portfolio1['Max HI'] = 0
#
#     df_Portfolio1['Qualifies HJ'] = df_Portfolio1.apply(lambda x: qualifiesHJ(x['Gambling Industry?']), axis=1)
#
#     df_Portfolio1['Loan Limit HK'] = df_Portfolio1.apply(
#         lambda x: loanLimitHK(df_Portfolio1[df_Portfolio1['Qualifies HJ'] == 'Yes'], x['Qualifies HE'],
#                               x['Revised Value HH']), axis=1)
#
#     df_Portfolio1['Excess Gambling Industries'] = df_Portfolio1.apply(
#         lambda x: excessHL(df_Portfolio1[df_Portfolio1['Qualifies HJ'] == 'Yes'], x['Loan Limit HK'], x['Max HI'],
#                            x['Revised Value HH']), axis=1)
#
#     df_Portfolio1['Revised Value HM'] = df_Portfolio1.apply(
#         lambda x: revisedValueHM(x['Revised Value HH'], x['Excess Gambling Industries']), axis=1)
#
#     # Max HN
#     # =IFERROR('Concentration Limits'!$J$56,0)
#     try:
#         df_Portfolio1['Max HN'] = df_ExcessConcentration1['Applicable Test Limit'].loc[19]
#     except:
#         df_Portfolio1['Max HN'] = 0
#
#     df_Portfolio1['Qualifies HO'] = df_Portfolio1.apply(lambda x: qualifiesHO(x['Loan Type']), axis=1)
#
#     df_Portfolio1['Loan Limit HP'] = df_Portfolio1.apply(
#         lambda x: loanLimitHP(df_Portfolio1[df_Portfolio1['Qualifies HO'] == 'Yes'], x['Qualifies HO'],
#                               x['Revised Value HM']), axis=1)
#
#     df_Portfolio1['Excess Recurring Revenue Loans'] = df_Portfolio1.apply(
#         lambda x: excessHQ(df_Portfolio1[df_Portfolio1['Qualifies HO'] == 'Yes'], x['Loan Limit HP'], x['Max HN'],
#                            x['Revised Value HM']), axis=1)
#
#     df_ExcessConcentration1.loc[0, 'Excess Concentration Amount'] = df_Portfolio1[
#         'Excess EBITDA not in top 3'].sum()
#     df_ExcessConcentration1.loc[1, 'Excess Concentration Amount'] = df_Portfolio1['Excess Largest Obligor'].sum()
#     df_ExcessConcentration1.loc[2, 'Excess Concentration Amount'] = df_Portfolio1['Other Excess'].sum()
#     df_ExcessConcentration1.loc[3, 'Excess Concentration Amount'] = df_Portfolio1['Excess Largest Industry'].sum()
#     df_ExcessConcentration1.loc[4, 'Excess Concentration Amount'] = df_Portfolio1[
#         'Excess 2nd Largest Industry'].sum()
#     df_ExcessConcentration1.loc[5, 'Excess Concentration Amount'] = df_Portfolio1[
#         'Excess 3rd Largest Industry'].sum()
#     df_ExcessConcentration1.loc[6, 'Excess Concentration Amount'] = df_Portfolio1['Excess Other Industry'].sum()
#     df_ExcessConcentration1.loc[7, 'Excess Concentration Amount'] = df_Portfolio1['Excess EBITDA < 10MM'].sum()
#     df_ExcessConcentration1.loc[8, 'Excess Concentration Amount'] = df_Portfolio1['Excess DIP Loans'].sum()
#     df_ExcessConcentration1.loc[9, 'Excess Concentration Amount'] = df_Portfolio1['Excess Cov-Lite Loans'].sum()
#     df_ExcessConcentration1.loc[10, 'Excess Concentration Amount'] = df_Portfolio1[
#         'Excess Less than Qtrly Pay'].sum()
#     df_ExcessConcentration1.loc[11, 'Excess Concentration Amount'] = df_Portfolio1['Excess Foreign Currency'].sum()
#     df_ExcessConcentration1.loc[12, 'Excess Concentration Amount'] = df_Portfolio1['Excess Aprroved Country'].sum()
#     df_ExcessConcentration1.loc[13, 'Excess Concentration Amount'] = df_Portfolio1[
#         'Excess DDTL and Revolving Loans'].sum()
#     df_ExcessConcentration1.loc[14, 'Excess Concentration Amount'] = df_Portfolio1['Excess Tier 3 Obligors'].sum()
#     df_ExcessConcentration1.loc[15, 'Excess Concentration Amount'] = df_Portfolio1['Excess Second Lien'].sum()
#     df_ExcessConcentration1.loc[16, 'Excess Concentration Amount'] = df_Portfolio1[
#         'Excess First Lien Last Out'].sum()
#     df_ExcessConcentration1.loc[17, 'Excess Concentration Amount'] = df_Portfolio1[
#         'Excess Maturity greater than 6 Years'].sum()
#     df_ExcessConcentration1.loc[18, 'Excess Concentration Amount'] = df_Portfolio1[
#         'Excess Gambling Industries'].sum()
#     df_ExcessConcentration1.loc[19, 'Excess Concentration Amount'] = df_Portfolio1[
#         'Excess Recurring Revenue Loans'].sum()
#
#     # Total Excess Concentration Amount
#     Total_Excess_Concentration_Amount = df_ExcessConcentration1['Excess Concentration Amount'].sum()
#
#     global df_Excess
#     df_Excess = df_Portfolio1[
#         ['Excess EBITDA not in top 3', 'Excess Largest Obligor', 'Other Excess', 'Excess Largest Industry',
#          'Excess 2nd Largest Industry', 'Excess 3rd Largest Industry', 'Excess Other Industry',
#          'Excess EBITDA < 10MM',
#          'Excess DIP Loans', 'Excess Cov-Lite Loans', 'Excess Less than Qtrly Pay', 'Excess Foreign Currency',
#          'Excess Aprroved Country', 'Excess DDTL and Revolving Loans', 'Excess Tier 3 Obligors',
#          'Excess Second Lien',
#          'Excess First Lien Last Out', 'Excess Maturity greater than 6 Years', 'Excess Gambling Industries',
#          'Excess Recurring Revenue Loans']]
#
#     # graphvizOther = GraphvizOutput()
#     # graphvizOther.output_type = 'pdf'
#     # graphvizOther.output_file = 'RemainingValuesFlow.pdf'
#     #
#     # with PyCallGraph(output=graphvizOther):
#
#     # Par Value of Portfolio
#     Par_Value_of_Portfolio = df_Portfolio1['Borrower Outstanding Principal Balance'].sum()
#
#     # Minimum credit Enhancement
#     # =LARGE('Portfolio '!DZ:DZ,1)+LARGE('Portfolio '!DZ:DZ,2)+LARGE('Portfolio '!DZ:DZ,3)+LARGE('Portfolio '!DZ:DZ,4)+LARGE('Portfolio '!DZ:DZ,5)
#     Minimum_credit_enhancemnt = df_Portfolio1['Remove Dupes'].nlargest(1).iloc[-1] + \
#                                 df_Portfolio1['Remove Dupes'].nlargest(2).iloc[-1] + \
#                                 df_Portfolio1['Remove Dupes'].nlargest(3).iloc[-1] + \
#                                 df_Portfolio1['Remove Dupes'].nlargest(4).iloc[-1] + \
#                                 df_Portfolio1['Remove Dupes'].nlargest(5).iloc[-1]
#
#     df_Portfolio1['Borrower Unfunded Amount'] = df_Portfolio1.apply(
#         lambda x: borrowerUnfundedAmount(x['Borrower Outstanding Principal Balance'],
#                                          x['Borrower Facility Commitment']), axis=1)
#
#     # Unfunded Exposure Amount
#     # =SUMIF('Portfolio '!AQ:AQ,"yes",'Portfolio '!J:J)
#     Unfunded_exposure_amount = round(
#         df_Portfolio1[df_Portfolio1['Revolving / Delayed Funding?'] == 'Yes']['Borrower Unfunded Amount'].sum())
#
#     df_Portfolio1['Advance Rate'] = df_Portfolio1.apply(lambda x: advanceRate(
#         df_BorrowerOutstandings1[df_BorrowerOutstandings1['Loan Category'] == x['Advance Rate Definition']]),
#                                                         axis=1)
#     # Weighted Average Advance Rate for Unfunded Exposures
#     Weighted_Average_Advance_Rate_for_Unfunded_Exposures = \
#         df_Portfolio1.groupby('Revolving / Delayed Funding?').apply(
#             lambda x: sum(x['Borrower Unfunded Amount'] * x['Advance Rate']))['Yes'] / Unfunded_exposure_amount
#
#     Advance_Rate_Cap_Until_15_Loans_in_Effect = 'Yes' if Weighted_Average_Advance_Rate_for_Unfunded_Exposures < 0.15 else 'No'
#
#     # =IF(G158="Yes",G26,G157)
#     Advance_Rate_Applied = df_Availability1['Value'].iloc[
#         8] if Advance_Rate_Cap_Until_15_Loans_in_Effect == 'Yes' else Weighted_Average_Advance_Rate_for_Unfunded_Exposures
#
#     # =IF(SUMIF('Portfolio '!$AQ$10:$AQ$85,"yes",'Portfolio '!$J$10:$J$85)=0,0,SUMPRODUCT(--('Portfolio '!$AQ$10:$AQ$85="yes"),'Portfolio '!$J$10:$J$85,'Portfolio '!$T$10:$T$85)/SUMIF('Portfolio '!$AQ$10:$AQ$85,"yes",'Portfolio '!$J$10:$J$85))
#     # SUMIF('Portfolio '!$AQ$10:$AQ$85,"yes",'Portfolio '!$J$10:$J$85 = Unfunded_Exposure_Amount
#     # SUMPRODUCT(--('Portfolio '!$AQ$10:$AQ$85="yes"),'Portfolio '!$J$10:$J$85,'Portfolio '!$T$10:$T$85)/SUMIF('Portfolio '!$AQ$10:$AQ$85,"yes",'Portfolio '!$J$10:$J$85))
#     Weighted_Average_Applicable_Collateral_Value_for_Unfunded_Exposures = \
#         df_Portfolio1.groupby('Revolving / Delayed Funding?').apply(
#             lambda x: sum(x['Borrower Unfunded Amount'] * x['Assigned Value'])).iloc[1] / Unfunded_exposure_amount
#
#     # Unfunded Equity Exposure Amount =((1-G159)*G155)+((1-G161)*G159*G155)
#     Unfunded_Equity_Exposure_Amount = ((1 - Advance_Rate_Applied) * Unfunded_exposure_amount) + ((
#                                                                                                          1 - Weighted_Average_Applicable_Collateral_Value_for_Unfunded_Exposures) * Advance_Rate_Applied * Unfunded_exposure_amount)
#
#     # Foreign Currency Adjusted Borrowing Value
#     # =SUMIF('Portfolio '!AS11:AS522,"Yes",'Portfolio '!E11:E522)
#     Foreign_Currency_Adjusted_Borrowing_Value = df_Portfolio1[df_Portfolio1['Non-US Approved Country?'] == 'Yes'][
#         'Adjusted Borrowing Value'].sum()
#
#     Unhedged_Foreign_Currency = Foreign_Currency_Adjusted_Borrowing_Value - df_Availability1['Value'].iloc[4]
#
#     df_Portfolio1['Revised Value HR'] = df_Portfolio1.apply(
#         lambda x: revisedValueHR(x['Revised Value HM'], x['Excess Recurring Revenue Loans']), axis=1)
#
#     df_Portfolio1['First Lien'] = df_Portfolio1.apply(
#         lambda x: firstLien(x['First Lien Value'], x['Revised Value HR'], x['Second Lien Value']), axis=1)
#
#     df_Portfolio1['Reclassed Second HT'] = df_Portfolio1.apply(
#         lambda x: reclassedSecond(x['Second Lien Value'], x['Revised Value HR'], x['First Lien Value']), axis=1)
#
#     df_Portfolio1['Last Out HU'] = df_Portfolio1.apply(
#         lambda x: lastOut(x['Loan Type'], x['Revised Value HR'], x['FLLO Value'], x['Second Lien ValueAC']), axis=1)
#
#     df_Portfolio1['Reclassed Second HV'] = df_Portfolio1.apply(
#         lambda x: reclassedSecondHV(x['Loan Type'], x['Revised Value HR'], x['Second Lien ValueAC'],
#                                     x['FLLO Value']),
#         axis=1)
#
#     df_Portfolio1['Recurring Revenue HW'] = df_Portfolio1.apply(
#         lambda x: recurringRevenueHW(x['Loan Type'], x['Revised Value HR'], x['Recurring Revenue Value']), axis=1)
#
#     # Create a new column in Borrower Outstanding Dataframe
#     df_BorrowerOutstandings1['Base Borrowing Value'] = np.nan
#
#     # =SUMIF('Portfolio '!$C$11:$C$522, 'Concentration Limits'!D5, 'Portfolio '!$HS$11:$HS$522)
#     # Base Borrowing Value in Borrower Outstanidings
#     df_BorrowerOutstandings1['Base Borrowing Value'].iloc[0] = \
#         df_Portfolio1[
#             df_Portfolio1['Advance Rate Definition'] == df_BorrowerOutstandings1['Loan Category'].iloc[0]][
#             'First Lien'].sum()
#
#     # =SUMIF('Portfolio '!$C$11:$C$522, 'Concentration Limits'!D5, 'Portfolio '!$HS$11:$HS$522)
#     # Base Borrowing Value in Borrower Outstanidings
#     df_BorrowerOutstandings1['Base Borrowing Value'].iloc[0] = \
#         df_Portfolio1[
#             df_Portfolio1['Advance Rate Definition'] == df_BorrowerOutstandings1['Loan Category'].iloc[0]][
#             'First Lien'].sum()
#
#     # =SUMIF('Portfolio '!$C$11:$C$522, 'Concentration Limits'!D5, 'Portfolio '!$HT$11:$HT$522)
#     # Base Borrowing Value in Borrower Outstanidings
#     df_BorrowerOutstandings1['Base Borrowing Value'].iloc[1] = \
#         df_Portfolio1[
#             df_Portfolio1['Advance Rate Definition'] == df_BorrowerOutstandings1['Loan Category'].iloc[0]][
#             'Reclassed Second HT'].sum()
#
#     # =SUMIF('Portfolio '!$C$11:$C$522, 'Concentration Limits'!D8, 'Portfolio '!$HS$11:$HS$522)
#     # Base Borrowing Value in Borrower Outstanidings
#     df_BorrowerOutstandings1['Base Borrowing Value'].iloc[3] = \
#         df_Portfolio1[
#             df_Portfolio1['Advance Rate Definition'] == df_BorrowerOutstandings1['Loan Category'].iloc[3]][
#             'First Lien'].sum()
#
#     # =SUMIF('Portfolio '!$C$11:$C$522, 'Concentration Limits'!D8, 'Portfolio '!$HT$11:$HT$522)
#     # Base Borrowing Value in Borrower Outstanidings
#     df_BorrowerOutstandings1['Base Borrowing Value'].iloc[4] = \
#         df_Portfolio1[
#             df_Portfolio1['Advance Rate Definition'] == df_BorrowerOutstandings1['Loan Category'].iloc[3]][
#             'Reclassed Second HT'].sum()
#
#     # =SUMIF('Portfolio '!$C$11:$C$522, 'Concentration Limits'!D11, 'Portfolio '!$HS$11:$HS$522)
#     # Base Borrowing Value in Borrower Outstanidings
#     df_BorrowerOutstandings1['Base Borrowing Value'].iloc[6] = \
#         df_Portfolio1[
#             df_Portfolio1['Advance Rate Definition'] == df_BorrowerOutstandings1['Loan Category'].iloc[6]][
#             'First Lien'].sum()
#
#     # =SUMIF('Portfolio '!$C$11:$C$522, 'Concentration Limits'!D11, 'Portfolio '!$HT$11:$HT$522)
#     # Base Borrowing Value in Borrower Outstanidings
#     df_BorrowerOutstandings1['Base Borrowing Value'].iloc[7] = \
#         df_Portfolio1[
#             df_Portfolio1['Advance Rate Definition'] == df_BorrowerOutstandings1['Loan Category'].iloc[6]][
#             'Reclassed Second HT'].sum()
#
#     # =SUMIF('Portfolio '!$C$11:$C$522, 'Concentration Limits'!D14, 'Portfolio '!$HS$11:$HS$522)
#     # Base Borrowing Value in Borrower Outstanidings
#     df_BorrowerOutstandings1['Base Borrowing Value'].iloc[9] = \
#         df_Portfolio1[
#             df_Portfolio1['Advance Rate Definition'] == df_BorrowerOutstandings1['Loan Category'].iloc[9]][
#             'First Lien'].sum()
#
#     # =SUMIF('Portfolio '!$C$11:$C$522, 'Concentration Limits'!D14, 'Portfolio '!$HT$11:$HT$522)
#     # Base Borrowing Value in Borrower Outstanidings
#     df_BorrowerOutstandings1['Base Borrowing Value'].iloc[10] = \
#         df_Portfolio1[
#             df_Portfolio1['Advance Rate Definition'] == df_BorrowerOutstandings1['Loan Category'].iloc[9]][
#             'Reclassed Second HT'].sum()
#
#     # =SUMIF('Portfolio '!$C$11:$C$522, 'Concentration Limits'!D17, 'Portfolio '!$HU$11:$HU$522)
#     # Base Borrowing Value in Borrower Outstanidings
#     df_BorrowerOutstandings1['Base Borrowing Value'].iloc[12] = \
#         df_Portfolio1[
#             df_Portfolio1['Advance Rate Definition'] == df_BorrowerOutstandings1['Loan Category'].iloc[12]][
#             'Last Out HU'].sum()
#
#     # =SUMIF('Portfolio '!$C$11:$C$522, 'Concentration Limits'!D19, 'Portfolio '!$HV$11:$HV$522)
#     # Base Borrowing Value in Borrower Outstanidings
#     df_BorrowerOutstandings1['Base Borrowing Value'].iloc[14] = \
#         df_Portfolio1[
#             df_Portfolio1['Advance Rate Definition'] == df_BorrowerOutstandings1['Loan Category'].iloc[14]][
#             'Reclassed Second HV'].sum()
#
#     # =SUMIF('Portfolio '!$C$11:$C$522, 'Concentration Limits'!D1, 'Portfolio '!$HW$11:$HW$522)
#     # Base Borrowing Value in Borrower Outstanidings
#     df_BorrowerOutstandings1['Base Borrowing Value'].iloc[16] = \
#         df_Portfolio1[
#             df_Portfolio1['Advance Rate Definition'] == df_BorrowerOutstandings1['Loan Category'].iloc[16]][
#             'Recurring Revenue HW'].sum()
#
#     Total_Borrowing_Base = df_BorrowerOutstandings1['Base Borrowing Value'].sum()
#
#     df_BorrowerOutstandings1['Base Borrowing Percentage'] = df_BorrowerOutstandings1.apply(
#         lambda x: baseBorrowingPercentage(x['Base Borrowing Value'], Total_Borrowing_Base), axis=1)
#
#     Weighted_Average_Advance_Rate = (
#             df_BorrowerOutstandings1['Advance Rate'] * df_BorrowerOutstandings1['Base Borrowing Percentage']).sum()
#
#     Base_Borrowing_Percentage = df_BorrowerOutstandings1['Base Borrowing Percentage'].sum()
#
#     Approved_Country = 0.03 * Unhedged_Foreign_Currency
#
#     Borrowing_Base = (
#             Adjusted_Borrowing_Value_for_Eligible_Loans - Total_Excess_Concentration_Amount - Unhedged_Foreign_Currency)
#
#     # The sum of: (i) the product of (x) the Borrowing Base and (y) the weighted average Advance Rate, minus
#     # Aggregate Unfunded Exposure Equity Amount, plus (ii) Cash on deposit in  the principal collection subaccount.
#     b = ((Borrowing_Base * Weighted_Average_Advance_Rate) - Unfunded_Equity_Exposure_Amount +
#          df_Availability1['Value'].iloc[3] + df_Availability1['Value'].iloc[2])
#
#     # The Adjusted Borrowing Value of Eligible Loans minus the Minimum Credit Enhancement Amount plus
#     # the amount on deposit in the Principal Collection Account, minus the Aggregate Unfunded Exposure Equity Amount
#     c = (Adjusted_Borrowing_Value_for_Eligible_Loans - Minimum_credit_enhancemnt + df_Availability1['Value'].iloc[
#         2] - Unfunded_Equity_Exposure_Amount + df_Availability1['Value'].iloc[3]).round()
#
#     # Availability Amount
#     Availability_Amount = min(df_Availability1['Value'].iloc[1], b, c)
#
#     Effective_Advance_Rate = Availability_Amount / Par_Value_of_Portfolio
#
#     Effective_Debt_to_Equity = Effective_Advance_Rate / (1 - Effective_Advance_Rate)
#
#     Proforma_Advances_Outstanding = df_Availability1['Value'].iloc[5] - df_Availability1['Value'].iloc[6] + \
#                                     df_Availability1['Value'].iloc[7]
#
#     Availability_Less_Advances_Outstanding = Availability_Amount - Proforma_Advances_Outstanding
#
#     Maximum_Advance_Rate_Test = Availability_Amount >= Proforma_Advances_Outstanding
#
#     Facility_Utilization = Proforma_Advances_Outstanding / df_Availability1['Value'].iloc[1]
#
#     Actual_Advance_Rate = Proforma_Advances_Outstanding / Par_Value_of_Portfolio
#
#     AvailabilityDict = {
#         'Terms': ['Availability Amount', 'Effective Advance Rate', 'Effective Debt to Equity',
#                   'Par Value of Portfolio',
#                   'Adjusted Borrowing Value of Eligible Loans', 'Excess Concentraions', 'Approved Country Reserves',
#                   'Borrowing Base ',
#                   'Minimum Credit Enhancement', 'Unfunded Exposure Amount', 'Unfunded Equity Exposure Amount',
#                   'On Deposit in Unfunded Exposure Account', 'Foreign Currency Adjusted Borrowing Value',
#                   'Foreign Currency hedged by Borrower', 'Unhedged Foreign Currency',
#                   'Weighted Average Advance Rate',
#                   'Cash on deposit in principal collections account', 'Current Advances Outstanding',
#                   'Advance Repaid',
#                   'Advances Requested', 'Pro Forma Advances Outstanding', 'Availability LESS Advances Outstanding',
#                   'Maximum Advance Rate Test', 'Facility Utilization', 'Actual Advance Rate'],
#         'Values': [f"${int(Availability_Amount):,}", '{:.2f}%'.format(Effective_Advance_Rate * 100),
#                    '{:.2f}'.format(Effective_Debt_to_Equity), f"${int(Par_Value_of_Portfolio):,}",
#                    f"${int(Adjusted_Borrowing_Value_for_Eligible_Loans):,}",
#                    f"${int(Total_Excess_Concentration_Amount):,}", f"{Approved_Country}",
#                    f"${int(Borrowing_Base):,}", f"${int(Minimum_credit_enhancemnt):,}", f"${Unfunded_exposure_amount}",
#                    f"${int(Unfunded_Equity_Exposure_Amount):,}",
#                    f"${df_Availability1['Value'].iloc[3]:,}", f"{int(Foreign_Currency_Adjusted_Borrowing_Value)}",
#                    df_Availability1['Value'].iloc[4], f"{int(Unhedged_Foreign_Currency)}",
#                    '{:.2f}%'.format(Weighted_Average_Advance_Rate * 100),
#                    f"${int(df_Availability1['Value'].iloc[2]):,}", f"${df_Availability1['Value'].iloc[5]:,}",
#                    df_Availability1['Value'].iloc[6],
#                    f"${df_Availability1['Value'].iloc[7]:,}", f"${Proforma_Advances_Outstanding:,}",
#                    f"${int(Availability_Less_Advances_Outstanding):,}", Maximum_Advance_Rate_Test,
#                    '{:.2f}%'.format(Facility_Utilization * 100),
#                    '{:.2f}%'.format(Actual_Advance_Rate * 100)]}
#
#     df_Portfolio['Interest Coverage'] = df_Portfolio.apply(
#         lambda x: interest_coverage_fun(x["Initial Interest Coverage"], x['Borrower'], measurement_date, df_VAE),
#         axis=1)
#
#     df_VAE1['Net Senior Leverage'] = df_VAE1.apply(
#         lambda x: Net_Senior_Leverage_fun(x['Senior Debt'], x['Unrestricted Cash'], x['TTM EBITDA']), axis=1)
#
#     df_Portfolio['VAE Net Senior Leverage'] = df_Portfolio.apply(
#         lambda x: VAE_Net_Senior_Leverage_fun(x['Permitted Net Senior Leverage CE'], x['Borrower'], measurement_date,
#                                               df_VAE), axis=1)
#
#     df_Portfolio['Net Senior Leverage Ratio Test'] = df_Portfolio.apply(
#         lambda x: Net_Senior_Leverage_Ratio_Test_fun(x['Loan Type'], x['Permitted Net Senior Leverage'],
#                                                      x['VAE Net Senior Leverage']), axis=1)
#
#     df_Portfolio['Cash Interest Coverage Ratio Test'] = df_Portfolio.apply(
#         lambda x: Cash_Interest_Coverage_Ratio_Test_fun(x['Loan Type'], x['Current Interest Coverage'],
#                                                         x['Interest Coverage']), axis=1)
#
#     df_Portfolio['Permitted Net Total Leverage'] = df_Portfolio.apply(
#         lambda x: Permitted_Net_Total_Leverage_fun(x['Initial Total Debt'], x['Initial Unrestricted Cash'],
#                                                    x['Permitted TTM EBITDA']), axis=1)
#
#     df_VAE['Net Total Leverage'] = df_VAE.apply(
#         lambda x: Net_Total_Leverage_fun(x['Total Debt'], x['Unrestricted Cash'], x['TTM EBITDA']), axis=1)
#
#     df_Portfolio['VAE Net Total Leverage'] = df_Portfolio.apply(
#         lambda x: VAE_Net_Total_Leverage_fun(x['Permitted Net Total Leverage'], x['Borrower'], measurement_date,
#                                              df_VAE), axis=1)
#
#     df_Portfolio['Net Total Leverage Ratio Test'] = df_Portfolio.apply(
#         lambda x: Net_Total_Leverage_Ratio_Test_fun(x['Loan Type'], x['VAE Net Total Leverage'],
#                                                     x['Permitted Net Total Leverage']), axis=1)
#
#     df_Portfolio['Initial Multiple'] = df_Portfolio.apply(
#         lambda x: Initial_Multiple_fun(x['Loan Type'], x['Initial Total Debt'], x['Initial Recurring Revenue']), axis=1)
#
#     df_Portfolio['VAE Multiple'] = df_Portfolio.apply(
#         lambda x: VAE_Multiple_fun(x['Loan Type'], x['Borrower'], measurement_date, x['Initial Multiple'], df_VAE),
#         axis=1)
#
#     df_Portfolio['Recurring Revenue Multiple'] = df_Portfolio.apply(
#         lambda x: Recurring_Revenue_Multiple_fun(x['Loan Type'], x['Current Multiple'], x['VAE Multiple']), axis=1)
#
#     df_Portfolio['VAE Liquidity'] = df_Portfolio.apply(
#         lambda x: VAE_Liquidity_fun(x['Loan Type'], x['Borrower'], measurement_date, x['Initial Liquidity'], df_VAE),
#         axis=1)
#
#     df_Portfolio['Liquidity'] = df_Portfolio.apply(
#         lambda x: Liquidity_fun(x['Loan Type'], x['Current Liquidity'], x['VAE Liquidity']), axis=1)
#
#     df_Portfolio['VAE Trigger'] = df_Portfolio.apply(
#         lambda x: VAE_Trigger_fun(x['Cash Interest Coverage Ratio Test'],
#                                   x['Net Senior Leverage Ratio Test'], x['Net Total Leverage Ratio Test'],
#                                   x['Recurring Revenue Multiple'], x['Liquidity'],
#                                   x['Obligor Payment Default'], x['Default Rights/Remedies Exercised'],
#                                   x['Reduces/waives Principal'], x['Extends Maturity/Payment Date'],
#                                   x['Waives Interest'], x['Subordinates Loan'],
#                                   x['Releases Collateral/Lien'], x['Amends Covenants'],
#                                   x['Amends Permitted Lien or Indebtedness'], x['Insolvency Event'],
#                                   x['Failure to Deliver Financial Statements']), axis=1)
#
#     columns = {'Borrower': object, 'Event Type': object, 'Date of VAE Decision': str, 'Assigned Value': float,
#                'Interest Coverage': float, 'TTM EBITDA': float, 'Senior Debt': float, 'Unrestricted Cash': float,
#                'Total Debt': float, 'Liquidity': float}
#     df_newVAE = pd.DataFrame(columns=columns)
#     df_newVAE['Date of VAE Decision'] = df_newVAE['Date of VAE Decision'].astype('datetime64[ns]')
#
#     condition = df_Portfolio['VAE Trigger'] == 'Yes'
#     df_borrowers = df_Portfolio[condition]
#     df_borrowers = df_borrowers[['Borrower']]
#
#     global merged_df
#     merged_df = pd.merge(df_borrowers, df_newVAE, on='Borrower', how='left')
#
#     return pd.DataFrame(AvailabilityDict)
