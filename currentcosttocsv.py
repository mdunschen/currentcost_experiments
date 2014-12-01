import sys, os
import re
import time, datetime
import Pysolar

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
    lt0 = time.localtime(t0 - h0)
    lt1 = time.localtime(t0 - h1)
    if time.strftime("%Y/%m/%d", lt0) == time.strftime("%Y/%m/%d", lt1):
        return "%s - %s" % (time.strftime("%Y/%m/%d %H:%M:%S", lt0), time.strftime("%H:%M:%S", lt1))
    else:
        return "%s - %s" % (time.strftime("%Y/%m/%d %H:%M:%S", lt0), time.strftime("%Y/%m/%d %H:%M:%S", lt1))


def ConvertToCSV(cc, fn, fdate): 
    # history
    h = cc['msg']['hist']
    # time taken
    t0 = cc['msg']['time']

    # assume file has date...
    dateofdump = "%s %s" % (fdate, t0)

    print "h keys:", h.keys()

    u = h['units']
    #expecting data entries
    datakeys = [k for k in h.keys() if re.match('data*', k)]

    # should be 9 sets of data
    assert len(datakeys) == 10
    datakeys.sort()

    # normaize sun's altitude to longest day for this geolocation
    bNormalizeSun = True
    if bNormalizeSun:
        altmax = Pysolar.GetAltitude(lat, lon, datetime.datetime(2014, 6, 21, 12, 00)) # is 21st June the longest day equal to the highest altitude of the sun?

    # probably only interested in data for sensor 0
    sensors = ['0']
    values = [ ]
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
            values.append((clockrange, val, alt0, alt1))
    f = open(fn, "w")
    f.write("%s, %s, %s, %s\n" % ("Date", "Energy [%s]" % u, "Sun Altitude From",  "Sun Altitude To"))
    for rv in values:
        f.write("%s, %f, %f, %f\n" % rv)
    f.close()
    



if __name__ == "__main__":
    # open a file
    cc = eval(open(sys.argv[1]).read())
    fdate = time.strftime("%Y %m %d", time.localtime(os.path.getctime(sys.argv[1])))
    ConvertToCSV(cc, "%s.csv" % sys.argv[1], fdate)
