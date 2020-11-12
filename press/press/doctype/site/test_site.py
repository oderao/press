# -*- coding: utf-8 -*-
# Copyright (c) 2019, Frappe and Contributors
# See license.txt
from __future__ import unicode_literals

import unittest
from unittest.mock import Mock, patch

import frappe

from press.agent import Agent
from press.press.doctype.bench.test_bench import create_test_bench
from press.press.doctype.frappe_app.test_frappe_app import (
	create_test_frappe_app,
)
from press.press.doctype.plan.test_plan import create_test_plan
from press.press.doctype.proxy_server.test_proxy_server import (
	create_test_proxy_server,
)
from press.press.doctype.release_group.test_release_group import (
	create_test_release_group,
)
from press.press.doctype.server.test_server import create_test_server

from .site import Site


def create_test_site(subdomain: str) -> Site:
	"""Create test Site doc."""
	proxy_server = create_test_proxy_server()
	server = create_test_server(proxy_server.name)
	frappe_app = create_test_frappe_app()

	release_group = create_test_release_group(frappe_app.name)
	release_group.create_deploy_candidate()

	plan = create_test_plan()
	bench = create_test_bench(release_group.name, server.name)

	return frappe.get_doc(
		{
			"doctype": "Site",
			"status": "Active",
			"subdomain": subdomain,
			"server": server.name,
			"bench": bench.name,
			"plan": plan.name,
			"apps": [{"app": frappe_app.name}],
			"admin_password": "admin",
		}
	).insert(ignore_if_duplicate=True)


@patch.object(Agent, "create_agent_job", new=Mock(return_value={"job": 1}))
class TestSite(unittest.TestCase):
	"""Tests for Site Document methods."""

	def tearDown(self):
		frappe.db.rollback()

	def test_host_name_updates_perform_checks_on_host_name(self):
		"""Ensure update of host name triggers verification of host_name"""
		site = create_test_site("testsubdomain")
		site.host_name = "balu.codes"  # domain that doesn't exist
		self.assertRaises(frappe.exceptions.ValidationError, site.save)
