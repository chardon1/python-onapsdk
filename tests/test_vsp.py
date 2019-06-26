#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Test vsp module."""
import mock
import pytest

import json
import requests

from onapsdk.vsp import Vsp
from onapsdk.vendor import Vendor
import onapsdk.constants as const
from onapsdk.sdc_element import SdcElement

@mock.patch.object(Vsp, 'send_message_json')
def test_get_all_no_vsp(mock_send):
    """Returns empty array if no vsps."""
    mock_send.return_value = {}
    assert Vsp.get_all() == []
    mock_send.assert_called_once_with("GET", 'get Vsps', 'http://sdc.api.fe.simpledemo.onap.org:30206/sdc1/feProxy/onboarding-api/v1.0/vendor-software-products')

@mock.patch.object(Vsp, 'send_message_json')
def test_get_all_some_vsps(mock_send):
    """Returns a list of vsp."""
    mock_send.return_value = {'results':[
        {'name': 'one', 'id': '1234', 'vendorName': 'vspOne'},
        {'name': 'two', 'id': '1235', 'vendorName': 'vspOne'}]}
    assert len(Vsp.get_all()) == 2
    vsp_1 = Vsp.get_all()[0]
    assert vsp_1.name == "one"
    assert vsp_1.identifier == "1234"
    assert vsp_1.created()
    vsp_2 = Vsp.get_all()[1]
    assert vsp_2.name == "two"
    assert vsp_2.identifier == "1235"
    assert vsp_2.vendor == vsp_1.vendor
    assert vsp_2.created()
    mock_send.assert_called_with("GET", 'get Vsps', 'http://sdc.api.fe.simpledemo.onap.org:30206/sdc1/feProxy/onboarding-api/v1.0/vendor-software-products')

def test_init_no_name():
    """Check init with no names."""
    vsp = Vsp()
    assert isinstance(vsp, SdcElement)
    assert vsp._identifier == None
    assert vsp._version == None
    assert vsp.name == "ONAP-test-VSP"
    assert vsp.headers["USER_ID"] == "cs0008"
    assert vsp.vendor == None
    assert isinstance(vsp._base_url(), str)
    assert "sdc1/feProxy/onboarding-api/v1.0" in vsp._base_url()

def test_init_with_name():
    """Check init with no names."""
    vsp = Vsp(name="YOLO")
    assert vsp._identifier == None
    assert vsp._version == None
    assert vsp.name == "YOLO"
    assert vsp.created() == False
    assert vsp.headers["USER_ID"] == "cs0008"
    assert vsp.vendor == None
    assert isinstance(vsp._base_url(), str)
    assert "sdc1/feProxy/onboarding-api/v1.0" in vsp._base_url()

def test_equality_really_equals():
    """Check two vsps are equals if name is the same."""
    vsp_1 = Vsp(name="equal")
    vsp_1.identifier  = "1234"
    vsp_2 = Vsp(name="equal")
    vsp_2.identifier  = "1235"
    assert vsp_1 == vsp_2

def test_equality_not_equals():
    """Check two vsps are not equals if name is not the same."""
    vsp_1 = Vsp(name="equal")
    vsp_1.identifier  = "1234"
    vsp_2 = Vsp(name="not_equal")
    vsp_2.identifier  = "1234"
    assert vsp_1 != vsp_2

def test_equality_not_equals_not_same_object():
    """Check a vsp and something different are not equals."""
    vsp_1 = Vsp(name="equal")
    vsp_1.identifier  = "1234"
    vsp_2 = Vendor(name="equal")
    assert vsp_1 != vsp_2

@mock.patch.object(Vsp, 'get_all')
def test_exists_not_exists(mock_get_all):
    """Return False if vsp doesn't exist in SDC."""
    vsp_1 = Vsp(name="one")
    vsp_1.identifier = "1234"
    mock_get_all.return_value = [vsp_1]
    vsp = Vsp(name="two")
    assert not vsp.exists()

