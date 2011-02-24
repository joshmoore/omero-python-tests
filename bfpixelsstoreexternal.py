#!/usr/bin/env python

"""
   Integration test focused on the BfPixelsStore API
   
   This test compares data got through BFPixelsStore and
   RawPixelsStore on the same image file.
   
   Copyright 2011 Glencoe Software, Inc. All rights reserved.
   Use is subject to license terms supplied in LICENSE.txt

"""
import unittest, time, shutil, hashlib, difflib, binascii
import library as lib
import omero, omero.gateway
from omero.rtypes import *
from path import path

class TestBfPixelsStore(lib.ITest):
    
    def setUpTestFile(self, name):
        filename = self.OmeroPy / ".." / ".." / ".." / "components" / "common" / "test" / name
        tmp_dir = self.uuid()
        repo_filename = path("/OMERO") / tmp_dir / name
        # Copy file into repository subdirectory
        path.mkdir(path("/OMERO") / tmp_dir)
        shutil.copyfile(filename, repo_filename)
        # Import the same file
        self.pix_id = long(self.import_image(filename)[0])
        # Get the raw pixels store on the imported file.
        self.rp = self.client.sf.createRawPixelsStore()
        self.rp.setPixelsId(self.pix_id, True)
        # This code will deprecated on API unification.
        gateway = self.client.sf.createGateway()
        pixels = gateway.getPixels(self.pix_id)
        self.sizeX = pixels.getSizeX().getValue()
        self.sizeY = pixels.getSizeY().getValue()
        self.sizeZ = pixels.getSizeZ().getValue()
        self.sizeC = pixels.getSizeC().getValue()
        self.sizeT = pixels.getSizeT().getValue()
        # Get repository and the bf pixels store on the copied file
        repoMap = self.root.sf.sharedResources().repositories()
        repoPrx = repoMap.proxies[1] # THIS IS NOT SAFE NEED TO GET "/OMERO" repo.
        self.bf = repoPrx.pixels(repo_filename)

    def tidyUp(self):
        #self.bf_rps.close()
        self.rp.close()
        
    
    # Rather than have one import per test or do a better workaround
    # for now just lump all the tests together.
    def offtestBMP(self):
        self.setUpTestFile("test.bmp")
        self.allTests()
        self.tidyUp()
        
    def testDV(self):
        self.setUpTestFile("tinyTest.d3d.dv")
        self.allTests()
        self.tidyUp()
        
    def offtestJPG(self):
        self.setUpTestFile("test.jpg")
        self.allTests()
        self.tidyUp()
        
    def allTests(self):
        self.xtestOtherGetters()
        self.xtestGetRow()
        self.xtestGetCol()
        self.xtestGetPlane()
        self.xtestGetStack()
        self.xtestGetTimepoint()
        self.xtestGetHypercube()
    
    # In this test below the middlish hypercube is got.
    # The rps method is not implemented so extract the cube manually.
    def xtestGetHypercube(self):
        x1 = self.sizeX/3; x2 = (2*self.sizeX)/3 + 1 - x1
        y1 = self.sizeY/3; y2 = (2*self.sizeY)/3 + 1 - y1
        z1 = self.sizeZ/3; z2 = (2*self.sizeZ)/3 + 1 - z1
        c1 = self.sizeC/3; c2 = (2*self.sizeC)/3 + 1 - c1
        t1 = self.sizeT/3; t2 = (2*self.sizeT)/3 + 1 - t1
        
        bf_data = self.bf.getHypercube([x1,y1,z1,c1,t1],[x2,y2,z2,c2,t2],[1,1,1,1,1])
        rp_data = self.getSolidHypercubeFromRPS([x1,y1,z1,c1,t1],[x2,y2,z2,c2,t2],[1,1,1,1,1])
        self.assert_(len(rp_data) == len(bf_data))
        bf_md5 = hashlib.md5(bf_data)
        rp_md5 = hashlib.md5(rp_data)
        self.assert_(bf_md5.digest() == rp_md5.digest())
        
        bf_data = self.bf.getHypercube([x1,y1,z1,c1,t1],[x2,y2,z2,c2,t2],[2,2,1,1,1])
        rp_data = self.getHypercubeFromRPS([x1,y1,z1,c1,t1],[x2,y2,z2,c2,t2],[2,2,1,1,1])
        self.assert_(len(rp_data) == len(bf_data))
        bf_md5 = hashlib.md5(bf_data)
        rp_md5 = hashlib.md5(rp_data)
        self.assert_(bf_md5.digest() == rp_md5.digest())

        bf_data = self.bf.getHypercube([x1,y1,z1,c1,t1],[x2,y2,z2,c2,t2],[6,5,4,3,2])
        rp_data = self.getHypercubeFromRPS([x1,y1,z1,c1,t1],[x2,y2,z2,c2,t2],[6,5,4,3,2])
        self.assert_(len(rp_data) == len(bf_data))
        bf_md5 = hashlib.md5(bf_data)
        rp_md5 = hashlib.md5(rp_data)
        self.assert_(bf_md5.digest() == rp_md5.digest())

    def getSolidHypercubeFromRPS(self,start,size,step):
        bw = self.rp.getByteWidth()
        data = ""
        for t in range(start[4],start[4]+size[4],step[4]):
            for c in range(start[3],start[3]+size[3],step[3]):
                for z in range(start[2],start[2]+size[2],step[2]):
                    for y in range(start[1],start[1]+size[1],step[1]):
                        offset = self.rp.getRowOffset(y,z,c,t)
                        data += self.rp.getRegion(size[0]*bw,start[0]*bw+offset)
        return data
 
    def getHypercubeFromRPS(self,start,size,step):
        bw = self.rp.getByteWidth()
        data = ""
        for t in range(start[4],start[4]+size[4],step[4]):
            for c in range(start[3],start[3]+size[3],step[3]):
                for z in range(start[2],start[2]+size[2],step[2]):
                    for y in range(start[1],start[1]+size[1],step[1]):
                        offset = self.rp.getRowOffset(y,z,c,t)
                        for x in range(start[0],start[0]+size[0],step[0]):
                            data += self.rp.getRegion(bw,x*bw+offset)
        return data
 
       
    # In the tests below the middling element is got.
    def xtestGetRow(self):
        bf_size = self.bf.getRowSize()
        rp_size = self.rp.getRowSize()
        self.assert_(bf_size == rp_size)

        y = self.sizeY/2
        z = self.sizeZ/2
        c = self.sizeC/2
        t = self.sizeT/2
        bf_data = self.bf.getRow(y,z,c,t)
        rp_data = self.rp.getRow(y,z,c,t)
        self.assert_(bf_size == len(bf_data))

        bf_md5 = hashlib.md5(bf_data)
        rp_md5 = hashlib.md5(rp_data)
        self.assert_(bf_md5.digest() == rp_md5.digest())

    def xtestGetCol(self):
        bf_size = self.bf.getByteWidth()*self.bf.getPlaneSize()/self.bf.getRowSize()
        rp_size = self.rp.getByteWidth()*self.rp.getPlaneSize()/self.rp.getRowSize()
        self.assert_(bf_size == rp_size)

        x = self.sizeX/2
        z = self.sizeZ/2
        c = self.sizeC/2
        t = self.sizeT/2
        bf_data = self.bf.getCol(x,z,c,t)
        rp_data = self.rp.getCol(x,z,c,t)
        self.assert_(bf_size == len(bf_data))
        
        bf_md5 = hashlib.md5(bf_data)
        rp_md5 = hashlib.md5(rp_data)
        self.assert_(bf_md5.digest() == rp_md5.digest())
    
    def xtestGetPlane(self):
        bf_size = self.bf.getPlaneSize()
        rp_size = self.rp.getPlaneSize()
        self.assert_(bf_size == rp_size)
        
        z = self.sizeZ/2
        c = self.sizeC/2
        t = self.sizeT/2
        bf_data = self.bf.getPlane(z,c,t)
        rp_data = self.rp.getPlane(z,c,t)
        self.assert_(bf_size == len(bf_data))
        
        bf_md5 = hashlib.md5(bf_data)
        rp_md5 = hashlib.md5(rp_data)
        self.assert_(bf_md5.digest() == rp_md5.digest())
    
    def xtestGetStack(self):
        bf_size = self.bf.getStackSize()
        rp_size = self.rp.getStackSize()
        self.assert_(bf_size == rp_size)
        
        c = self.sizeC/2
        t = self.sizeT/2
        bf_data = self.bf.getStack(c,t)
        rp_data = self.rp.getStack(c,t)
        self.assert_(bf_size == len(bf_data))
        
        bf_md5 = hashlib.md5(bf_data)
        rp_md5 = hashlib.md5(rp_data)
        self.assert_(bf_md5.digest() == rp_md5.digest())
    
    def xtestGetTimepoint(self):
        bf_size = self.bf.getTimepointSize()
        rp_size = self.rp.getTimepointSize()
        self.assert_(bf_size == rp_size)
        
        t = self.sizeT/2
        bf_data = self.bf.getTimepoint(t)
        rp_data = self.rp.getTimepoint(t)
        self.assert_(bf_size == len(bf_data))
        
        bf_md5 = hashlib.md5(bf_data)
        rp_md5 = hashlib.md5(rp_data)
        self.assert_(bf_md5.digest() == rp_md5.digest())
    
    def xtestOtherGetters(self):
        bf_size = self.bf.getTotalSize()
        rp_size = self.rp.getTotalSize()
        self.assert_(bf_size == rp_size)
        
        bf_width = self.bf.getByteWidth()
        rp_width = self.rp.getByteWidth()
        self.assert_(bf_width == rp_width)
        
        bf_offset = self.bf.getRowOffset(0,0,0,0)
        self.assert_(bf_offset == 0)
        bf_offset = self.bf.getPlaneOffset(0,0,0)
        self.assert_(bf_offset == 0)
        bf_offset = self.bf.getStackOffset(0,0)
        self.assert_(bf_offset == 0)
        bf_offset = self.bf.getTimepointOffset(0)
        self.assert_(bf_offset == 0)
        
        y = self.sizeY/2
        z = self.sizeZ/2
        c = self.sizeC/2
        t = self.sizeT/2
        bf_offset = self.bf.getRowOffset(y,z,c,t)
        rp_offset = self.rp.getRowOffset(y,z,c,t)
        self.assert_(bf_offset == rp_offset)
        
        bf_offset = self.bf.getPlaneOffset(z,c,t)
        rp_offset = self.rp.getPlaneOffset(z,c,t)
        self.assert_(bf_offset == rp_offset)
        
        bf_offset = self.bf.getStackOffset(c,t)
        rp_offset = self.rp.getStackOffset(c,t)
        self.assert_(bf_offset == rp_offset)
        
        bf_offset = self.bf.getTimepointOffset(t)
        rp_offset = self.rp.getTimepointOffset(t)
        self.assert_(bf_offset == rp_offset)

if __name__ == '__main__':
    unittest.main()
