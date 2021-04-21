import json
import uuid

from urllib.parse import urlparse

from python_soql_parser import parse

from simple_mockforce.utils import (
    parse_detail_url,
    parse_create_url,
    find_object_and_index,
)
from simple_mockforce.virtual import virtual_salesforce


def query_callback(request):
    parse_results = parse(request.params["q"])
    sobject = parse_results["sobject"]
    fields = parse_results["fields"].asList()
    limit = parse_results["limit"].asList()
    objects = virtual_salesforce.get_sobjects(sobject)
    # TODO: construct attributes
    records = [*map(lambda record: {field: record[field] for field in fields}, objects)]
    if limit:
        limit: int = limit[0]
        records = records[:limit]

    body = {
        "totalSize": len(records),
        "done": True,
        "records": records,
    }
    return (200, {}, json.dumps(body))


def get_callback(request):
    url = request.url
    path = urlparse(url).path
    sobject, _, record_id = parse_detail_url(path)

    object_ = virtual_salesforce.get(sobject, record_id)

    return (
        200,
        {},
        json.dumps({"attributes": {"type": sobject, "url": path}, **object_}),
    )


def create_callback(request):
    url = request.url
    path = urlparse(url).path
    body = json.loads(request.body)

    sobject = parse_create_url(path)

    normalized = {key.lower(): value for key, value in body.items()}

    id_ = str(uuid.uuid4())

    normalized["id"] = id_

    virtual_salesforce.create(sobject, normalized)

    return (
        200,
        {},
        # yep, salesforce lowercases id on create's response
        json.dumps({"id": id_, "success": True, "errors": []}),
    )


def update_callback(request):
    url = request.url
    path = urlparse(url).path
    body = json.loads(request.body)

    sobject, upsert_key, record_id = parse_detail_url(path)

    virtual_salesforce.update(sobject, record_id, body, upsert_key=upsert_key)

    return (
        204,
        {},
        json.dumps({}),
    )


def delete_callback(request):
    url = request.url
    path = urlparse(url).path

    sobject, _, record_id = parse_detail_url(path)
    virtual_salesforce.delete(sobject, record_id)

    return (
        204,
        {},
        json.dumps({}),
    )