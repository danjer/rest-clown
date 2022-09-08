from rest_clown._protocols import (
    ResourceInstanceProtocol,
    ResourceProtocol,
    ListProtocol,
)
import requests
import typing


class ResourceInstance(ResourceInstanceProtocol):
    def __init__(
        self,
        url: str,
        pk: typing.Optional[str] = None,
        data: typing.Optional[typing.Dict[str, typing.Any]] = None,
        nested_resources: typing.Optional[
            typing.Sequence[typing.Type["ResourceProtocol"]]
        ] = None,
    ):
        self._data = data
        self._url = url
        self._pk = pk
        self._nested_resources = nested_resources or []
        self._setup_nested_resources()

    def deserialize_response(self, response: requests.Response) -> typing.Any:
        return response.json()

    def serialize_data(self) -> typing.Dict[str, typing.Any]:
        return self.data


class ResourceLister(ListProtocol):
    def __init__(self, url):
        self._url = url


class Resource(ResourceProtocol):
    instance_class: typing.ClassVar[typing.Type[ResourceInstance]]
    nested_resources: typing.ClassVar[
        typing.Sequence[typing.Type["ResourceProtocol"]]
    ] = []
    list_class = ResourceLister

    @classmethod
    def get(cls, pk: str) -> ResourceInstance:
        return cls.instance_class(cls.url, pk=pk, nested_resources=cls.nested_resources)

    @classmethod
    def create(cls, data: typing.Dict[str, typing.Any]) -> ResourceInstance:
        instance = cls.instance_class(cls.url, data=data)
        instance.save()
        return instance

    @classmethod
    def list(cls):
        return cls.list_class(cls.url)
