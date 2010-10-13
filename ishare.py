#!/usr/bin/env python

"""
   Integration test focused on the omero.api.IShare interface
   a running server.

   Copyright 2008 Glencoe Software, Inc. All rights reserved.
   Use is subject to license terms supplied in LICENSE.txt

"""
import unittest, time
import integration.library as lib
import omero
import omero_Constants_ice
from omero_model_PixelsI import PixelsI
from omero_model_ImageI import ImageI
from omero_model_DatasetI import DatasetI
from omero_model_ExperimenterI import ExperimenterI
from omero_model_ExperimenterGroupI import ExperimenterGroupI
from omero_model_GroupExperimenterMapI import GroupExperimenterMapI
from omero_model_DatasetImageLinkI import DatasetImageLinkI
from omero.rtypes import rtime, rlong, rstring, rlist

from integration.helpers import createTestImage
    
class TestIShare(lib.ITest):

    def testThatPermissionsAreDefaultPrivate(self):
        i = omero.model.ImageI()
        i.name = rstring("name")
        i.acquisitionDate = rtime(0)
        i = self.client.sf.getUpdateService().saveAndReturnObject(i)
        self.assert_( not i.details.permissions.isGroupRead() )
        self.assert_( not i.details.permissions.isGroupWrite() )
        self.assert_( not i.details.permissions.isWorldRead() )

    def testBasicUsage(self):
        share = self.client.sf.getShareService()
        update = self.client.sf.getUpdateService()
        admin = self.client.sf.getAdminService()

        test_user = self.new_user()
        # create share
        description = "my description"
        timeout = None
        objects = []
        experimenters = [test_user]
        guests = ["ident@emaildomain.com"]
        enabled = True
        self.share_id = share.createShare(description, timeout, objects,experimenters, guests, enabled)

        self.assertEquals(0, len(share.getContents(self.share_id)))

        d = omero.model.DatasetI()
        d.setName(rstring("d"))
        d = update.saveAndReturnObject(d)
        share.addObjects(self.share_id, [d])

        self.assert_(len(share.getContents(self.share_id)) == 1)

        ds = []
        for i in range(0,4):
            ds.append(omero.model.DatasetI())
            ds[i].setName(rstring("ds%i" % i))
        ds = update.saveAndReturnArray(ds)
        share.addObjects(self.share_id, ds)

        self.assert_(share.getContentSize(self.share_id) == 5)

        self.assert_(len(share.getAllUsers(self.share_id)) == 2)

        #check access by a member to see the content
        client_guest_read_only = omero.client()
        client_guest_read_only.createSession(test_user.omeName.val,"ome")

        #get dataset - not allowed
        query = client_guest_read_only.sf.getQueryService()
        try:
            query.find("Dataset",d.id.val)
        except Exception, x:
            pass

        share_read_only = client_guest_read_only.sf.getShareService()
        share_read_only.activate(self.share_id)
        content = share_read_only.getContents(self.share_id)
        self.assert_(share_read_only.getContentSize(self.share_id) == 5)

        #check access by a member to add comments
        client_guest = omero.client()
        client_guest.createSession(test_user.omeName.val,"ome")

        share_guest = client_guest.sf.getShareService()
        share_guest.addComment(self.share_id,"comment for share %i" % self.share_id)
        self.assertEquals(1,len(share_guest.getComments(self.share_id)))

        # get share key and join directly
        s = share.getShare(self.share_id)

        client_share = omero.client()
        client_share.createSession(s.uuid,s.uuid)
        share1 = client_share.sf.getShareService()
        self.assertEquals(1, len(share1.getOwnShares(True)))

