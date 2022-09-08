from rest_clown._interfaces import IResourceInstance, IResource, IResourceList
import requests
from typing import Dict, Any


class ResourceInstance(IResourceInstance[Dict[str, Any]]):
    def deserialize_response(self, response: requests.Response):
        return response.json()

    def serialize_data(self, data):
        return self.data


class ResourceList(IResourceList):

    def deserialize_response(self, response: requests.Response):
        return response.json()


class Resource(IResource[ResourceInstance]):
    pass
