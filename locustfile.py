#Нагрузочное тестирование (tests/load/locustfile.py)

from locust import HttpUser, task, between

class ShortLinkUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def create_short_link(self):
        self.client.post(
            "/links/shorten",
            json={"link": "http://example.com"},
        )
    
    @task(3)
    def access_short_link(self):
        self.client.get("/links/abc123")