import requests
import random
import string
import time
from jsonschema import validate

BASE_URL = "https://qa-internship.avito.com"
def gen_seller_id():
    return random.randint(111111, 999999)

def gen_name(length=12):
    return "test-" + ''.join(random.choice(string.ascii_lowercase) for _ in range(length))

ITEM_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "sellerID": {"type": "integer"},
        "name": {"type": "string"},
        "price": {"type": "integer"},
        "likes": {"type": "integer"},
        "viewCount": {"type": "integer"},
        "contacts": {"type": "integer"},
        "createdAt": {"type": "string"}
    },
    "required": ["id", "sellerID", "name", "price", "likes", "viewCount", "contacts", "createdAt"]
}

STAT_ARRAY_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "likes": {"type": "integer"},
            "viewCount": {"type": "integer"},
            "contacts": {"type": "integer"}
        },
        "required": ["likes", "viewCount", "contacts"]
    }
}

# Тесты
# Положительные сценарии

def test_create_item_success():
    seller = gen_seller_id()
    payload = {
        "sellerID": seller,
        "name": gen_name(),
        "price": 100,
        "likes": 0,
        "viewCount": 0,
        "contacts": 0
    }
    r = requests.post(f"{BASE_URL}/api/1/item", json=payload)
    assert r.status_code in (200, 201), f"Expected 200/201, got {r.status_code}, body: {r.text}"
    data = r.json()
    validate(instance=data, schema=ITEM_SCHEMA)
    assert data["sellerID"] == seller
    assert data["name"] == payload["name"]
    global CREATED_ITEM
    CREATED_ITEM = data

def test_get_item_by_id():
    try:
        item = CREATED_ITEM
    except NameError:
        seller = gen_seller_id()
        payload = {"sellerID": seller, "name": gen_name(), "price": 200, "likes": 1, "viewCount": 1, "contacts": 0}
        r = requests.post(f"{BASE_URL}/api/1/item", json=payload)
        assert r.status_code in (200, 201)
        item = r.json()
    r = requests.get(f"{BASE_URL}/api/1/item/{item['id']}")
    assert r.status_code == 200
    data = r.json()
    if isinstance(data, list):
        data = data[0]
    validate(instance=data, schema=ITEM_SCHEMA)
    assert data["id"] == item["id"]

def test_get_items_by_seller():
    seller = gen_seller_id()
    payload1 = {"sellerID": seller, "name": gen_name(), "price": 50, "likes": 0, "viewCount": 0, "contacts": 0}
    payload2 = {"sellerID": seller, "name": gen_name(), "price": 60, "likes": 0, "viewCount": 0, "contacts": 0}
    r1 = requests.post(f"{BASE_URL}/api/1/item", json=payload1)
    r2 = requests.post(f"{BASE_URL}/api/1/item", json=payload2)
    assert r1.status_code in (200,201)
    assert r2.status_code in (200,201)
    id1 = r1.json()["id"]
    id2 = r2.json()["id"]

    r = requests.get(f"{BASE_URL}/api/1/{seller}/item")
    assert r.status_code == 200
    arr = r.json()
    assert isinstance(arr, list)
    ids = [x.get("id") for x in arr]
    assert id1 in ids and id2 in ids
    for item in arr:
        assert item["sellerID"] == seller

def test_get_items_by_seller_empty():
    seller = gen_seller_id()
    r = requests.get(f"{BASE_URL}/api/1/{seller}/item")
    assert r.status_code == 200
    arr = r.json()
    assert isinstance(arr, list)

def test_get_statistic_for_item():
    seller = gen_seller_id()
    payload = {"sellerID": seller, "name": gen_name(), "price": 777, "likes": 3, "viewCount": 7, "contacts": 1}
    r = requests.post(f"{BASE_URL}/api/1/item", json=payload)
    assert r.status_code in (200,201)
    item = r.json()
    r2 = requests.get(f"{BASE_URL}/api/2/statistic/{item['id']}")
    assert r2.status_code in (200, 404), f"status {r2.status_code}, body: {r2.text}"
    if r2.status_code == 200:
        arr = r2.json()
        validate(instance=arr, schema=STAT_ARRAY_SCHEMA)

# Негативные тесты

def test_create_invalid_seller_id_low():
    payload = {"sellerID": 111110, "name": gen_name(), "price": 10, "likes": 0,"viewCount":0,"contacts":0}
    r = requests.post(f"{BASE_URL}/api/1/item", json=payload)
    assert r.status_code in (400, 422), f"Expected client error for low sellerID, got {r.status_code}"

def test_create_invalid_price_type():
    payload = {"sellerID": gen_seller_id(), "name": gen_name(), "price": "free", "likes": 0,"viewCount":0,"contacts":0}
    r = requests.post(f"{BASE_URL}/api/1/item", json=payload)
    assert r.status_code in (400, 422)

def test_get_nonexistent_item():
    fake_id = "non-existent-" + str(int(time.time()))
    r = requests.get(f"{BASE_URL}/api/1/item/{fake_id}")
    assert r.status_code in (404, 400)

def test_delete_item_v2():
    seller = gen_seller_id()
    payload = {"sellerID": seller, "name": gen_name(), "price": 5, "likes": 0,"viewCount": 0,"contacts": 0}
    r = requests.post(f"{BASE_URL}/api/2/item", json=payload)
    assert r.status_code in (200,201)
    item = r.json()
    rdel = requests.delete(f"{BASE_URL}/api/2/item/{item['id']}")
    assert rdel.status_code in (200, 204, 404), f"DELETE returned {rdel.status_code}, body: {rdel.text}"
