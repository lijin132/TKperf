'''
Created on 07.08.2012

@author: gschoenb
'''
import perfTest.SsdTest as ssd
import perfTest.HddTest as hdd
from reports.XmlReport import XmlReport
from reports.RstReport import RstReport
import plots.genPlots as pgp

class PerfTest(object):
    '''
    A performance test, consists of multiple Device Tests
    '''
    
    def __init__(self,testname,filename,baseDir):
        '''
        A performance test has several reports and plots.
        '''
        
        ## The output file for the fio job test results.
        self.__testname = testname
        
        ## The data file for the test, can be a whole device also.
        self.__filename = filename
        
        ## Base directory to write results to.
        self.__baseDir = baseDir
        if self.__baseDir != '':
            if self.__baseDir[-1] != '/':
                self.__baseDir += '/'
            
        ## Xml file to write test results to
        self.__xmlReport = XmlReport(testname)
        
        ## Rst file to generate pdf of
        self.__rstReport = RstReport(self.__testname)
        
        ## Dictionary of tests to carry out
        self.__tests = {}

    def getTestname(self):
        return self.__testname
    
    def getFilename(self):
        return self.__filename
    
    def getTests(self):
        return self.__tests
    
    def addTest(self,key,test):
        self.__tests[key] = test
    
    def resetTests(self):
        self.__tests.clear()
    
    def runTests(self):
        for test in self.__tests:
            test.run()
    
    def getXmlReport(self):
        return self.__xmlReport
    
    def getRstReport(self):
        return self.__rstReport
    
    def getBaseDir(self):
        return self.__baseDir
    
    def setBaseDir(self):
        for test in self.__tests:
            test.setBaseDir(self.__baseDir)
    
    def toXml(self):
        '''
        Calls for every test in the test dictionary the toXMl method
        and writes the results to the xml file.
        '''
        tests = self.getTests()
        e = self.getXmlReport().getXml()
        
        #call the xml function for every test in the dictionary
        for k,v in tests.iteritems():
            e.append(v.toXml(k))
        
        self.getXmlReport().xmlToFile(self.getTestname())

class SsdPerfTest(PerfTest):
    '''
    A performance test for ssds consists of all ssd tests
    '''
    
    ## Keys valid for test dictionary and xml file
    testKeys = ['iops','lat','tp','writesat','iod']
    
    def __init__(self,testname,filename,baseDir,nj,iod):
        PerfTest.__init__(self, testname, filename, baseDir)
        
        ## Number of jobs for fio.
        self.__nj = nj
        
        ## Number of iodepth for fio.
        self.__iod = iod
        
        #Add every test to the performance test
        test = ssd.IopsTest(testname,filename,nj,iod)
        self.addTest(SsdPerfTest.testKeys[0], test)
        test = ssd.LatencyTest(testname,filename,nj,iod)
        self.addTest(SsdPerfTest.testKeys[1], test)
        test = ssd.TPTest(testname,filename,nj,iod)
        self.addTest(SsdPerfTest.testKeys[2], test)
        test = ssd.WriteSatTest(testname,filename,nj,iod)
        self.addTest(SsdPerfTest.testKeys[3], test)
        test = ssd.IodTest(testname,filename,nj,iod)
        self.addTest(SsdPerfTest.testKeys[4], test)
        
        if self.getBaseDir() != '':
            self.setBaseDir()
        
    def run(self):
        self.runTests()
        self.toXml()
        self.getPlots()
        self.toRst()
        
    def fromXml(self):
        '''
        Reads out the xml file name 'testname.xml' and initializes the test
        specified with xml. The valid tags are "iops,lat,tp,writesat,iod", but
        there don't must be every tag in the file.
        Afterwards the plotting and rst methods for the specified tests are
        called.
        '''
        self.getXmlReport().fileToXml(self.getTestname())
        self.resetTests()
        root = self.getXmlReport().getXml()
        for tag in SsdPerfTest.testKeys:
            for elem in root.iterfind(tag):
                test = None
                if elem.tag == 'iops':
                    test = ssd.IopsTest(self.getTestname(),self.getFilename,self.__nj,self.__iod)
                if elem.tag == 'lat':
                    test = ssd.LatencyTest(self.getTestname(),self.getFilename,self.__nj,self.__iod)
                if elem.tag == 'tp':
                    test = ssd.TPTest(self.getTestname(),self.getFilename,self.__nj,self.__iod)
                if elem.tag == 'writesat':
                    test = ssd.WriteSatTest(self.getTestname(),self.getFilename,self.__nj,self.__iod)
                if elem.tag == 'iod':
                    test = ssd.IodTest(self.getTestname(),self.getFilename,self.__nj,self.__iod)
                if test != None:
                    test.fromXml(elem)
                    self.addTest(tag, test)

        self.getPlots()
        self.toRst()
    
    def toRst(self):
        tests = self.getTests()
        rst = self.getRstReport()
        rst.addTitle()
        rst.addSetupInfo(tests['iops'].getFioJob().__str__())
        rst.addChapter("IOPS")
        rst.addFigure(tests['iops'].getFigure())
        rst.toRstFile()
        
    def getPlots(self):
        tests = self.getTests()
        #plots for iops
        pgp.stdyStVerPlt(tests['iops'],"IOPS")
        pgp.stdyStConvPlt(tests['iops'],"IOPS")
        pgp.mes2DPlt(tests['iops'],"IOPS")
        #plots for latency
        pgp.stdyStVerPlt(tests['lat'],"LAT")
        pgp.stdyStConvPlt(tests['lat'],"LAT")
        pgp.mes2DPlt(tests['lat'],"avg-LAT")
        pgp.mes2DPlt(tests['lat'],"max-LAT")
        #plots for throughout
        pgp.stdyStVerPlt(tests['tp'],"TP")
        pgp.tpStdyStConvPlt(tests['tp'], "read","ssd")
        pgp.tpStdyStConvPlt(tests['tp'], "write","ssd")
        pgp.tpMes2DPlt(tests['tp'])
        #plots for write saturation
        pgp.writeSatIOPSPlt(tests['writesat'])
        pgp.writeSatLatPlt(tests['writesat'])
        #plots for io depth        
        pgp.ioDepthMes3DPlt(tests['iod'],"read")
        pgp.ioDepthMes3DPlt(tests['iod'],"write")
        pgp.ioDepthMes3DPlt(tests['iod'],"randread")
        pgp.ioDepthMes3DPlt(tests['iod'],"randwrite")

