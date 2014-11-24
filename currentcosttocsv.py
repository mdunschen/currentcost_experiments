import sys
import re
def ConvertToCSV(cc, fn):
    # history
    h = cc['msg']['hist']
    # time taken
    t0 = cc['msg']['time']

    print "h keys:", h.keys()
    print t0

    u = h['units']
    #expecting data entries
    datakeys = [k for k in h.keys() if re.match('data*', k)]
    print datakeys

    # should be 9 sets of data
    assert len(datakeys) == 10
    datakeys.sort()

    # probably only interested in data for sensor 0
    sensors = ['0']

    for dk in datakeys:
        dset = h[dk]
        assert 'sensor' in dset, dset.keys()
        sid = dset['sensor']
        if sid not in sensors:
            continue
        hours = [hk for hk in dset if re.match("h([0-9][0-9][0-9])", hk)]
        hours.sort()
        values = [ ]
        for hh in hours:
            hrange = int(hh[1:])
            val = float(dset[hh])
            values.append((hrange, val))
    
        print "values = ", values



if __name__ == "__main__":
    # open a file
    cc = eval(open(sys.argv[1]).read())
    ConvertToCSV(cc, "%s.csv" % sys.argv[1])