@mock.patch.object(Vsp, 'get_all')
def test_exists_exists(mock_get_all):
    """Return True if vsp exists in SDC."""
    vsp_1 = Vsp(name="one")
    vsp_1.identifier = "1234"
    mock_get_all.return_value = [vsp_1]
    vsp = Vsp(name="one")
    assert vsp.exists()

@mock.patch.object(Vsp, 'get_all')
@mock.patch.object(Vsp, 'send_message_json')
def test_load_created(mock_send, mock_get_all):
    mock_send.return_value = {'results':
        [{'status': 'state_one', 'id': "5678", 'vendorName': 'vspOne'}]}
    vsp = Vsp(name="one")
    vsp.identifier = "1234"
    vsp.load()
    mock_get_all.assert_not_called()
    mock_send.assert_called_once_with('GET', 'get item', 'http://sdc.api.fe.simpledemo.onap.org:30206/sdc1/feProxy/onboarding-api/v1.0/items/1234/versions')
    assert vsp._status == None
    assert vsp.version == "5678"

@mock.patch.object(Vsp, 'get_all')
@mock.patch.object(Vsp, 'send_message_json')
def test_load_not_created(mock_send, mock_get_all):
    mock_send.return_value = {'results':
        [{'status': 'state_one', 'id': "5678", 'vendorName': 'vspOne'}]}
    vsp = Vsp(name="one")
    vsp.load()
    mock_get_all.return_value = []
    mock_send.assert_not_called()
    assert vsp._status == None
    assert vsp.version == None
    assert vsp.identifier == None

@mock.patch.object(Vsp, 'get_all')
@mock.patch.object(Vsp, 'send_message_json')
def test_load_created_but_not_known(mock_send, mock_get_all):
    mock_send.return_value = {'results':
        [{'status': 'state_one', 'id': "5678", 'vendorName': 'vspOne'}]}
    vsp = Vsp(name="one")
    found_vsp = Vsp(name="one")
    found_vsp.identifier = "1234"
    mock_get_all.return_value = [found_vsp]
    vsp.load()
    mock_send.assert_not_called()
    assert vsp.created() == True
    assert vsp._version == None
    assert vsp.identifier == "1234"

@mock.patch.object(Vsp, 'exists')
@mock.patch.object(Vsp, 'send_message_json')
def test_create_no_vendor(mock_send, mock_exists):
    """Do nothing if no vendor."""
    vsp = Vsp()
    mock_exists.return_value = False
    vsp.create()
    mock_send.assert_not_called()

@mock.patch.object(Vsp, 'exists')
@mock.patch.object(Vsp, 'send_message_json')
def test_create_already_exists(mock_send, mock_exists):
    """Do nothing if already created in SDC."""
    vsp = Vsp()
    vendor = Vendor()
    vendor._identifier = "1232"
    vsp.vendor = vendor
    mock_exists.return_value = True
    vsp.create()
    mock_send.assert_not_called()

@mock.patch.object(Vsp, 'exists')
@mock.patch.object(Vsp, 'send_message_json')
def test_create_issue_in_creation(mock_send, mock_exists):
    """Do nothing if not created but issue during creation."""
    vsp = Vsp()
    vendor = Vendor()
    vendor._identifier = "1232"
    vsp.vendor = vendor
    expected_data = '{\n  "name": "ONAP-test-VSP",\n  "description": "vendor software product",\n  "icon": "icon",\n  "category": "resourceNewCategory.generic",\n  "subCategory": "resourceNewCategory.generic.abstract",\n  "vendorName": "Generic-Vendor",\n  "vendorId": "1232",\n  "licensingData": {},\n  "onboardingMethod": "NetworkPackage"\n}'
    mock_exists.return_value = False
    mock_send.return_value = {}
    vsp.create()
    mock_send.assert_called_once_with("POST", "create Vsp", 'http://sdc.api.fe.simpledemo.onap.org:30206/sdc1/feProxy/onboarding-api/v1.0/vendor-software-products', data=expected_data)
    assert vsp.created() == False

