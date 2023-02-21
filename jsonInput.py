import pandas
import json

Portfolio_df = pandas.read_excel('BaseData.xlsx', sheet_name='Portfolio')
VAE_df = pandas.read_excel('BaseData.xlsx', sheet_name='VAE')
Availability_df = pandas.read_excel('BaseData.xlsx', sheet_name='Availability')
Concentration_limit_Tiers_df = pandas.read_excel('BaseData.xlsx', sheet_name='Concentration limit Tiers')
Concentration_limit_EBITDA_df = pandas.read_excel('BaseData.xlsx', sheet_name='Concentration limit EBITDA')
Excess_Concentration_Values_df = pandas.read_excel('BaseData.xlsx', sheet_name='Excess Concentration Values')
Industries_df = pandas.read_excel('BaseData.xlsx', sheet_name='Industries')
Borrower_Outstandings_df = pandas.read_excel('BaseData.xlsx', sheet_name='Borrower Outstandings')

thisisjson1 = Portfolio_df.to_json(orient='records')
thisisjson2 = VAE_df.to_json(orient='records')
thisisjson3 = Availability_df.to_json(orient='records')
thisisjson4 = Concentration_limit_Tiers_df.to_json(orient='records')
thisisjson5 = Concentration_limit_EBITDA_df.to_json(orient='records')
thisisjson6 = Excess_Concentration_Values_df.to_json(orient='records')
thisisjson7 = Industries_df.to_json(orient='records')
thisisjson8 = Borrower_Outstandings_df.to_json(orient='records')

calculate_availability_dict ={}

calculate_availability_dict["Portfolio"] = json.loads(thisisjson1)
calculate_availability_dict["VAE"] = json.loads(thisisjson2)
calculate_availability_dict["Availability"] = json.loads(thisisjson3)
calculate_availability_dict["Concentration_limit_Tiers"] = json.loads(thisisjson4)
calculate_availability_dict["Concentration_limit_EBITDA"] = json.loads(thisisjson5)
calculate_availability_dict["Excess_Concentration_Values"] = json.loads(thisisjson6)
calculate_availability_dict["Industries"] = json.loads(thisisjson7)
calculate_availability_dict["Borrower_Outstandings"] = json.loads(thisisjson8)
calculate_availability_var = json.dumps(calculate_availability_dict)

print(calculate_availability_var)
# with open('data.json', 'w') as json_file:
#     json.dump(calculate_availability, json_file)