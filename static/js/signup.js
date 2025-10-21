document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("signup-form");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const username = form.querySelector('input[type="text"]').value.trim();
    const email = form.querySelector('input[type="email"]').value.trim();
    const password = form.querySelector('input[type="password"]').value.trim();

    if (!username || !email || !password) {
      Swal.fire({ icon: "warning", title: "Missing Fields", text: "Please fill all fields." });
      return;
    }

    try {
      const res = await fetch("/api/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, email, password }),
      });

      const data = await res.json();

      if (data.status === "success") {
        Swal.fire({
          icon: "success",
          title: "Account Created!",
          text: data.message,
          timer: 1500,
          showConfirmButton: false,
        }).then(() => (window.location.href = "/login"));
      } else {
        Swal.fire({ icon: "error", title: "Signup Failed", text: data.message });
      }
    } catch (err) {
      Swal.fire({ icon: "error", title: "Network Error", text: "Please try again." });
    }
  });
});
