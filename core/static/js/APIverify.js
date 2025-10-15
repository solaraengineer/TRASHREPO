function submitCode() {
  const code = document.getElementById("code").value;

  fetch('https://fwaeh.cloud/api/register/verify/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    credentials: 'include',
    body: JSON.stringify({ code: code })
  })
  .then(res => res.json())
  .then(data => {
    if (data.message) {
      alert(" Success: " + data.message);
      window.location.href = "/dash";
    } else {
      alert(" Error: " + (data.error || "Unknown error"));
    }
  })
  .catch(err => {
    console.error("Fetch error:", err);
    alert("Something went wrong. Check console.");
  });
}