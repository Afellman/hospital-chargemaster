#!/usr/bin/env python

import os
from glob import glob
import json
import pandas
import datetime

here = os.path.dirname(os.path.abspath(__file__))
folder = os.path.basename(here)
latest = '%s/latest' % here
year = datetime.datetime.today().year
output_data = os.path.join(here, 'data-latest.tsv')
output_year = os.path.join(here, 'data-%s.tsv' % year)

# Don't continue if we don't have latest folder
if not os.path.exists(latest):
    print('%s does not have parsed data.' % folder)
    sys.exit(0)

# Don't continue if we don't have results.json
results_json = os.path.join(latest, 'records.json')
if not os.path.exists(results_json):
    print('%s does not have results.json' % folder)
    sys.exit(1)

with open(results_json, 'r') as filey:
    results = json.loads(filey.read())

columns = ['charge_code', 
           'price', 
           'description', 
           'hospital_id', 
           'filename', 
           'charge_type']

df = pandas.DataFrame(columns=columns)

# First parse standard charges (doesn't have DRG header)
for result in results:
    filename = os.path.join(latest, result['filename'])
    if not os.path.exists(filename):
        print('%s is not found in latest folder.' % filename)
        continue

    if os.stat(filename).st_size == 0:
        print('%s is empty, skipping.' % filename)
        continue

    # Facility', 'DRG', 'DRG Description', 'Average Covered Charges
    if filename.endswith('csv'):
        content = pandas.read_csv(filename)

    charge_type = 'standard'
    if "DRG" in filename:
        charge_type = 'drg'

    # We need to combine Facility, DRG, 
    print("Parsing %s" % filename)

    # Important! This file also has (some) Medicare charge per case
    # Update by row
    if charge_type == "drg":

        # ['DRG_Long_Desc', 'Average_Charge_Per_Case', 'Average_Medicare_Payment_Per_Case']
        for row in content.iterrows():
            idx = df.shape[0] + 1
            charge_code = row[1]['DRG_Long_Desc'].split('-')[0].strip()
            entry = [charge_code,                                      # charge code
                     row[1]['Average_Charge_Per_Case'],         # price
                     row[1]['DRG_Long_Desc'],                   # description
                     result['hospital_id'],
                     result['filename'], 
                     charge_type]
            df.loc[idx,:] = entry

    else:

        # ['Procedure ID', 'Description', 'Amount']
        for row in content.iterrows():
            idx = df.shape[0] + 1
            entry = [row[1]['Procedure ID'],                    # charge code
                     row[1].Amount,                             # price
                     row[1].Description,                        # description
                     result['hospital_id'],
                     result['filename'], 
                     charge_type]
            df.loc[idx,:] = entry


# Remove empty rows
df = df.dropna(how='all')

# Save data!
print(df.shape)
df.to_csv(output_data, sep='\t', index=False)
df.to_csv(output_year, sep='\t', index=False)
