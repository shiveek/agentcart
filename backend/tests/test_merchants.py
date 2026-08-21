import uuid

def test_create_and_get_merchant(client):
    """Test merchant creation and retrieval endpoints."""
    payload = {
        "name": "GadgetVerse",
        "business_name": "GadgetVerse Retail Ltd",
        "description": "Electronics seller",
        "email": "info@gadgetverse.com",
        "currency": "INR",
    }
    response = client.post("/api/merchants", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "GadgetVerse"
    assert data["email"] == "info@gadgetverse.com"
    assert "id" in data
    merchant_id = data["id"]

    # Get merchant
    get_res = client.get(f"/api/merchants/{merchant_id}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "GadgetVerse"

    # Update merchant
    update_res = client.put(f"/api/merchants/{merchant_id}", json={"name": "GadgetVerse Pro"})
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "GadgetVerse Pro"


def test_merchant_not_found(client):
    """Test retrieving non-existent merchant returns 404."""
    random_id = str(uuid.uuid4())
    response = client.get(f"/api/merchants/{random_id}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_duplicate_merchant_email(client):
    """Test creating merchant with duplicate email returns 400."""
    payload = {
        "name": "Store A",
        "business_name": "Store A Ltd",
        "email": "unique@store.com",
        "currency": "INR",
    }
    res1 = client.post("/api/merchants", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/merchants", json=payload)
    assert res2.status_code == 400
    assert res2.json()["error"]["code"] == "BAD_REQUEST"
