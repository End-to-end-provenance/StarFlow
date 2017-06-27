import time, datetime
import pickle
import starflow.make_json_prov as JP
from urllib.request import urlopen
import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

days_to_plot = 30
rows_to_plot = days_to_plot * 96

metsta_url = "http://harvardforest.fas.harvard.edu/sites/harvardforest.fas.harvard.edu/files/weather/metsta.dat"
m101 = "m101.csv"
m102 = "m102.csv"

def split_logger_file(depends_on = metsta_url, creates = (m101, m102)):
    m101_file = open(m101, "w")
    m102_file = open(m102, "w")
    with urlopen(metsta_url) as response:
        for line in response:
            line = line.decode("utf-8")
            if line[0:3] == "101":
                m101_file.write(line)
            else:
                m102_file.write(line)
    m101_file.close()
    m102_file.close()

temp_outfile = 'air_temperature.png'
rad_outfile = 'solar_radiation.png'
wind_outfile = 'wind_speed.png'
prec_outfile = 'daily_precipitation.png'

def read_plot(depends_on = (m101, m102), creates = (temp_outfile, rad_outfile, wind_outfile, prec_outfile)):

    cols = ["table", "year", "jd", "time", "airt", "rh", "dewp", "prec", "slrr", "parr", "netr", "bar", "wspd", "wres", "wdir", "wdev", "gspd", "s10t"]
    qq_all = pd.read_csv(m101, names = cols)
    qq_all_rows = len(qq_all.index)

    cols = ["table", "year", "jd", "time", "airt", "airtmax", "airtmin", "rh", "rhmax", "rhmin", "dewp", "dewpmax", "dewpmin", "prec", "slrt", "part", "netr", "bar", "wspd", "wres", "wdir", "wdev", "gspd", "s10t", "s10tmax", "s10tmin", "bat", "prog"]
    dd_all = pd.read_csv(m102, names = cols)
    dd_all_rows = len(dd_all.index)

    qq = qq_all[(qq_all_rows - rows_to_plot) : qq_all_rows]
    dd = dd_all[(dd_all_rows - days_to_plot) : dd_all_rows]

    qq_datetime = pd.to_datetime(qq.year, format='%Y') + pd.to_timedelta(qq.jd - 1, unit='d') + pd.to_timedelta(qq.time // 100, unit='h') + pd.to_timedelta(qq.time % 100, unit='m')
    dd_date = pd.to_datetime(dd.year, format='%Y') + pd.to_timedelta(dd.jd - 1, unit='d')

    qq_airt = qq['airt'].apply(lambda x: outliers(x, -50, 50))
    qq_dewp = qq['dewp'].apply(lambda x: outliers(x, -50, 50))
    qq_s10t = qq['s10t'].apply(lambda x: outliers(x, -50, 50))
    qq_slrr = qq['slrr'].apply(lambda x: outliers(x, 0, 1500))
    qq_netr = qq['netr'].apply(lambda x: outliers(x, -100, 1000))
    qq_wspd = qq['wspd'].apply(lambda x: outliers(x, 0, 100))
    qq_gspd = qq['gspd'].apply(lambda x: outliers(x, 0, 100))
    qq_prec = qq['prec'].apply(lambda x: outliers(x, 0, 1000))

    dd_prec = dd['prec'].apply(lambda x: outliers(x, 0, 1000))

    plt.plot(qq_datetime, qq_airt, color="blue")
    plt.plot(qq_datetime, qq_s10t, color="purple")
    plt.plot(qq_datetime, qq_dewp, color="gray")
    plt.title("Temperature & Humidity")
    plt.ylabel("Temperature (deg C)")
    plt.savefig(temp_outfile)
    plt.clf()

    plt.plot(qq_datetime, qq_slrr, color="blue")
    plt.plot(qq_datetime, qq_netr, color="gray")
    plt.title("Radiation")
    plt.ylabel("Radiation (W/m2)")
    plt.savefig(rad_outfile)
    plt.clf()

    plt.plot(qq_datetime, qq_wspd, color="blue")
    plt.plot(qq_datetime, qq_gspd, color="gray")
    plt.title("Wind Speed")
    plt.ylabel("Speed (m/sec)")
    plt.savefig(wind_outfile)
    plt.clf()

    plt.plot(qq_datetime, qq_prec, color="gray")
    plt.title("Precipitation")
    plt.ylabel("Precipitation (mm)")
    plt.savefig(precip_outfile)
    plt.clf()

def main():
    times_dict = {}
    functions = [split_logger_file, read_plot]
    for f in functions:
        f
        current = datetime.datetime.now()
        times_dict[f.__name__] = current.microsecond

    times_pickle = open("./results/test3.pickle", 'wb')
    pickle.dump(times_dict, times_pickle)

    times_pickle.close()

    FileList = ['./scripts/test3.py']
    pickle_location = "./results/test3.pickle"
    output_json_file = "./results/test3.json"

    JP.StarFlowLL_to_DDG(FileList, output_json_file, pickle_location)

if __name__ == "__main__":
    main()
