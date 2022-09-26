import pytest
from rest_clown.resources import Resource, ResourceInstance, ResourceList
from rest_clown.exceptions import RestClownException


@pytest.fixture
def resource(mocker):
    session = mocker.Mock()
    return Resource(session, "http://somehost.nl/resource/", ResourceInstance)


@pytest.fixture
def nested_resource(mocker):
    session = mocker.Mock()
    return Resource(
        session, "/nestedresource/", ResourceInstance, resource_list_class=ResourceList
    )


@pytest.fixture
def resource_with_nested_resource(nested_resource, mocker):
    session = mocker.Mock()
    return Resource(
        session,
        "http://somehost.nl/resource/",
        ResourceInstance,
        nested_resources=[("nested_resource", nested_resource)],
    )


@pytest.fixture
def resource_with_resource_list(nested_resource, mocker):
    session = mocker.Mock()
    return Resource(
        session,
        "http://somehost.nl/resource",
        ResourceInstance,
        nested_resources=[("nested_resource", nested_resource)],
        resource_list_class=ResourceList,
    )


def test_lazy_evaluation_not_evaluated(resource):
    some_resource = resource.get("3")
    assert some_resource._session.not_called()


def test_lazy_evaluation_evaluated(resource):
    some_resource = resource.get("3")
    _ = some_resource.data
    assert some_resource._session.get.called


def test_instance_save_after_create(resource):
    some_resource = resource.create(data={"k": "v"})
    some_resource.save()
    assert some_resource._session.post.called


def test_instance_save_after_get(resource):
    some_resource = resource.get("3")
    some_resource.save()
    assert some_resource._session.put.called


def test_direct_get(resource):
    some_resource = resource.get("3")
    assert type(some_resource) == ResourceInstance
    assert some_resource.url.endswith("/3/")


def test_resolve_on_unsaved_instance_raises_rest_clown_exception(resource):
    some_unsaved_instance = resource.create(data={"k": "v"})
    with pytest.raises(RestClownException):
        some_unsaved_instance.refresh()


def test_nested_resource_setup_without_list_class(resource_with_nested_resource):
    some_resource_instance = resource_with_nested_resource.get("3").nested_resource.get(
        "3"
    )
    assert (
        some_resource_instance.url == "http://somehost.nl/resource/3/nestedresource/3/"
    )


def test_nested_resource_setup_with_list_class(resource_with_resource_list):
    some_resource_instance = resource_with_resource_list.get("3")
    assert some_resource_instance.nested_resource._resource_list_class == ResourceList


def test_list_operation_not_allowed(resource_with_nested_resource):
    with pytest.raises(RestClownException):
        resource_with_nested_resource.list()


def test_list_operation_allowed(resource_with_resource_list):
    list_instance = resource_with_resource_list.list()
    assert type(list_instance) == ResourceList


