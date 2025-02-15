from simple_mockforce import mock_salesforce
from simple_salesforce import Salesforce
from simple_salesforce.exceptions import SalesforceResourceNotFound

from tests.utils import MOCK_CREDS


@mock_salesforce
def test_crud_lifecycle():
    salesforce = Salesforce(**MOCK_CREDS)

    result = salesforce.Contact.create({"FirstName": "John", "LastName": "Doe"})

    record_id = result["id"]

    assert record_id
    assert result["success"] == True
    assert result["errors"] == []

    result = salesforce.Contact.get(record_id)

    assert result["Id"] == record_id
    assert result["FirstName"] == "John"
    assert result["LastName"] == "Doe"

    result = salesforce.Contact.update(record_id, {"LastName": "Smith"})

    assert result == 204

    result = salesforce.Contact.get(record_id)

    assert result["Id"] == record_id
    assert result["FirstName"] == "John"
    assert result["LastName"] == "Smith"

    result = salesforce.Contact.delete(record_id)

    assert result == 204

    failed = False
    try:
        result = salesforce.Contact.get(record_id)
    except SalesforceResourceNotFound:
        failed = True

    assert failed


@mock_salesforce
def test_crud_lifecycle_with_custom_id():
    salesforce = Salesforce(**MOCK_CREDS)

    custom_id = "imacustomid123"
    custom_id_field = "customExtIdField__c"

    result = salesforce.Contact.upsert(
        f"{custom_id_field}/{custom_id}",
        {"LastName": "Doe"},
    )

    assert result == 204

    result = salesforce.Contact.get_by_custom_id(custom_id_field, custom_id)

    assert result["Id"]
    assert result[custom_id_field] == custom_id
    assert result["LastName"] == "Doe"

    result = salesforce.Contact.upsert(
        f"{custom_id_field}/{custom_id}",
        {"LastName": "Smith"},
    )

    result = salesforce.Contact.get_by_custom_id(custom_id_field, custom_id)

    assert result["Id"]
    assert result[custom_id_field] == custom_id
    assert result["LastName"] == "Smith"

    result = salesforce.Contact.delete(result["Id"])

    assert result == 204

    failed = False
    try:
        salesforce.Contact.get_by_custom_id(custom_id_field, custom_id)
    except SalesforceResourceNotFound:
        failed = True

    assert failed


@mock_salesforce
def test_crud_lifecycle_with_custom_id_and_foreign_key():
    salesforce = Salesforce(**MOCK_CREDS)

    custom_id = "123-abc"
    custom_id_field = "SuperId__c"

    response = salesforce.CustomAccount__c.create(
        {"Name": "I'm Custom", "CustomAccountId__c": "xyz"}
    )
    custom_account_id = response["id"]

    result = salesforce.Contact.upsert(
        f"{custom_id_field}/{custom_id}",
        {
            "FirstName": "Seymour",
            "LastName": "Butz",
            f"{custom_id_field}": f"{custom_id}",
            "CustomAccount__r": {"CustomAccountId__c": "xyz"},
        },
    )

    assert result == 204

    result = salesforce.Contact.get_by_custom_id(custom_id_field, custom_id)

    assert result["Id"]
    assert result[custom_id_field] == custom_id
    assert result["FirstName"] == "Seymour"
    assert result["LastName"] == "Butz"
    assert result["CustomAccount__c"] == custom_account_id

    result = salesforce.Contact.upsert(
        f"{custom_id_field}/{custom_id}",
        {
            "FirstName": "Pierre",
            "LastName": "Pants",
            f"{custom_id_field}": f"{custom_id}",
            "CustomAccount__r": {"CustomAccountId__c": "xyz"},
        },
    )

    result = salesforce.Contact.get_by_custom_id(custom_id_field, custom_id)

    assert result["Id"]
    assert result[custom_id_field] == custom_id
    assert result["FirstName"] == "Pierre"
    assert result["LastName"] == "Pants"
    assert result["CustomAccount__c"] == custom_account_id

    result = salesforce.CustomAccount__c.get(custom_account_id)
    assert result["CustomAccountId__c"] == "xyz"


@mock_salesforce
def test_crud_error_handling():
    salesforce = Salesforce(**MOCK_CREDS)

    failed = False
    try:
        salesforce.I_Dont_Exist__c.get("512")
    except SalesforceResourceNotFound:
        failed = True

    assert failed

    failed = False
    try:
        salesforce.Contact.update("512", {"Name": "idk"})
    except SalesforceResourceNotFound:
        failed = True

    assert failed

    failed = False
    try:
        salesforce.Contact.delete("512")
    except SalesforceResourceNotFound:
        failed = True

    assert failed
