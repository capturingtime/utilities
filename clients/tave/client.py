"""
from git.ctp.utilities.classes.tave import Tave
tave = Tave("550fedac-2c50-098c-8dd7-45e100d2-12f9127b28ce")

Also, make a requests.Session() client that any CRM should reference to handle underlying HTTP

"""
from requests import Request, Session
import re
import urllib.parse


def id_in_path(path) -> bool:
    pattern = re.compile(r"^\/[a-z\-\/]+[a-z0-9]{26}.*$")
    return bool(pattern.match(path))


class Client:
    def __init__(self):
        self._session = Session()

    def request(self, *args, **kwargs) -> Request:
        # https://requests.readthedocs.io/en/latest/user/advanced/#prepared-requests
        req = Request(*args, **kwargs)
        return req.prepare()

    def send(self, request: Request = None, **kwargs):
        if request is None:
            raise ValueError("There is no request to send")
        return self._session.send(request, **kwargs)


class APISpecV2(Client):
    url = "https://tave.io/v2"
    spec_path = "/openapi.json"
    version = 2

    def __init__(self):
        super().__init__()
        self.__spec: dict = self.send(
            request=self.request("GET", url=f"{self.url}{self.spec_path}")
        ).json()

    def _list_path_params(self, path: str) -> list:
        """List out the parameters for a given path"""
        param_list = (
            self.__spec["paths"][path].get("get", list()).get("parameters", list())
        )

        if len(param_list) == 0:
            return param_list
        else:
            result = list()
            # param_list = [v.get("$ref").split("/")[-1] for v in param_list if v.get("$ref")]
            for v in param_list:
                p = v.get("name") if "name" in v else v.get("$ref")
                result.append(p.split("/")[-1])
        return result

    @property
    def get_spec(self) -> dict:
        """return the spec dict"""
        return self.__spec

    @property
    def get_paths(self) -> list:
        """Return a list of paths"""
        return self.__spec["paths"].keys()


class Tave:
    def __init__(self, api_key: str, api_ver: int = 2):
        # super().__init__()
        self.__api_key: str = api_key
        self._api = None

        if api_ver == 2:
            self._api = APISpecV2()
        else:
            raise ValueError(
                f"The API version provided ({api_ver}) is unavailable at this time"
            )

    def _format_req(
        self, method: str, path: str, path_params: dict = dict(), *args, **kwargs
    ) -> dict:
        """A simple client to format requests to the API"""

        path = path.lower()
        method = method.upper()
        headers = {"X-API-KEY": self.__api_key, "Accept": "application/json"}
        url = f"{self._api.url}{path}"

        if path_params and method == "GET":
            url = f"{url}?{urllib.parse.urlencode(path_params)}"
        elif path_params:
            # Add logging WARN about params being ignored
            pass

        # Clean this up, checks if path string provided matches a valid endpoint
        spec_path = re.sub(r"[a-z0-9]{26}", "{id}", path) if id_in_path(path) else path
        spec_ref = self._api.get_spec.get("paths").get(spec_path, None)

        if spec_path not in self._api.get_paths:
            spec_path = (
                re.sub(r"[a-z0-9]{26}", "{jobId}", path) if id_in_path(path) else path
            )
            spec_ref = self._api.get_spec.get("paths").get(spec_path, None)
            if spec_path not in self._api.get_paths:
                raise ValueError(
                    f"path must be one of {[v for v in self._api.get_paths]}. Got: {spec_path}"
                )
        #######

        if method.lower() not in spec_ref.keys():
            raise ValueError(
                f"The HTTP method for {path} must be one of {[v.upper() for v in spec_ref.keys()]}."
                f" Got: {method}"
            )

        return self._api.request(method, url, *args, headers=headers, **kwargs)

    def get(self, path: str, params: dict = dict()) -> dict:
        req = self._format_req("GET", path, params)
        return self._api.send(req).json()

    def post(self, path: str, body: dict) -> dict:
        req = self._format_req("POST", path)
        return self._api.send(req).json()

    def put(self, path: str, body: dict) -> dict:
        req = self._format_req("PUT", path)
        return self._api.send(req).json()

    def delete(self, path: str) -> dict:
        req = self._format_req("DELETE", path)
        return self._api.send(req).json()
