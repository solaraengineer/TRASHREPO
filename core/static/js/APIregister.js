document.addEventListener('DOMContentLoaded', function () {

  // Register
  document.getElementById('registerForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const recaptchaToken = grecaptcha.getResponse();
    if (!recaptchaToken) {
      document.getElementById('regMessage').textContent = "Please complete the reCAPTCHA before submitting.";
      return;
    }

    const username = document.getElementById('regUsername').value;
    const email = document.getElementById('regEmail').value;
    const password = document.getElementById('regPassword').value;

    try {
      const res = await fetch('http://127.0.0.1:8000/api/register/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password, recaptcha: recaptchaToken })
      });

      const data = await res.json();
      document.getElementById('regMessage').textContent = data.message || data.error || 'Something went wrong.';
      grecaptcha.reset();

    } catch (error) {
      console.error("Register error:", error);
      document.getElementById('regMessage').textContent = "Network error or invalid response.";
    }
  });

  // Login
  document.getElementById('loginForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;

    try {
      const res = await fetch('http://127.0.0.1:8000/api/login/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      const data = await res.json();
      console.log("Login response:", data);

      if (data.access && data.refresh) {
        localStorage.setItem('accessToken', data.access);
        localStorage.setItem('refreshToken', data.refresh);
        document.getElementById('loginMessage').textContent = "Login successful!";
        window.location.href = "/dash/";
      } else {
        document.getElementById('loginMessage').textContent = data.error || 'Login failed.';
      }

    } catch (error) {
      console.error("Login fetch failed:", error);
      document.getElementById('loginMessage').textContent = "Network error during login.";
    }
  });

});