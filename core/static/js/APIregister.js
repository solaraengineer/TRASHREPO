    document.addEventListener('DOMContentLoaded', function () {

        document.getElementById('registerForm').addEventListener('submit', async function (e) {
            e.preventDefault();

            const recaptchaToken = grecaptcha.getResponse();
            if (!recaptchaToken) {
                document.getElementById('regMessage').textContent = " Please complete the reCAPTCHA before submitting.";
                return;
            }

            const username = document.getElementById('regUsername').value;
            const email = document.getElementById('regEmail').value;
            const password = document.getElementById('regPassword').value;

            console.log(" Submitting registration...");

            try {
                const res = await fetch('http://127.0.0.1:8000/api/register/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        username,
                        email,
                        password,
                        recaptcha: recaptchaToken
                    })
                });

                if (!res.ok) {
                    console.error("HTTP error:", res.status);
                }


                const data = await res.json();
                console.log("Response:", data);

                document.getElementById('regMessage').textContent =
                    data.message || data.error || 'Something happened during registration.';


                grecaptcha.reset();

            } catch (error) {
                console.error("Fetch failed:", error);
                document.getElementById('regMessage').textContent = "Network error or invalid response.";
            }
        });


        document.getElementById('loginForm').addEventListener('submit', async function (e) {
            e.preventDefault();

            const email = document.getElementById('loginEmail').value;
            const password = document.getElementById('loginPassword').value;

            const res = await fetch('http://127.0.0.1:8100/api/login/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email, password })
            });

            const data = await res.json();

            if (data.message === "2FA code sent to email.") {
                document.getElementById('loginMessage').textContent = "Check your email for a 2FA code.";
                window.location.href = "/verify";
            } else {
                document.getElementById('loginMessage').textContent =
                    data.error || 'Login failed.';
            }
        });

        const verifyForm = document.getElementById('verifyForm');
        if (verifyForm) {
            verifyForm.addEventListener('submit', async function (e) {
                e.preventDefault();

                const code = document.getElementById('verifyCode').value;

                const res = await fetch('http://127.0.0.1:8100/api/login/verify/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    credentials: 'include',
                    body: JSON.stringify({ code })
                });

                const data = await res.json();

                if (data.access && data.refresh) {
                    localStorage.setItem('accessToken', data.access);
                    localStorage.setItem('refreshToken', data.refresh);
                    window.location.href = "/dash";
                } else {
                    document.getElementById('verifyMessage').textContent =
                        data.error || 'Verification failed.';
                }
            });
        }

    });