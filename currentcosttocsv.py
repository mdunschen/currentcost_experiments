import sys, os
import re
import time, datetime
import Pysolar

import bokeh.plotting as plot
from bokeh.charts import TimeSeries

lat, lon = 53.373242,-2.86108

def Getdatetime(t):
    return datetime.datetime.utcfromtimestamp(t)

def GetAsSeconds(tnow):
    t0 = time.mktime(time.strptime(tnow, "%Y %m %d %H:%M:%S"))
    return t0
    

def GetSunAltitude(dateofdump, hrange):
    t0 = GetAsSeconds(dateofdump)
    h0 = (hrange - 0) * 3600
    h1 = (hrange - 1) * 3600
    dh0 = (t0 - h0)
    dh1 = (t0 - h1)
    dt0 = Getdatetime(dh0)
    dt1 = Getdatetime(dh1)

    alt0 = Pysolar.GetAltitude(lat, lon, dt0)
    alt1 = Pysolar.GetAltitude(lat, lon, dt1)
    return (alt0, alt1)


def ConvertToClock(tnow, hrange):
    # h="hours", 24="22 to 24 hrs ago"
    # tnow in seconds since the millenium
    t0 = GetAsSeconds(tnow)
    #print tnow, t0, hrange
    h0 = (hrange - 0) * 3600 # seconds
    h1 = (hrange - 2) * 3600 # seconds
    # same day?
    lt0 = datetime.datetime.fromtimestamp(t0 - h0)
    lt1 = datetime.datetime.fromtimestamp(t0 - h1)
    return (lt0, lt1)

def FormatTimeRange(timerange, bAddDay):
    lt0, lt1 = timerange
    #sameday = time.strftime("%Y/%m/%d", lt0) == time.strftime("%Y/%m/%d", lt1)
    sameday = (lt0.year, lt0.month, lt0.day) == (lt1.year, lt1.month, lt1.day)
    if bAddDay:
        return (sameday, "%s %s-%s" % (lt0.strftime("%Y/%m/%d"), lt0.strftime("%H"), lt1.strftime("%Hh")))
    else:
        return (sameday, "%s-%s" % (lt0.strftime("%H"), lt1.strftime("%Hh")))

def addCCToValues(cc, values, fdate):
    # history
    h = cc['msg']['hist']
    # time taken
    t0 = cc['msg']['time']

    # assume file has date...
    dateofdump = "%s %s" % (fdate, t0)

    u = h['units']
    #expecting data entries
    datakeys = [k for k in h.keys() if re.match('data*', k)]

    # should be 9 sets of data
    assert len(datakeys) == 10
    datakeys.sort()

    # probably only interested in data for sensor 0
    sensors = ['0']
    bNormalizeSun = True

    if bNormalizeSun:
        altmax = Pysolar.GetAltitude(lat, lon, datetime.datetime(2014, 6, 21, 12, 00))

    for dk in datakeys:
        dset = h[dk]
        assert 'sensor' in dset, dset.keys()
        sid = dset['sensor']
        if sid not in sensors:
            continue
        hours = [hk for hk in dset if re.match("h([0-9][0-9][0-9])", hk)]
        hours.sort(reverse=True)
        for hh in hours:
            hrange = int(hh[1:])
            clockrange = ConvertToClock(dateofdump, hrange)
            val = float(dset[hh])
            alt0, alt1 = GetSunAltitude(dateofdump, hrange)
            if bNormalizeSun:
                alt0 = alt0 / altmax
                alt1 = alt1 / altmax
            if clockrange in values:
                assert values[clockrange] == (val, alt0, alt1)
            else:
                values[clockrange] = (val, alt0, alt1)
    

def ConvertToCSV(historylogs, fn, fdate): 
    values = { }
    for hislog in historylogs:
        cc = eval(open(hislog, "r").read())
        addCCToValues(cc, values, fdate)

    f = open(fn, "w")
    f.write("%s, %s, %s, %s\n" % ("Date", "Energy [%s]" % 'kWh', "Sun Altitude From",  "Sun Altitude To"))
    skeys = sorted(values.keys())
    sd = True
    for sk in skeys:
        lsd, ts = FormatTimeRange(sk, sd)
        f.write("%s, %f, %f, %f\n" % ((ts,) + values[sk]))
        sd = not lsd
    f.close()


def PlotUsingBokeh(historylogs, fdate):
    values = { }
    for hislog in historylogs:
        cc = eval(open(hislog, "r").read())
        addCCToValues(cc, values, fdate)
    skeys = sorted(values.keys())
    elec = [values[k][0] for k in skeys]
    labels = [ ]
    sd = True
    for sk in skeys:
        lsd, ts = FormatTimeRange(sk, sd)
        labels.append(ts)
        sd = not lsd


    plot.output_file("elec.html", title="elec example")

    #plot.figure(title="Electricity[kwh]")
    ts = TimeSeries(skeys)
    plot.quad(left=[s[0] for s in skeys], right=[s[1] for s in skeys], bottom=0.0, top=elec)
    ts.show()




if __name__ == "__main__":
    # open a file
    hl = sorted([f for f in os.listdir('.') if re.match('history[0-9][0-9][0-9].log$', f)])
    assert hl
    fdate = time.strftime("%Y %m %d", time.localtime(os.path.getctime(hl[-1])))
    #ConvertToCSV(hl, "%s.csv" % hl[0], fdate)
    PlotUsingBokeh(hl, fdate)
