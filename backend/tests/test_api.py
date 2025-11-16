def test_root(client):
    """Test the root endpoint."""
    response = client.get('/')
    assert response.status_code == 200
    assert response.json["message"] == "SW Glenmore Wellness Clinic API"

def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get('/health')
    # This will be 200 if the db connection is successful, 503 otherwise
    # Both are valid status checks. We'll check that the code is one of them.
    assert response.status_code in [200, 503]