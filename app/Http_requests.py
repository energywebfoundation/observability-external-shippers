import requests

class Http_requests:

    def __init__(self, url, token, authorization="Basic", payload={}, headers={}):
        self.url = url
        self.token = token
        self.authorization = authorization  # set authorization method, default is Basic
        self.payload = payload
        self.headers = dict({'Authorization': self.authorization + ' ' + self.token}, **headers)

    def print_me(self):
        print(self.url)
        print(self.token)
        print(self.authorization)
        print(self.headers)


    def reset_url(self, url):

        """resets url that class was initialized with"""

        self.url = url


    def get(self):

        # Checks status via http GET request

        try:
            response = requests.request("GET", self.url, headers=self.headers, data=self.payload)
            status_code = response.status_code
            text = response.text
        except Exception as e:
            status_code = "888"
            text = str(e)

        return text, status_code

    def delete_resource(self):

        """Deletes resource via http DELETE request"""

        try:
            response = requests.request("DELETE", self.url, headers=self.headers, data=self.payload)
            status_code = response.status_code
            text = response.text
        except Exception as e:
            status_code = "888"
            text = str(e)

        return text, status_code

    def post(self, body):

        """POST body via http request"""

        try:
            response = requests.request("POST", self.url, headers=self.headers, json=body)
            status_code = response.status_code
            text = response.text
        except Exception as e:
            status_code = "888"
            text = str(e)

        return text, status_code

    def put(self, body):

        """PUT body via http request"""

        try:
            response = requests.request("PUT", self.url, headers=self.headers, data=body)
            status_code = response.status_code
            text = response.text
        except Exception as e:
            status_code = "888"
            text = str(e)

        return text, status_code
