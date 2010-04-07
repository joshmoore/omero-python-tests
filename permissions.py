#!/usr/bin/env python

"""
   Tests of the admin service

   Copyright 2008 Glencoe Software, Inc. All rights reserved.
   Use is subject to license terms supplied in LICENSE.txt

"""

import unittest
import test.integration.library as lib
import omero
from omero_model_PermissionsI import PermissionsI
from omero_model_ImageI import ImageI
from omero_model_DatasetI import DatasetI
from omero_model_TagAnnotationI import TagAnnotationI
from omero_model_ExperimenterI import ExperimenterI
from omero_model_ExperimenterGroupI import ExperimenterGroupI
from omero_model_GroupExperimenterMapI import GroupExperimenterMapI
from omero_model_DatasetImageLinkI import DatasetImageLinkI
from omero.rtypes import *

class TestAdmin(lib.ITest):

    def testLoginToPublicGroupTicket1940(self):
        # As root create a new group
        from uuid import uuid4
        uuid = str(uuid4())
        g = ExperimenterGroupI()
        g.name = rstring(uuid)
        g.details.permissions = PermissionsI("rwrwrw")
        gid = self.root.sf.getAdminService().createGroup(g)

        # As a regular user, login to that group
        rv = self.root.getPropertyMap()
        ec = self.client.sf.getAdminService().getEventContext()
        public_client = omero.client(rv)
        public_client.getImplicitContext().put("omero.group", uuid)
        sf = public_client.createSession(ec.userName, "foo")
        ec = sf.getAdminService().getEventContext()
        self.assertEquals(uuid, ec.groupName)

        # But can the user write anything?
        tag = TagAnnotationI()
        sf.getUpdateService().saveObject(tag)
        # And link?
        # And edit? cF. READ-ONLY & READ-LINK

    def testCreatAndUpdatePrivateGroup(self):
        # this is the test of creating private group and updating it
        # including changes in #1434
        uuid = self.root.sf.getAdminService().getEventContext().sessionUuid
        query = self.root.sf.getQueryService()
        update = self.root.sf.getUpdateService()
        admin = self.root.sf.getAdminService()

        #create group1
        new_gr1 = ExperimenterGroupI()
        new_gr1.name = rstring("group1_%s" % uuid)
        p = PermissionsI()
        p.setUserRead(True)
        p.setUserWrite(True)
        p.setGroupRead(False)
        p.setGroupWrite(False)
        p.setWorldRead(False)
        p.setWorldWrite(False)
        new_gr1.details.permissions = p
        g1_id = admin.createGroup(new_gr1)
        
        # update name of group1
        gr1 = admin.getGroup(g1_id)
        self.assertEquals('rw----', str(gr1.details.permissions))
        new_name = "changed_name_group1_%s" % uuid
        gr1.name = rstring(new_name)
        admin.updateGroup(gr1)
        gr1_u = admin.getGroup(g1_id)
        self.assertEquals(new_name, gr1_u.name.val)
    
    def testCreatAndUpdatePublicGroupReadOnly(self):
        # this is the test of creating public group read-only and updating it
        # including changes in #1434
        uuid = self.root.sf.getAdminService().getEventContext().sessionUuid
        query = self.root.sf.getQueryService()
        update = self.root.sf.getUpdateService()
        admin = self.root.sf.getAdminService()

        #create group1
        new_gr1 = ExperimenterGroupI()
        new_gr1.name = rstring("group1_%s" % uuid)
        p = PermissionsI()
        p.setUserRead(True)
        p.setUserWrite(True)
        p.setGroupRead(True)
        p.setGroupWrite(False)
        p.setWorldRead(False)
        p.setWorldWrite(False)
        new_gr1.details.permissions = p
        g1_id = admin.createGroup(new_gr1)
        
        # update name of group1
        gr1 = admin.getGroup(g1_id)
        self.assertEquals('rwr---', str(gr1.details.permissions))
        new_name = "changed_name_group1_%s" % uuid
        gr1.name = rstring(new_name)
        admin.updateGroup(gr1)
        gr1_u = admin.getGroup(g1_id)
        self.assertEquals(new_name, gr1_u.name.val)
        
    def testCreatAndUpdatePublicGroup(self):
        # this is the test of creating public group and updating it
        # including changes in #1434
        uuid = self.root.sf.getAdminService().getEventContext().sessionUuid
        query = self.root.sf.getQueryService()
        update = self.root.sf.getUpdateService()
        admin = self.root.sf.getAdminService()

        #create group1
        new_gr1 = ExperimenterGroupI()
        new_gr1.name = rstring("group1_%s" % uuid)
        p = PermissionsI()
        p.setUserRead(True)
        p.setUserWrite(True)
        p.setGroupRead(True)
        p.setGroupWrite(True)
        p.setWorldRead(False)
        p.setWorldWrite(False)
        new_gr1.details.permissions = p
        g1_id = admin.createGroup(new_gr1)
        
        # update name of group1
        gr1 = admin.getGroup(g1_id)
        self.assertEquals('rwrw--', str(gr1.details.permissions))
        new_name = "changed_name_group1_%s" % uuid
        gr1.name = rstring(new_name)
        admin.updateGroup(gr1)
        gr1_u = admin.getGroup(g1_id)
        self.assertEquals(new_name, gr1_u.name.val)

    def testCreatGroupAndchangePermissions(self):
        # this is the test of updating group permissions
        # including changes in #1434
        uuid = self.root.sf.getAdminService().getEventContext().sessionUuid
        query = self.root.sf.getQueryService()
        update = self.root.sf.getUpdateService()
        admin = self.root.sf.getAdminService()

        #create group1
        new_gr1 = ExperimenterGroupI()
        new_gr1.name = rstring("group1_%s" % uuid)
        p = PermissionsI()
        p.setUserRead(True)
        p.setUserWrite(True)
        p.setGroupRead(False)
        p.setGroupWrite(False)
        p.setWorldRead(False)
        p.setWorldWrite(False)
        new_gr1.details.permissions = p
        g1_id = admin.createGroup(new_gr1)
        
        #incrise permissions of group1 to rwr---
        gr1 = admin.getGroup(g1_id)
        p1 = PermissionsI()
        p1.setUserRead(True)
        p1.setUserWrite(True)
        p1.setGroupRead(True)
        p1.setGroupWrite(False)
        p1.setWorldRead(False)
        p1.setWorldWrite(False)
        admin.changePermissions(gr1, p1)
        gr2 = admin.getGroup(g1_id)
        self.assertEquals('rwr---', str(gr2.details.permissions)) 
        
        #incrise permissions of group1 to rwrw--
        p2 = PermissionsI()
        p2.setUserRead(True)
        p2.setUserWrite(True)
        p2.setGroupRead(True)
        p2.setGroupWrite(True)
        p2.setWorldRead(False)
        p2.setWorldWrite(False)
        admin.changePermissions(gr2, p2)
        gr3 = admin.getGroup(g1_id)
        self.assertEquals('rwrw--', str(gr3.details.permissions)) 
        
    def testGroupOwners(self):
        # this is the test of creating private group and updating it
        # including changes in #1434
        uuid = self.root.sf.getAdminService().getEventContext().sessionUuid
        query = self.root.sf.getQueryService()
        update = self.root.sf.getUpdateService()
        admin = self.root.sf.getAdminService()
        
        #create group1
        new_gr1 = ExperimenterGroupI()
        new_gr1.name = rstring("group1_%s" % uuid)
        p = PermissionsI()
        p.setUserRead(True)
        p.setUserWrite(True)
        p.setGroupRead(True)
        p.setGroupWrite(False)
        p.setWorldRead(False)
        p.setWorldWrite(False)
        new_gr1.details.permissions = p
        g1_id = admin.createGroup(new_gr1)
        gr1 = admin.getGroup(g1_id)
        
        #create user1
        new_exp1 = ExperimenterI()
        new_exp1.omeName = rstring("user1_%s" % uuid)
        new_exp1.firstName = rstring("New")
        new_exp1.lastName = rstring("Test")
        new_exp1.email = rstring("newtest@emaildomain.com")

        from uuid import uuid4
        uuid = str(uuid4())
        uuidGroup = ExperimenterGroupI()
        uuidGroup.name = rstring(uuid)
        uuidGroupId = admin.createGroup(uuidGroup)
        uuidGroup = ExperimenterGroupI(uuidGroupId, False)
        listOfGroups = list()
        listOfGroups.append(admin.lookupGroup("user"))
        eid1 = admin.createExperimenterWithPassword(new_exp1, rstring("ome"), uuidGroup, listOfGroups)
        exp1 = admin.getExperimenter(eid1)

        #set owner of the group (user is not a member of)
        admin.addGroupOwners(gr1, [exp1])
        # chech if is the leader
        leaderOfGroups = admin.getLeaderOfGroupIds(exp1)
        self.assertTrue(gr1.id.val in leaderOfGroups)

        # remove group owner
        admin.removeGroupOwners(gr1, [exp1])
        # chech if no longer is the leader
        leaderOfGroups = admin.getLeaderOfGroupIds(exp1)
        self.assertFalse(gr1.id.val in leaderOfGroups)

        '''
        Controller method shows how it is used in practice
        
        available = request.POST.getlist('available')
        owners = request.POST.getlist('owners')
        
        def setOwnersOfGroup(self, available, owners):
            # available - current list rest of the users
            # owners - current list of chosen users
            experimenters = admin.lookupExperimenters()
            old_owners = admin.containedOwners(gr1_id)
            old_available = list()
            for e in experimenters:
                flag = False
                for m in old_owners:
                    if e.id == m.id:
                        flag = True
                if not flag:
                    old_available.append(e)

            add_exps = list()
            rm_exps = list()
            for om in old_owners:
                for a in available:
                    if om.id == long(str(a)):
                        rm_exps.append(om._obj)
            for oa in old_available:
                for o in owners:
                    if oa.id == long(str(o)):
                        add_exps.append(oa._obj)

            #final save
            admin_serv.addGroupOwners(gr1, add_exps)
            admin_serv.removeGroupOwners(gr1, rm_exps)
        '''
        
        
if __name__ == '__main__':
    unittest.main()