@mock.patch.object(Vsp, 'exists')
@mock.patch.object(Vsp, 'send_message_json')
def test_create_OK(mock_send, mock_exists):
    """Create and update object."""
    vsp = Vsp()
    vendor = Vendor()
    vendor._identifier = "1232"
    vsp.vendor = vendor
    expected_data = '{\n  "name": "ONAP-test-VSP",\n  "description": "vendor software product",\n  "icon": "icon",\n  "category": "resourceNewCategory.generic",\n  "subCategory": "resourceNewCategory.generic.abstract",\n  "vendorName": "Generic-Vendor",\n  "vendorId": "1232",\n  "licensingData": {},\n  "onboardingMethod": "NetworkPackage"\n}'
    mock_exists.return_value = False
    mock_send.return_value = {
        'itemId': "1234",
        'version': {'id': "5678", 'status': 'state_created'}}
    vsp.create()
    mock_send.assert_called_once_with("POST", "create Vsp", 'http://sdc.api.fe.simpledemo.onap.org:30206/sdc1/feProxy/onboarding-api/v1.0/vendor-software-products', data=expected_data)
    assert vsp.created() == True
    assert vsp._status == const.DRAFT
    assert vsp.identifier == "1234"
    assert vsp.version == "5678"

@mock.patch.object(Vsp, 'load')
def test_version_no_load_no_created(mock_load):
    vsp = Vsp()
    assert vsp.version == None
    mock_load.assert_not_called()

@mock.patch.object(Vsp, 'load')
def test_version_no_load_created(mock_load):
    vsp = Vsp()
    vsp.identifier = "1234"
    vsp._version = "64"
    assert vsp.version == "64"
    mock_load.assert_not_called()

@mock.patch.object(Vsp, 'load')
def test_version_with_load(mock_load):
    vsp = Vsp()
    vsp.identifier = "1234"
    assert vsp.version == None
    mock_load.assert_called_once()

def test_status_no_load_no_created():
    vsp = Vsp()
    assert vsp.status == None

@mock.patch.object(Vsp, '_get_item_details')
def test_status_status_is_certified_in_SDC(mock_vsp_items):
    vsp = Vsp()
    vsp.identifier = "1234"
    mock_vsp_items.return_value={'results':[{'status': const.CERTIFIED}]}
    vsp._status = "Draft"
    assert vsp.status == const.CERTIFIED

@mock.patch.object(Vsp, '_get_vsp_details')
@mock.patch.object(Vsp, '_get_item_version_details')
@mock.patch.object(Vsp, '_get_item_details')
def test_status_version_is_not_dirty(mock_vsp_items, mock_vsp_items_version, mock_vsp_details):
    vsp = Vsp()
    vsp.identifier = "1234"
    mock_vsp_items.return_value={'results':[{'status': const.DRAFT}]}
    mock_vsp_items_version.return_value={"state": {'dirty': False}}
    mock_vsp_details.return_value={'validationData': "true"}
    assert vsp.status == const.COMMITED

@mock.patch.object(Vsp, '_get_vsp_details')
@mock.patch.object(Vsp, '_get_item_version_details')
@mock.patch.object(Vsp, '_get_item_details')
def test_status_version_is_dirty_has_validation_data(mock_vsp_items, mock_vsp_items_version,
                                     mock_vsp_details):
    vsp = Vsp()
    vsp.identifier = "1234"
    mock_vsp_items.return_value={'results':[{'status': const.DRAFT}]}
    mock_vsp_items_version.return_value={"state": {'dirty': True}}
    mock_vsp_details.return_value={'validationData': {'some': 'thing'}}
    assert vsp.status == const.VALIDATED

@mock.patch.object(Vsp, '_get_vsp_details')
@mock.patch.object(Vsp, '_get_item_version_details')
@mock.patch.object(Vsp, '_get_item_details')
def test_status_version_is_dirty_no_validation_data_no_state(mock_vsp_items, mock_vsp_items_version,
                                     mock_vsp_details):
    vsp = Vsp()
    vsp.identifier = "1234"
    mock_vsp_items.return_value={'results':[{'status': const.DRAFT}]}
    mock_vsp_items_version.return_value={"status": {'dirty': False}}
    mock_vsp_details.return_value={'no_validationData': {'some': 'thing'}}
    assert vsp.status == const.DRAFT

