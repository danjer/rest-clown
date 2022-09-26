from abc import abstractmethod, ABC
import requests
from typing import Any, Optional, TypeVar, Type, Sequence, Dict, Generic, Tuple
from rest_clown.exceptions import RestClownException

T = TypeVar("T")
R = TypeVar("R", bound="IResourceInstance")
RL = TypeVar("RL", bound="IResourceList")


class IResourceList(ABC, Generic[T]):
    def __init__(
        self,
        session,
        url,
        nested_resources: Optional[Sequence[Tuple[str, "IResource"]]],
        params: Optional[Dict[str, str]] = None
    ):
        self._session = session
        self._nested_resources = nested_resources
        self._url = url
        self._data: Optional[T] = None
        self._params = params

    @property
    def data(self) -> T:
        if not self._data:
            self._data = self.deserialize_response(self.resolve())
        return self._data

    def resolve(self):
        return self._session.get(self._url, params=self._params)

    @abstractmethod
    def deserialize_response(self, r) -> T:
        pass


class IResourceInstance(ABC, Generic[T]):
    def __init__(
        self,
        session: requests.Session,
        url: str,
        pk: Optional[str] = None,
        data: Optional[T] = None,
        nested_resources: Optional[Sequence[Tuple[str, "IResource"]]] = None,
    ):
        self._session = session
        self._url = url
        self._pk = pk
        self._data: Optional[T] = data
        for n, r in nested_resources or []:
            setattr(self, n, self.convert_to_nested_resource(r))

    @property
    def data(self) -> T:
        if not self._data:
            self._data = self.deserialize_response(self.resolve())
        return self._data

    @property
    def url(self) -> str:
        if self._pk:
            return f"{self._url}{self._pk}/"
        else:
            return self._url

    def refresh(self):
        self._data = None
        _ = self.data

    def convert_to_nested_resource(self, resource: "IResource"):
        session = resource._session
        url = f"{self._url}{self._pk}{resource._url}"
        instance_class = resource._resource_instance_class
        list_class = resource._resource_list_class
        return type(resource)(
            session, url, instance_class, resource_list_class=list_class
        )

    def resolve(self):
        if not self._pk:
            raise RestClownException("Cant resolve an unknown/unsaved instance")
        url = f"{self._url}{self._pk}"
        return self._session.get(url)

    def save(self) -> Any:
        if self._pk:
            response = self._update()
        else:
            response = self._create()
        return self.post_save(response)

    def _update(self):
        url = f"{self._url}{self._pk}/"
        json_data = self.serialize_data(self.data)
        return self._session.put(url, json=json_data)

    def _create(self):
        json_data = self.serialize_data(self.data)
        return self._session.post(self._url, json=json_data)

    def post_save(self, response: requests.Response) -> Any:
        pass

    @abstractmethod
    def deserialize_response(self, response) -> T:
        raise NotImplementedError

    @abstractmethod
    def serialize_data(self, data: T) -> Dict[str, Any]:
        raise NotImplementedError


class IResource(ABC, Generic[R, RL]):
    def __init__(
        self,
        session: requests.Session,
        url: str,
        resource_instance_class: Type[R],
        resource_list_class: Optional[Type[RL]] = None,
        nested_resources: Optional[Sequence[Tuple[str, "IResource"]]] = None,
    ):
        self._session = session
        self._url = url
        self._resource_instance_class = resource_instance_class
        self._resource_list_class = resource_list_class
        self._nested_resources = nested_resources

    def set_session(self, session: requests.Session) -> None:
        self._session = session
        if self._nested_resources:
            for _, resource in self._nested_resources:
                resource.set_session(session)

    def get(self, pk: str) -> R:
        return self._resource_instance_class(
            self._session, self._url, pk=pk, nested_resources=self._nested_resources
        )

    def create(self, data) -> R:
        return self._resource_instance_class(
            self._session, self._url, nested_resources=self._nested_resources, data=data
        )

    def list(self, params=None) -> RL:
        if not self._resource_list_class:
            raise RestClownException(
                "Must set the resource_list_class to call this operations"
            )
        return self._resource_list_class(
            self._session, self._url, self._nested_resources, params
        )