## Removing test for 'guest' user. 
## This currently fails but there is some question
## as to whether we should have a guest user.
##
##        # guest looks in to the share
##        guest_email = "ident@emaildomain.com"
##        token =  s.uuid
##        client_share_guest = omero.client()
##        client_share_guest.createSession("guest","guest") # maybe there can be some verification of identity by (share_key, email) - both params could be sent to email
##
##        share2 = client_share_guest.sf.getShareService()
##        # Doesn't exist # share2.getAllGuestShares(guest_email)
##        # Doesn't exist # self.assert_(share2.getGuestShare(token) > 0)
##        share2.addComment(self.share_id,"guest comment for share %i" % self.share_id)
##        self.assertEquals(1,len(share2.getComments(self.share_id)))

    def test1154(self):
        uuid = self.root.sf.getAdminService().getEventContext().sessionUuid

        
        ### create two users in one group
        user1 = self.new_user()
        user2 = self.new_user()
        
        ## login as user1 
        client_share1 = omero.client()
        client_share1.createSession(user1.omeName.val,"ome")
        share1 = client_share1.sf.getShareService()
        update1 = client_share1.sf.getUpdateService()
        
        # create image
        img = ImageI()
        img.setName(rstring('test1154-img-%s' % (uuid)))
        img.setAcquisitionDate(rtime(0))
        img = update1.saveAndReturnObject(img)
        img.unload()
        
        # create share
        description = "my description"
        timeout = None
        objects = [img]
        experimenters = [user2]
        guests = []
        enabled = True
        sid = share1.createShare(description, timeout, objects,experimenters, guests, enabled)
        
        self.assertEquals(1,len(share1.getContents(sid)))
        
        ## login as user2
        client_share2 = omero.client()
        client_share2.createSession(user2.omeName.val,"ome")
        share2 = client_share2.sf.getShareService()
        query2 = client_share2.sf.getQueryService()
        
        content = share2.getContents(sid)
        self.assertEquals(1,len(share2.getContents(sid)))
        
        # get shared image when share is activated
        share2.activate(sid)

        p = omero.sys.Parameters()
        p.map = {}
        p.map["ids"] = rlist([rlong(img.id.val)])
        sql = "select im from Image im where im.id in (:ids) order by im.name"
        res = query2.findAllByQuery(sql, p)
        self.assertEquals(1,len(res))
        for e in res:
            self.assert_(e.id.val == img.id.val)

    def test1157(self):
        uuid = self.root.sf.getAdminService().getEventContext().sessionUuid
        share = self.root.sf.getShareService()
        
        ### create two users in one group
        user1 = self.new_user()
        user2 = self.new_user()
        
        ## login as user1 
        client_share1 = omero.client()
        client_share1.createSession(user1.omeName.val,"ome")
        share1 = client_share1.sf.getShareService()
        update1 = client_share1.sf.getUpdateService()
        
        # create image
        img = ImageI()
        img.setName(rstring('test1154-img-%s' % (uuid)))
        img.setAcquisitionDate(rtime(0))
        img = update1.saveAndReturnObject(img)
        img.unload()
        
        # create share
        description = "my description"
        timeout = None
        objects = [img]
        experimenters = [user2]
        guests = []
        enabled = True
        sid = share1.createShare(description, timeout, objects,experimenters, guests, enabled)
        self.assert_(len(share1.getContents(sid)) == 1)
        # add comment by the owner
        share.addComment(sid, 'test comment by the owner %s' % (uuid))
        
        ## login as user2
        client_share2 = omero.client()
        client_share2.createSession(user2.omeName.val,"ome")
        share2 = client_share2.sf.getShareService()
        query2 = client_share2.sf.getQueryService()
        
        # add comment by the member
        share2.addComment(sid, 'test comment by the member %s' % (uuid))

        # Don't have to activate share2

        #get comments
        # by user1
        c1 = len(share.getComments(sid))
        self.assertEquals(2,c1)
        # by user2
        c2 = len(share2.getComments(sid))
        self.assertEquals(2,c2)

    def test1172(self):
        uuid = self.root.sf.getAdminService().getEventContext().sessionUuid
        share = self.root.sf.getShareService()
        query = self.root.sf.getQueryService()
        update = self.root.sf.getUpdateService()
        
        ### create user
        user1 = self.new_user()
        
        #create dataset with image
        #dataset with image
        ds = omero.model.DatasetI()
        ds.setName(rstring("dataset-%s" % (uuid)))
        ds = update.saveAndReturnObject(ds)
        ds.unload()
        
        # create image
        img = ImageI()
        img.setName(rstring('test-img in dataset-%s' % (uuid)))
        img.setAcquisitionDate(rtime(0))
        img = update.saveAndReturnObject(img)
        img.unload()
        
        dil = DatasetImageLinkI()
        dil.setParent(ds)
        dil.setChild(img)
        dil = update.saveAndReturnObject(dil)
        dil.unload()
        
        # create share by root
        items = list()
        ms = list()
        
        p = omero.sys.Parameters()
        p.map = {}
        p.map["oid"] = ds.id
        sql = "select ds from Dataset ds join fetch ds.details.owner join fetch ds.details.group " \
              "left outer join fetch ds.imageLinks dil left outer join fetch dil.child i " \
              "where ds.id=:oid"
        items.extend(query.findAllByQuery(sql, p))
        self.assertEquals(1, len(items))
        
        #members
        p.map["eid"] = rlong(user1.id.val)
        sql = "select e from Experimenter e where e.id =:eid order by e.omeName"
        ms = query.findAllByQuery(sql, p)
        sid = share.createShare(("test-share-%s" % uuid), rtime(long(time.time()*1000 + 86400)) , items, ms, [], True)
        
        # USER RETRIEVAL
        ## login as user1
        client_share1 = omero.client()
        client_share1.createSession(user1.omeName.val,"ome")
        share1 = client_share1.sf.getShareService()
        query1 = client_share1.sf.getQueryService()
        cntar1 = client_share1.sf.getContainerService()
        
        content = share1.getContents(sid)
        # Content now contains just the dataset with nothing loaded
        self.assertEquals(1, len(content))

        # get shared dataset and image when share is activated
        share1.activate(sid)

        #retrieve dataset
        p = omero.sys.Parameters()
        p.map = {}
        p.map["ids"] = rlist([ds.id])
        sql = "select ds from Dataset ds join fetch ds.details.owner join fetch ds.details.group " \
              "left outer join fetch ds.imageLinks dil left outer join fetch dil.child i " \
              "where ds.id in (:ids) order by ds.name"
        try:
            res1 = query1.findAllByQuery(sql, p)
            self.fail("This should throw an exception")
        except:
            pass

        #
        # Now we add all the other elements to the share to prevent
        # the security violation
        #
        # Not working imgs = cntar.getImages("Dataset",[ds.id.val], None)
        img = query.findByQuery("select i from Image i join fetch i.datasetLinks dil join dil.parent d where d.id = %s " % ds.id.val, None)
        self.assert_(img)
        share.addObject(sid, img)
        share.addObjects(sid, img.copyDatasetLinks())
        self.assertEquals(3, len(share.getContents(sid)))

        #
        # And try again to load them
        #
        share1.activate(sid)
        res1 = query1.findAllByQuery(sql, p)
        self.assert_(len(res1) == 1)
        for e in res1:
            self.assert_(e.id.val == ds.id.val)

        # retrieve only image
        p = omero.sys.Parameters()
        p.map = {}
        p.map["oid"] = rlong(img.id)
        sql = "select im from Image im " \
              "where im.id=:oid order by im.name"
        res2 = query1.findByQuery(sql, p)
        self.assert_(res2.id.val == img.id.val)

    def test1179(self):
        try:
            createTestImage(self.root.sf)
            rdefs = self.root.sf.getQueryService().findAll("RenderingDef", None)
            if len(rdefs) == 0:
                raise "Must have at least one rendering def"
            share = self.root.sf.getShareService()
            sid = share.createShare("", None, [], [], [], True)
            share.activate(sid)
            tb = self.root.sf.createThumbnailStore()
            try:
                tb.setPixelsId(rdefs[0].pixels.id.val)
            except omero.SecurityViolation:
                self.fail("Pixels was not in share")
        except omero.ValidationException, ve:
            print " test1179 - createTestImage has failed. This fixture method needs to be fixed."

    def test1201(self):
        uuid = self.root.sf.getAdminService().getEventContext().sessionUuid
        share = self.client.sf.getShareService()
        update = self.root.sf.getUpdateService()
        admin = self.root.sf.getAdminService()
        
        ### create two users in one group
        user1 = self.new_user()
        ## login as user1
        client_share1 = omero.client()
        client_share1.createSession(user1.omeName.val,"ome")
        share1 = client_share1.sf.getShareService()

        test_user = self.new_user()
        # create share
        description = "my description"
        timeout = None
        objects = []
        experimenters = [test_user]
        guests = ["ident@emaildomain.com"]
        enabled = True
        sid = share1.createShare(description, timeout, objects,experimenters, guests, enabled)

        #re - login as user1

        client_share2 = omero.client()
        client_share2.createSession(user1.omeName.val,"ome")
        share2 = client_share2.sf.getShareService()

        new_description = "new description"
        share1.setDescription(sid, new_description)
        try:
            self.assertEquals(share2.getShare(sid).message.val, new_description)
        except omero.ValidationException, ve:
            pass # This user can't see the share

        self.assertEquals(share1.getShare(sid).message.val, new_description)

        expiration = long(time.time()*1000)+86400
        share1.setExpiration(sid, rtime(expiration))
        self.assertEquals((share1.getShare(sid).started.val+share1.getShare(sid).timeToLive.val), expiration)

        share1.setActive(sid, False)
        self.assert_(share1.getShare(sid).active.val == False)

        owned = share1.getOwnShares(False)
        self.assertEquals(1, len(owned))

    def test1201b(self):
        share = self.client.sf.getShareService()
        # create share
        description = "my description"
        timeout = None
        objects = []
        experimenters = []
        guests = ["ident@emaildomain.com"]
        enabled = True
        sid = share.createShare(description, timeout, objects,experimenters, guests, enabled)

        self.assert_(share.getShare(sid).active.val == True)
        share.setActive(sid, False)
        self.assert_(share.getShare(sid).active.val == False)
        owned = share.getOwnShares(False)
        self.assertEquals(1, len(owned))

    def test1207(self):

        ### create two users in one group
        new_gr1 = self.new_group()
        client_share1, new_exp = self.new_client_and_user(new_gr1)
        client_share3, new_exp3 = self.new_client_and_user(new_gr1)

        share1 = client_share1.sf.getShareService()
        share3 = client_share3.sf.getShareService()

        test_user = self.new_user()

        # create share
        description = "my description"
        timeout = None
        objects = []
        experimenters = [test_user]
        guests = ["ident@emaildomain.com"]
        enabled = True
        sid = share1.createShare(description, timeout, objects, experimenters, guests, enabled)

        res = None
        try:
            share = share3.getShare(sid)
            self.fail("Share returned to non-member")
        except:
            pass

    def test1227(self):
        share = self.client.sf.getShareService()
        update = self.client.sf.getUpdateService()
        admin = self.client.sf.getAdminService()

        test_user = self.new_user()
        # create share
        description = "my description"
        timeout = None
        objects = []
        experimenters = [test_user]
        guests = ["ident@emaildomain.com"]
        enabled = True
        self.share_id = share.createShare(description, timeout, objects,experimenters, guests, enabled)
        
        share.addComment(self.share_id,"comment for share %i" % self.share_id)
        self.assertEquals(1,len(share.getComments(self.share_id)))
        
        self.assertEquals(1,share.getCommentCount([self.share_id])[self.share_id])
        
        # create second share
        description = "my second description"
        timeout = None
        objects = []
        experimenters = [test_user]
        guests = ["ident@emaildomain.com"]
        enabled = True
        self.share_id2 = share.createShare(description, timeout, objects,experimenters, guests, enabled)
        
        self.assertEquals(0,share.getCommentCount([self.share_id, self.share_id2])[self.share_id2])
        share.addComment(self.share_id2,"comment for share %i" % self.share_id2)
        self.assertEquals(1,share.getCommentCount([self.share_id, self.share_id2])[self.share_id2])

    def test2327(self):

        ### create two users in two groups
        client_share1, user1 = self.new_client_and_user()
        client_share2, user2 = self.new_client_and_user()

        ## login as user1
        share1 = client_share1.sf.getShareService()
        update1 = client_share1.sf.getUpdateService()

        # create image
        img = ImageI()
        img.setName(rstring('test2327'))
        img.setAcquisitionDate(rtime(0))
        img = update1.saveAndReturnObject(img)
        img.unload()

        # create share
        description = "my description"
        timeout = None
        objects = [img]
        experimenters = [user2]
        guests = []
        enabled = True
        sid = share1.createShare(description, timeout, objects, experimenters, guests, enabled)
        self.assert_(len(share1.getContents(sid)) == 1)
        # add comment by the owner
        share1.addComment(sid, 'test comment by the owner %s' % user1.id.val)

        ## login as user2
        share2 = client_share2.sf.getShareService()
        query2 = client_share2.sf.getQueryService()

        l = share2.getMemberShares(False)
        self.assertEquals(1, len(l))

        # add comment by the member
        share2.addComment(sid, 'test comment by the member %s' % (user2.id.val))

        # Don't have to activate share2

        #get comments
        # by user1
        c1 = len(share1.getComments(sid))
        self.assertEquals(2, c1)
        # by user2
        c2 = len(share2.getComments(sid))
        self.assertEquals(2, c2)

    def test2733(self):
        ### create two users in two groups
        client_share1, user1 = self.new_client_and_user()
        client_share2, user2 = self.new_client_and_user()

        ## login as user1
        share1 = client_share1.sf.getShareService()
        update1 = client_share1.sf.getUpdateService()

        # create image
        img = ImageI()
        img.setName(rstring('test2327'))
        img.setAcquisitionDate(rtime(0))
        img = update1.saveAndReturnObject(img)
        img.unload()

        # create share
        description = "my description"
        timeout = None
        objects = [img]
        experimenters = [user2]
        guests = []
        enabled = True
        sid = share1.createShare(description, timeout, objects, experimenters, guests, enabled)

        share2 = client_share2.sf.getShareService()
        share = share2.getShare(sid)

if __name__ == '__main__':
    unittest.main()
