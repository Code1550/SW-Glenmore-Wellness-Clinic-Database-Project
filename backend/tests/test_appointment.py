def test_get_appointments(client):
    """Test GET /appointments endpoint."""
    response = client.get('/appointments')
    assert response.status_code == 200

def test_get_appointment_not_found(client):
    """Test GET /appointments/<id> for a non-existent appointment."""
    response = client.get('/appointments/99999')
    assert response.status_code == 404

def test_get_appointments_by_patient(client):
    """Test GET /appointments/patient/<id> endpoint."""
    response = client.get('/appointments/patient/99999')
    assert response.status_code == 200 # Should return 200 and an empty list

def test_get_appointments_by_staff(client):
    """Test GET /appointments/staff/<id> endpoint."""
    response = client.get('/appointments/staff/99999')
    assert response.status_code == 200 # Should return 200 and an empty list