@mock.patch.object(Vsp, '_get_vsp_details')
@mock.patch.object(Vsp, '_get_item_version_details')
@mock.patch.object(Vsp, '_get_item_details')
def test_status_version_is_dirty_no_validation_data_but_state(mock_vsp_items, mock_vsp_items_version,
                                     mock_vsp_details):
    vsp = Vsp()
    vsp.identifier = "1234"
    mock_vsp_items.return_value={'results':[{'status': const.DRAFT}]}
    mock_vsp_items_version.return_value={"state": {'dirty': True}}
    mock_vsp_details.return_value={'no_validationData': {'some': 'thing'}}
    assert vsp.status == const.DRAFT

@mock.patch.object(Vsp, '_get_vsp_details')
@mock.patch.object(Vsp, '_get_item_version_details')
@mock.patch.object(Vsp, '_get_item_details')
def test_status_version_is_dirty_no_validation_data_but_networkPackageName(mock_vsp_items, mock_vsp_items_version,
                                     mock_vsp_details):
    vsp = Vsp()
    vsp.identifier = "1234"
    mock_vsp_items.return_value={'results':[{'status': const.DRAFT}]}
    mock_vsp_items_version.return_value={"state": {'dirty': True}}
    mock_vsp_details.return_value={'no_validationData': {'some': 'thing'}, 'networkPackageName': 'ubuntu16'}
    assert vsp.status == const.UPLOADED

@mock.patch.object(Vsp, 'send_message_json')
def test__get_vsp_details_not_created(mock_send):
    vsp = Vsp()
    assert vsp._get_vsp_details() == {}
    mock_send.assert_not_called()

@mock.patch.object(Vsp, 'load')
@mock.patch.object(Vsp, 'send_message_json')
def test__get_vsp_details_no_version(mock_send, mock_load):
    vsp = Vsp()
    vsp.identifier = "1234"
    mock_send.assert_not_called()
    assert vsp._get_vsp_details() == {}

@mock.patch.object(Vsp, 'send_message_json')
def test__get_vsp_details(mock_send):
    vsp = Vsp()
    vsp.identifier = "1234"
    vsp._version = "4567"
    mock_send.return_value = {'return': 'value'}
    assert vsp._get_vsp_details() == {'return': 'value'}
    mock_send.assert_called_once_with('GET', 'get vsp version', "{}/vendor-software-products/1234/versions/4567".format(vsp._base_url()))

@pytest.mark.parametrize("status", [const.DRAFT, const.CERTIFIED, const.UPLOADED, const.VALIDATED])
@mock.patch.object(Vsp, 'load_status')
@mock.patch.object(Vsp, 'send_message')
def test_submit_not_Commited(mock_send, mock_status, status):
    """Do nothing if not created."""
    vsp = Vsp()
    vsp._status = status
    vsp.submit()
    mock_send.assert_not_called()

@mock.patch.object(Vsp, 'load_status')
@mock.patch.object(Vsp, 'send_message')
def test_submit_OK(mock_send, mock_status):
    """Don't update status if submission NOK."""
    vsp = Vsp()
    vsp._status = const.COMMITED
    expected_data = '{\n\n  "action": "Submit"\n}'
    vsp._version = "1234"
    vsp._identifier = "12345"
    vsp.submit()
    mock_send.assert_called_once_with("PUT", "Submit Vsp", 'http://sdc.api.fe.simpledemo.onap.org:30206/sdc1/feProxy/onboarding-api/v1.0/vendor-software-products/12345/versions/1234/actions', data=expected_data)

@pytest.mark.parametrize("status", [const.DRAFT, const.COMMITED, const.UPLOADED, const.VALIDATED])
@mock.patch.object(Vsp, 'load_status')
@mock.patch.object(Vsp, 'send_message')
def test_create_csar_not_Certified(mock_send, mock_status, status):
    """Do nothing if not created."""
    vsp = Vsp()
    vsp._status = status
    vsp.create_csar()
    mock_send.assert_not_called()
    assert vsp.csar_uuid == None

