import sys, os
import re
import time, datetime
import Pysolar

import bokeh.plotting as plot
from bokeh.plotting import ColumnDataSource
from bokeh.charts import TimeSeries
from bokeh.objects import HoverTool
from bokeh.resources import CDN
from bokeh.embed import components

lat, lon = 53.373242,-2.86108 # Liverpool

def Getdatetime(t):
    return datetime.datetime.utcfromtimestamp(t)

def GetAsSeconds(tnow, bDropMinutes=True):
    if bDropMinutes:
        t0 = time.mktime(time.strptime(tnow[:-6], "%Y %m %d %H"))
    else:
        t0 = time.mktime(time.strptime(tnowi, "%Y %m %d %H:%M:%S"))
    return t0
    

def GetSunAltitudes(ts):
    altitudes = [ ]
    for t in ts:
        dt = Getdatetime(t)
        alt = Pysolar.GetAltitude(lat, lon, dt)
        altitudes.append(alt)
    return altitudes


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
    t0 = GetAsSeconds(dateofdump)    
    print "dateofdump = ", dateofdump

    u = h['units']
    #expecting data entries
    datakeys = sorted([k for k in h.keys() if re.match('data*', k)])    
    assert len(datakeys) == 10 # should be 10 sets of data

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
        days = [hk for hk in dset if re.match("d([0-9][0-9][0-9])", hk)]
        days.sort(reverse=True)
        if days:
            print "days = ", days
        for hh in hours:
            # h="hours", 24="22 to 24 hrs ago"
            hp2 = int(hh[1:])
            lt0 = datetime.datetime.fromtimestamp(t0 - hp2 * 3600)
            lt1 = datetime.datetime.fromtimestamp(t0 - (hp2 - 2) * 3600)
            print "lt0, lt1 = ", lt0, lt1
            val = float(dset[hh])
            altitudes = GetSunAltitudes([t0 - hp2 * 3600, t0 - (hp2 - 2) * 3600])
            alt0 = altitudes[0]
            alt1 = altitudes[1]
            if bNormalizeSun:
                alt0 = alt0 / altmax
                alt1 = alt1 / altmax
            if (lt0, lt1) in values:
                assert values[(lt0, lt1)] == (val, alt0, alt1)
            else:
                values[(lt0, lt1)] = (val, alt0, alt1)
    

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


def PlotUsingBokeh(historylogs, fname, fdate):
    values = { }
    for hislog in historylogs:
        cc = eval(open(hislog, "r").read())
        addCCToValues(cc, values, fdate)
    skeys = sorted(values.keys())
    elec = [values[k][0] for k in skeys]

    altmax = Pysolar.GetAltitude(lat, lon, datetime.datetime(2014, 6, 21, 12, 00))
    alltimes = [ ]
    for s0, s1 in skeys:
        alltimes.append(s0)
        alltimes.append(s1)
    atf = ["%s-%s" % (t0.strftime("%Y/%m/%d(%a) %Hh"), t1.strftime("%Hh")) for t0, t1 in skeys]
    
    source = ColumnDataSource(data={'alltimesformatted':atf, 'elec': ["%.3fkWh" % e for e in elec], 'altitude': ["%.2f%% to %.3f%%" % (100.0 * Pysolar.GetAltitude(lat, lon, t0)/altmax, 100.0 * Pysolar.GetAltitude(lat, lon, t1)/altmax) for t0, t1 in skeys]})

    plot.output_file(fname)

    plot.figure(title="Electricity[kwh]", x_axis_type="datetime", xrange=[min([s[0] for s in skeys]), max([s[1] for s in skeys])], tools="hover,resize,pan,wheel_zoom,box_zoom,reset,previewsave")
    plot.hold()
    plot.quad(left=[s[0] for s in skeys], right=[s[1] for s in skeys], bottom=0.0, top=elec, source=source, line_color="#000000", fill_color="#ff00ff")
    plot.line(x=alltimes, y=[Pysolar.GetAltitude(lat, lon, t)/altmax for t in alltimes])
    p = plot.curplot()
    p.plot_width = 700
    
    hover = p.select(dict(type=HoverTool))
    hover.tooltips = {'Date & Time': '@alltimesformatted', 'Electricity': '@elec', 'Sun Altitude': '@altitude'}

    script, div = components(p, CDN)
    inum = 0
    fnh = "%s%03d_script.html" % (os.path.basename(fname), inum)
    fnj = "%s%03d_script.js" % (os.path.basename(fname), inum)
    while (os.path.isfile(fnh) or os.path.isfile(fnj)):
        inum += 1
        fnh = "%s%03d_script.js" % (os.path.basename(fname), inum)
        fnj = "%s%03d_script.js" % (os.path.basename(fname), inum)
        
    open(fnj, "w").write(script)
    open(fnh, "w").write(div)
    
    ft = open("test.html", "w")
    ft.write("<html>\n")
    ft.write('<script src="http://cdn.pydata.org/bokeh-0.6.1.min.js"></script>\n')    
    ft.write('<link rel="stylesheet" type="text/css" href="http://cdn.pydata.org/bokeh-0.6.1.min.css"></link>\n')
    nonconflictmode = 'jQuery(document).ready(function($)'
    ft.write('<script>\n%s%s\n' % (nonconflictmode, script[script.index('{'):]))
    ft.write('%s\n' % div)
    ft.write('</html>')
    ft.close()


    plot.show()




if __name__ == "__main__":
    if len(sys.argv) == 1:
        print "Usage: sys.argv[0] <output>.html|.csv"
        sys.exit(0)
    
    # read all history files (written by 'readcurrentcost.py') 
    hl = sorted([f for f in os.listdir('.') if re.match('history[0-9][0-9][0-9].log$', f)])
    assert hl
    fdate = time.strftime("%Y %m %d", time.localtime(os.stat(hl[-1]).st_atime)) # date the history was written
    fdate = "2014 12 20"
    print "fdate = ", fdate
    if len(sys.argv) > 1 and sys.argv[1][:-3] == 'csv':
        ConvertToCSV(hl, sys.argv[1], fdate)
    else:
        PlotUsingBokeh(hl, sys.argv[1], fdate)
