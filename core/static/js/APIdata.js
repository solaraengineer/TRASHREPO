const token = localStorage.getItem('accessToken');

fetch('https://fwwaeh.cloud/api/user/', {
  method: 'GET',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  }
})
  .then(res => res.json())
  .then(data => {
    document.getElementById('username').textContent = data.username;
    document.getElementById('email').textContent = data.email;
    document.getElementById('userId').textContent = data.id;

  })
  .catch(err => {
    console.error("Failed to fetch user:", err);
    document.getElementById('userBox').innerHTML = "<p>Error loading user data.</p>";
  });