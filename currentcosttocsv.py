import sys, os
import re
import time

def ConvertToClock(tnow, hrange):
    # h="hours", 24="22 to 24 hrs ago"
    # tnow in seconds since the millenium
    t0 = time.mktime(time.strptime(tnow, "%Y %m %d %H:%M:%S"))
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
    print datakeys

    # should be 9 sets of data
    assert len(datakeys) == 10
    datakeys.sort()

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
            values.append((clockrange, val))
    f = open(fn, "w")
    f.write("%s, %s\n" % ("Date", "Energy [%s]" % u))
    for rv in values:
        f.write("%s, %f\n" % rv)
    f.close()
    



if __name__ == "__main__":
    # open a file
    cc = eval(open(sys.argv[1]).read())
    fdate = time.strftime("%Y %m %d", time.localtime(os.path.getctime(sys.argv[1])))
    ConvertToCSV(cc, "%s.csv" % sys.argv[1], fdate)
