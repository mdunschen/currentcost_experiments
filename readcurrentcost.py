#
# CurrentCost parsing
#
#    Copyright (C) 2009  Dale Lane
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#  The author of this code can be contacted at Dale.Lane@gmail.com
#    Any contact about this application is warmly welcomed.
#

import os, sys
# need this to get data from the CurrentCost meter 
import serial

# parses the XML
from currentcostparser    import CurrentCostDataParser

# stubs for storing the CurrentCost data
from currentcostdatastore import CurrentCostDataStore


#
# canned data - lines of XML from CurrentCost meters
#  - use this instead of data from the serial port if you don't have a CC128
# 
#line = "<msg><date><dsb>00101</dsb><hr>20</hr><min>16</min><sec>58</sec></date><src><name>CC02</name><id>00077</id><type>1</type><sver>1.06</sver></src><ch1><watts>02350</watts></ch1><ch2><watts>00000</watts></ch2><ch3><watts>00000</watts></ch3><tmpr>13.4</tmpr></msg>"
#line = "<msg><date><dsb>00101</dsb><hr>19</hr><min>25</min><sec>48</sec></date><src><name>CC02</name><id>00077</id><type>1</type><sver>1.06</sver></src><ch1><watts>02247</watts></ch1><ch2><watts>00000</watts></ch2><ch3><watts>00000</watts></ch3><tmpr>13.3</tmpr><hist><hrs><h02>000.3</h02><h04>001.6</h04><h06>001.8</h06><h08>000.3</h08><h10>001.0</h10><h12>000.8</h12><h14>000.6</h14><h16>000.3</h16><h18>000.3</h18><h20>000.3</h20><h22>000.3</h22><h24>000.6</h24><h26>000.6</h26></hrs><days><d01>0013</d01><d02>0011</d02><d03>0014</d03><d04>0019</d04><d05>0009</d05><d06>0006</d06><d07>0014</d07><d08>0014</d08><d09>0013</d09><d10>0016</d10><d11>0011</d11><d12>0014</d12><d13>0008</d13><d14>0011</d14><d15>0013</d15><d16>0011</d16><d17>0012</d17><d18>0015</d18><d19>0014</d19><d20>0013</d20><d21>0016</d21><d22>0013</d22><d23>0010</d23><d24>0012</d24><d25>0022</d25><d26>0013</d26><d27>0011</d27><d28>0010</d28><d29>0011</d29><d30>0017</d30><d31>0012</d31></days><mths><m01>0382</m01><m02>0326</m02><m03>0374</m03><m04>0000</m04><m05>0000</m05><m06>0000</m06><m07>0000</m07><m08>0000</m08><m09>0000</m09><m10>0000</m10><m11>0000</m11><m12>0000</m12></mths><yrs><y1>0000000</y1><y2>0000000</y2><y3>0000000</y3><y4>0000000</y4></yrs></hist></msg>"
#line = "<msg><src>CC128-v0.09</src><dsb>00001</dsb><time>22:24:38</time><tmpr>21.8</tmpr><sensor>0</sensor><id>00952</id><type>1</type><ch1><watts>00445</watts></ch1></msg>"
#line = "<msg><src>CC128-v0.09</src><dsb>00001</dsb><time>22:29:57</time><hist><data><sensor>0</sensor><type>1</type><units>kwhr</units><h010>0.362</h010><h008>2.386</h008><h006>3.346</h006><h004>1.639</h004></data><data><sensor>1</sensor><type>1</type><units>kwhr</units><h010>0.000</h010><h008>0.000</h008><h006>0.000</h006><h004>0.000</h004></data><data><sensor>2</sensor><type>1</type><units>kwhr</units><h010>0.000</h010><h008>0.000</h008><h006>0.000</h006><h004>0.000</h004></data><data><sensor>3</sensor><type>1</type><units>kwhr</units><h010>0.000</h010><h008>0.000</h008><h006>0.000</h006><h004>0.000</h004></data><data><sensor>4</sensor><type>1</type><units>kwhr</units><h010>0.000</h010><h008>0.000</h008><h006>0.000</h006><h004>0.000</h004></data><data><sensor>5</sensor><type>1</type><units>kwhr</units><h010>0.000</h010><h008>0.000</h008><h006>0.000</h006><h004>0.000</h004></data><data><sensor>6</sensor><type>1</type><units>kwhr</units><h010>0.000</h010><h008>0.000</h008><h006>0.000</h006><h004>0.000</h004></data><data><sensor>7</sensor><type>1</type><units>kwhr</units><h010>0.000</h010><h008>0.000</h008><h006>0.000</h006><h004>0.000</h004></data><data><sensor>8</sensor><type>1</type><units>kwhr</units><h010>0.000</h010><h008>0.000</h008><h006>0.000</h006><h004>0.000</h004></data><data><sensor>9</sensor><type>1</type><units>kwhr</units><h010>0.000</h010><h008>0.000</h008><h006>0.000</h006><h004>0.000</h004></data></hist></msg>"

def SaveHistoryData(ccstruct):
    fn = "history%.3d.log"
    i = 0
    while os.path.isfile(fn % i):
        i += 1
    open(fn % i, "w").write("%s" % str(ccstruct))



def ReadCC(src, bmirror):
    # objects to parse and store the data
    ccdb_ch1 = CurrentCostDataStore()

    # create the parser class
    myparser = CurrentCostDataParser()

    fm = None
    if bmirror:
        i = 0
        fn = "mirrored%03d.data"
        while (os.path.isfile(fn % i)):
            i += 1
        fm = open(fn % i, "w")

    while True:
        # read a line of XML from the CurrentCost meter
        try:
	    line = src.readline()
        except EOFError:
            break
        if fm:
            fm.write(line)
        line = line.rstrip('\r\n')
        if not line:
            break
        if line[0] != '<':
            line = line[1:]
            assert line[0] == '<'

        # get a Python array representation of the XML
        currentcoststruct = myparser.parseCurrentCostXML(line)
        assert currentcoststruct
    
        # examine the reply and print some useful bits from it
        if 'msg' not in currentcoststruct:
            print 'Unknown message format'
        else:
            if 'src' in currentcoststruct['msg']:
                if 'sver' in currentcoststruct['msg']['src']:
                    print 'data from CurrentCost meter : version ' + currentcoststruct['msg']['src']['name'] + '-v' + currentcoststruct['msg']['src']['sver']
                else:
                    print 'data from CurrentCost meter : version ' + currentcoststruct['msg']['src']
            if 'hist' in currentcoststruct['msg']:
                print 'received history data'
                SaveHistoryData(currentcoststruct)
            if 'ch1' in currentcoststruct['msg']:
                print 'received update for channel 1'
            if 'ch2' in currentcoststruct['msg']:
                print 'received update for channel 2'
            if 'ch3' in currentcoststruct['msg']:
                print 'received update for channel 3'

        # store the CurrentCost data in the datastore
        myparser.storeTimedCurrentCostData(ccdb_ch1)
    

def ReadFromSerial():
    # connect to a CurrentCost meter
    ser = serial.Serial(port='/dev/ttyUSB0', 
                        baudrate=57600, 
                        bytesize=serial.EIGHTBITS,
                        parity=serial.PARITY_NONE, 
                        stopbits=serial.STOPBITS_ONE)
    ReadCC(ser, True)


def ReadFromMirror(fn):
    f = open(fn, "r")
    ReadCC(f, False)
    f.close()
    

if __name__ == "__main__":
    if len(sys.argv) > 1:
        assert os.path.isfile(sys.argv[1])
        ReadFromMirror(sys.argv[1])
    else:
        ReadFromSerial()
