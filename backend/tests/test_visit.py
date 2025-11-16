def test_get_visits(client):
    """Test GET /visits endpoint."""
    response = client.get('/visits')
    assert response.status_code == 200

def test_get_visit_not_found(client):
    """Test GET /visits/<id> for a non-existent visit."""
    response = client.get('/visits/99999')
    assert response.status_code == 404

def test_get_visits_by_patient(client):
    """Test GET /visits/patient/<id> endpoint."""
    response = client.get('/visits/patient/99999')
    assert response.status_code == 200 # Returns 200 and empty list

def test_get_visit_diagnoses(client):
    """Test GET /visits/<id>/diagnoses endpoint."""
    response = client.get('/visits/99999/diagnoses')
    assert response.status_code == 200 # Returns 200 and empty list

def test_get_visit_procedures(client):
    """Test GET /visits/<id>/procedures endpoint."""
    response = client.get('/visits/99999/procedures')
    assert response.status_code == 200 # Returns 200 and empty list