class HddPerfTest(PerfTest):
    '''
    A performance test for hdds consists of all hdd
    '''
    
    ## Keys valid for test dictionary and xml file
    testKeys = ['iops','tp']
    
    def __init__(self,testname,filename,baseDir,iod):
        PerfTest.__init__(self, testname, filename, baseDir)
        
        ## Number of iodepth for fio.
        self.__iod = iod
        
        test = hdd.IopsTest(testname,filename,iod)
        self.addTest(HddPerfTest.testKeys[0],test)
        test = hdd.TPTest(testname,filename,iod)
        self.addTest(HddPerfTest.testKeys[1],test)
        
        if self.getBaseDir() != '':
            self.setBaseDir()
    
    def run(self):
        self.runTests()
    
    def fromXml(self):
        '''
        Reads out the xml file name 'testname.xml' and initializes the test
        specified with xml. The valid tags are "iops,tp", but
        there don't must be every tag in the file.
        Afterwards the plotting and rst methods for the specified tests are
        called.
        '''
        self.getXmlReport().fileToXml(self.getTestname())
        self.resetTests()
        root = self.getXmlReport().getXml()
        for tag in HddPerfTest.testKeys:
            for elem in root.iterfind(tag):
                test = None
                if elem.tag == 'iops':
                    test = hdd.IopsTest(self.getTestname(),self.getFilename,self.__nj,self.__iod)
                if elem.tag == 'tp':
                    test = hdd.TPTest(self.getTestname(),self.getFilename,self.__nj,self.__iod)
                if test != None:
                    test.fromXml(elem)
                    self.addTest(tag, test)

        self.getPlots()
        self.toRst()
    
    def toRst(self):
        tests = self.getTests()
        rst = self.getRstReport()
        rst.addTitle()
        rst.addSetupInfo(tests['iops'].getFioJob().__str__())
        rst.addChapter("IOPS")
        rst.addFigure(tests['iops'].getFigure())
        rst.toRstFile()
        
    def getPlots(self):
        tests = self.getTests()
        pgp.IOPSplot(tests['iops'])
        pgp.tpStdyStConvPlt(tests['tp'], "rw","hdd")

        