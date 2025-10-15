document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('registerForm').addEventListener('submit', async function (e) {
        e.preventDefault();

        const recaptchaToken = grecaptcha.getResponse();
        const username = document.getElementById('regUsername').value;
        const email = document.getElementById('regEmail').value;
        const password = document.getElementById('regPassword').value;
        console.log("got here so far")

        const res = await fetch('https://fwaeh.cloud/api/register/', {
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

        const data = await res.json();
        document.getElementById('regMessage').textContent =
            data.message || data.error || 'Something happened during registration.';
        console.log("got here so far")
    });


    document.getElementById('loginForm').addEventListener('submit', async function (e) {
        e.preventDefault();

        const email = document.getElementById('loginEmail').value;
        const password = document.getElementById('loginPassword').value;

        const res = await fetch('https://fwaeh.cloud/api/login/', {
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

            const res = await fetch('https://fwaeh.cloud/api/login/verify/', {
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