@mock.patch.object(Vsp, 'load_status')
@mock.patch.object(Vsp, 'send_message')
def test_create_csar_not_OK(mock_send, mock_status):
    """Don't update status if submission NOK."""
    vsp = Vsp()
    vsp._status = const.CERTIFIED
    mock_send.return_value = {}
    expected_data = '{\n\n  "action": "Create_Package"\n}'
    vsp._version = "1234"
    vsp._identifier = "12345"
    vsp.create_csar()
    mock_send.assert_called_once_with("PUT", "Create_Package Vsp", 'http://sdc.api.fe.simpledemo.onap.org:30206/sdc1/feProxy/onboarding-api/v1.0/vendor-software-products/12345/versions/1234/actions', data=expected_data)
    assert vsp.csar_uuid == None

@mock.patch.object(Vsp, 'load_status')
@mock.patch.object(Vsp, 'send_message')
def test_create_csar_OK(mock_send, mock_status):
    """Don't update status if submission NOK."""
    vsp = Vsp()
    vsp._status = const.CERTIFIED
    result = requests.Response()
    result.status_code = 201
    result._content = json.dumps({'packageId': "64"}).encode('UTF-8')
    mock_send.return_value = result
    expected_data = '{\n\n  "action": "Create_Package"\n}'
    vsp._version = "1234"
    vsp._identifier = "12345"
    vsp.create_csar()
    mock_send.assert_called_once_with("PUT", "Create_Package Vsp", 'http://sdc.api.fe.simpledemo.onap.org:30206/sdc1/feProxy/onboarding-api/v1.0/vendor-software-products/12345/versions/1234/actions', data=expected_data)
    assert vsp.csar_uuid == "64"

@pytest.mark.parametrize("status", [const.DRAFT, const.CERTIFIED, const.UPLOADED, const.COMMITED])
@mock.patch.object(Vsp, 'load_status')
@mock.patch.object(Vsp, 'send_message')
def test_commit_not_Validated(mock_send, mock_status, status):
    """Do nothing if not created."""
    vsp = Vsp()
    vsp._status = status
    vsp.commit()
    mock_send.assert_not_called()

@mock.patch.object(Vsp, 'load_status')
@mock.patch.object(Vsp, 'send_message')
def test_commit_OK(mock_send, mock_status):
    """Don't update status if submission NOK."""
    vsp = Vsp()
    vsp._status = const.VALIDATED
    expected_data = '{\n\n  "commitRequest":{"message":"ok"},\n\n  "action": "Commit"\n}'
    vsp._version = "1234"
    vsp._identifier = "12345"
    vsp.commit()
    mock_send.assert_called_once_with("PUT", "Commit Vsp", 'http://sdc.api.fe.simpledemo.onap.org:30206/sdc1/feProxy/onboarding-api/v1.0/items/12345/versions/1234/actions', data=expected_data)

@pytest.mark.parametrize("status", [const.CERTIFIED, const.COMMITED, const.UPLOADED, const.VALIDATED])
@mock.patch.object(Vsp, 'load_status')
@mock.patch.object(Vsp, 'send_message')
def test_upload_not_Draft(mock_send, mock_status, status):
    """Do nothing if not created."""
    vsp = Vsp()
    vsp._status = status
    vsp.upload_files('data')
    mock_send.assert_not_called()

@mock.patch.object(Vsp, 'load_status')
@mock.patch.object(Vsp, 'send_message')
def test_upload_not_OK(mock_send, mock_status):
    """Don't update status if submission NOK."""
    vsp = Vsp()
    vsp._status = const.DRAFT
    mock_send.return_value = None
    expected_data = '{\n\n  "action": "Create_Package"\n}'
    vsp._version = "1234"
    vsp._identifier = "12345"
    vsp.upload_files('data')
    mock_send.assert_called_once_with('POST', 'upload ZIP for Vsp', "http://sdc.api.fe.simpledemo.onap.org:30206/sdc1/feProxy/onboarding-api/v1.0/vendor-software-products/12345/versions/1234/orchestration-template-candidate", files={'upload': 'data'}, headers={'Accept': 'application/json', 'USER_ID': 'cs0008', 'Authorization': 'Basic YWFpOktwOGJKNFNYc3pNMFdYbGhhazNlSGxjc2UyZ0F3ODR2YW9HR21KdlV5MlU=', 'Accept-Encoding': 'gzip, deflate'})

