import typing

from rest_clown.resources import Resource, ResourceInstance

api_url = "https://6310a8f836e6a2a04ef436bf.mockapi.io/api/"


class SnackResource(Resource):
    url = f"/snacks/"
    instance_class = ResourceInstance


class MenuResource(Resource):
    url = f"{api_url}/menu/"
    instance_class = ResourceInstance
    nested_resources = [SnackResource]
