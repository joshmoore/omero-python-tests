#!/usr/bin/env python

"""
   Integration test suite. Please add a reference to your subpackage,
   module, or specific class here.

   This suite is called via `ant python-integration` (defined in
   tools/python.xml) and requires that a blitz server be running to
   perform properly.

   Copyright 2008 Glencoe Software, Inc. All rights reserved.
   Use is subject to license terms supplied in LICENSE.txt

"""

import logging
logging.basicConfig(level=logging.WARN)

import unittest
import xmlrunner

class TopLevel(unittest.TestCase):
    pass

def additional_tests():
    load = unittest.defaultTestLoader.loadTestsFromName
    suite = unittest.TestSuite()
    suite.addTest(load("test.integration.simple"))
    suite.addTest(load("test.integration.api"))
    suite.addTest(load("test.integration.client_ctors"))
    suite.addTest(load("test.integration.counts"))
    suite.addTest(load("test.integration.gateway"))
    suite.addTest(load("test.integration.icontainer"))
    suite.addTest(load("test.integration.isession"))
    suite.addTest(load("test.integration.ishare"))
    suite.addTest(load("test.integration.itypes"))
    suite.addTest(load("test.integration.metadatastore"))
    suite.addTest(load("test.integration.scripts"))
    suite.addTest(load("test.integration.files"))
    suite.addTest(load("test.integration.ping"))
    suite.addTest(load("test.integration.proj"))
    suite.addTest(load("test.integration.tickets1000"))
    suite.addTest(load("test.integration.tickets2000"))
    suite.addTest(load("test.scripts.suite._additional_tests"))
    suite.addTest(load("test.gateway.suite._additional_tests"))
    suite.addTest(load("test.tablestest.suite._additional_tests"))
    suite.addTest(load("test.tablestest.integration_suite._additional_tests"))
    return suite

if __name__ == "__main__":
    xmlrunner.XMLTestRunner(output='target/test-reports').run(additional_tests())