@mock.patch.object(Vsp, 'load_status')
@mock.patch.object(Vsp, 'send_message')
def test_upload_OK(mock_send, mock_status):
    """Don't update status if submission NOK."""
    vsp = Vsp()
    vsp._status = const.DRAFT
    mock_send.return_value = True
    expected_data = '{\n\n  "action": "Create_Package"\n}'
    vsp._version = "1234"
    vsp._identifier = "12345"
    vsp.upload_files('data')
    mock_send.assert_called_once_with('POST', 'upload ZIP for Vsp', "http://sdc.api.fe.simpledemo.onap.org:30206/sdc1/feProxy/onboarding-api/v1.0/vendor-software-products/12345/versions/1234/orchestration-template-candidate", files={'upload': 'data'}, headers={'Accept': 'application/json', 'USER_ID': 'cs0008', 'Authorization': 'Basic YWFpOktwOGJKNFNYc3pNMFdYbGhhazNlSGxjc2UyZ0F3ODR2YW9HR21KdlV5MlU=', 'Accept-Encoding': 'gzip, deflate'})

@pytest.mark.parametrize("status", [const.CERTIFIED, const.COMMITED, const.DRAFT, const.VALIDATED])
@mock.patch.object(Vsp, 'load_status')
@mock.patch.object(Vsp, 'send_message_json')
def test_validate_not_Draft(mock_send, mock_status, status):
    """Do nothing if not created."""
    vsp = Vsp()
    vsp._status = status
    vsp.validate()
    mock_send.assert_not_called()

@mock.patch.object(Vsp, 'load_status')
@mock.patch.object(Vsp, 'send_message_json')
def test_validate_not_OK(mock_send, mock_status):
    """Don't update status if submission NOK."""
    vsp = Vsp()
    vsp._status = const.UPLOADED
    mock_send.return_value = {}
    vsp._version = "1234"
    vsp._identifier = "12345"
    vsp.validate()
    mock_send.assert_called_once_with('PUT', 'Validate artifacts for Vsp', 'http://sdc.api.fe.simpledemo.onap.org:30206/sdc1/feProxy/onboarding-api/v1.0/vendor-software-products/12345/versions/1234/orchestration-template-candidate/process')

@mock.patch.object(Vsp, 'load_status')
@mock.patch.object(Vsp, 'send_message_json')
def test_validate_not_success(mock_send, mock_status):
    """Don't update status if submission NOK."""
    vsp = Vsp()
    vsp._status = const.UPLOADED
    mock_send.return_value = {'status': 'not_success'}
    vsp._version = "1234"
    vsp._identifier = "12345"
    vsp.validate()
    mock_send.assert_called_once_with('PUT', 'Validate artifacts for Vsp', 'http://sdc.api.fe.simpledemo.onap.org:30206/sdc1/feProxy/onboarding-api/v1.0/vendor-software-products/12345/versions/1234/orchestration-template-candidate/process')

@mock.patch.object(Vsp, 'load_status')
@mock.patch.object(Vsp, 'send_message_json')
def test_validate_OK(mock_send, mock_status):
    """Don't update status if submission NOK."""
    vsp = Vsp()
    vsp._status = const.UPLOADED
    mock_send.return_value = {'status': 'Success'}
    vsp._version = "1234"
    vsp._identifier = "12345"
    vsp.validate()
    mock_send.assert_called_once_with('PUT', 'Validate artifacts for Vsp', 'http://sdc.api.fe.simpledemo.onap.org:30206/sdc1/feProxy/onboarding-api/v1.0/vendor-software-products/12345/versions/1234/orchestration-template-candidate/process')
