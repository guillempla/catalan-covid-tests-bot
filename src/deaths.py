import os
import pandas as pd
from sodapy import Socrata
from datetime import datetime, timedelta


class Deaths:

    def __init__(self, region):
        self.limit = 10000
        self.dataset_link = "analisi.transparenciacatalunya.cat"
        self.dataset_id = "uqk7-bf9s"
        self.region = region
        self.total_deaths = 0
        self.last_death = 'None'
        self.calculateInformation()

    # update deaths' dataset
    def updateDatabase(self):
        f = open("./text/last_update_deaths.txt").read().strip()
        last_update = datetime.strptime(f, "%Y-%m-%dT%H:%M:%S")
        if datetime.now()-last_update > timedelta(hours=8):
            f = open("./text/last_update_deaths.txt", "w")
            f.write((datetime.now()).strftime("%Y-%m-%dT%H:%M:%S"))
            f.close()
            print("updated")
            client = Socrata(self.dataset_link, None)
            data = client.get(self.dataset_id, limit=self.limit)
            df = pd.DataFrame.from_dict(data)
            # dataset contains extra characters on those counties finished with 'à'
            try:
                df['comarcadescripcio'] = df['comarcadescripcio'].str.replace(
                    "\xa0", "")
                df.to_pickle("./text/deaths_backup.pkl")
                return df
            except KeyError:
                df = pd.read_pickle("./text/deaths_backup.pkl")
                print("Malament")
                return df
        else:
            df = pd.read_pickle("./text/deaths_backup.pkl")
            return df

    def checkDataIntegrity(self, df):
        try:
            df['comarcadescripcio'] = df['comarcadescripcio'].str.replace(
                "\xa0", "")
        except KeyError:
            return False
        df_noguera = df.loc[df['comarcadescripcio'] == 'Noguera']
        df_jussa = df.loc[df['comarcadescripcio'] == 'Pallars Jussà']
        if len(df_noguera) < 15 or len(df_jussa) < 10:
            return False
        return True

    # converts date_string into a datetime object and returns the maximum date
    def updateMaxDate(self, date, date_string):
        date_string = date_string[:date_string.find('.')]
        if date == 'None':
            date = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S")
        else:
            aux_date = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S")
            if aux_date > date:
                date = aux_date
        return date

    # calculates the number of deaths for the region given
    def calculateInformation(self):
        df = self.updateDatabase()
        # they changed Aran's county name
        if self.region == "Aran":
            self.region = "Val d'Aran"
        df_region = df.loc[df['comarcadescripcio'] == self.region]

        if self.region == "CATALUNYA":
            df_region = df

        self.total_deaths = df_region['numexitus'].astype(int).sum()
        if (self.total_deaths > 0):
            self.last_death = df_region['exitusdata'].max()
            self.last_death = datetime.strptime(
                self.last_death[:self.last_death.find('.')], "%Y-%m-%dT%H:%M:%S")

        if self.last_death != 'None':
            self.last_death = self.last_death.strftime("%d/%m/%Y")
