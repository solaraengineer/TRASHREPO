const token = localStorage.getItem('accessToken');

fetch('/api/user/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  }
});