from abc import abstractmethod
import requests
import typing


class Resolvable(typing.Protocol):
    _session: typing.ClassVar[requests.Session]
    _url: str
    _data: typing.Any
    _pk: typing.Optional[str]

    def resolve(self) -> requests.Response:
        if self._pk:
            return self._session.get(f"{self._url}{self._pk}")
        else:
            raise ValueError("Can't resolve an unknown/unsaved object")

    @property
    def data(self) -> typing.Any:
        if not self._data:  # type: ignore
            self._data = self.deserialize_response(self.resolve())
        return self._data

    @abstractmethod
    def deserialize_response(self, response: requests.Response) -> typing.Any:
        raise NotImplementedError


class Updateable(Resolvable, typing.Protocol):
    @abstractmethod
    def serialize_data(self) -> typing.Dict[str, typing.Any]:
        raise NotImplementedError

    def _update(self) -> requests.Response:
        uri = f"{self._url}{self._pk}/"
        data = self.serialize_data()
        return self._session.put(uri, json=data)

    def _create(self) -> requests.Response:
        data = self.serialize_data()
        return self._session.post(self._url, json=data)

    def save(self) -> typing.Any:
        if self._pk:
            response = self._update()
        else:
            response = self._create()
        return self.post_save(response)

    def delete(self) -> typing.Any:
        if not self._pk:
            raise ValueError("Can't delete unknown/unsaved object")
        else:
            url = f"{self._url}{self._pk}"
            response = self._session.delete(url)
            return self.post_delete(response)

    def post_save(self, response: requests.Response) -> typing.Any:
        pass

    def post_delete(self, response: requests.Response) -> typing.Any:
        pass


class SupportsNestedResources(Resolvable, typing.Protocol):
    _nested_resources: typing.Sequence[typing.Type["ResourceProtocol"]] = []

    def _setup_nested_resources(self) -> None:
        if self._pk:
            for r in self._nested_resources:
                setattr(self, r.__name__, self._convert_to_nested_resource(r))

    def _convert_to_nested_resource(
        self, resource: typing.Type["ResourceProtocol"]
    ) -> typing.Type["ResourceProtocol"]:
        url = f"{self._url}{self._pk}{resource.url}"
        name = resource.__name__
        return type(name, (resource,), {"url": url})


class ResourceInstanceProtocol(SupportsNestedResources, Updateable, typing.Protocol):
    pass


class ListProtocol(typing.Protocol):
    _session: typing.ClassVar[requests.Session]
    _url: str

    def __iter__(self):
        return iter(self.parse_response(self._session.get(self._url)))

    def parse_response(self, response) -> typing.Iterable:
        return response.json()


class ResourceProtocol(typing.Protocol):
    url: typing.ClassVar[str]
    instance_class: typing.ClassVar[typing.Type[ResourceInstanceProtocol]]
    list_class: typing.ClassVar[typing.Type[ListProtocol]]
    nested_resources: typing.ClassVar[
        typing.Sequence[typing.Type["ResourceProtocol"]]
    ] = []

    @classmethod
    @abstractmethod
    def get(cls, pk: str) -> ResourceInstanceProtocol:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def create(cls, data: typing.Dict[str, typing.Any]) -> ResourceInstanceProtocol:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def list(cls) -> ListProtocol:
        raise NotImplementedError
