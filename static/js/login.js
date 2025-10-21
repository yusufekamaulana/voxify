document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("login-form");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();

    if (!username || !password) {
      Swal.fire({ icon: "warning", title: "Missing Fields", text: "Please fill all fields." });
      return;
    }

    try {
      const res = await fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
      });

      const data = await res.json();

      if (data.status === "success") {
        Swal.fire({ icon: "success", title: "Welcome!"
            , text: data.message })
          .then(() => window.location.href = "/onboarding");
      } else {
        Swal.fire({ icon: "error", title: "Login Failed", text: data.message });
      }
    } catch (err) {
      Swal.fire({ icon: "error", title: "Network Error", text: "Please try again." });
    }
  });
});
