document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("seat-form");
  if (!form) return;
  const checks = [...form.querySelectorAll('input[name="seats"]:not(:disabled)')];
  const count = document.getElementById("selected-count");
  const total = document.getElementById("total-price");
  const price = checks.length ? Number(checks[0].dataset.price) : 0;
  function update() {
    const chosen = checks.filter(c => c.checked);
    count.textContent = `${chosen.length} seat${chosen.length === 1 ? "" : "s"}`;
    total.textContent = `₹${(chosen.length * price).toFixed(2)}`;
  }
  checks.forEach(c => c.addEventListener("change", update));
  form.addEventListener("submit", e => {
    if (!checks.some(c => c.checked)) {
      e.preventDefault();
      alert("Please select at least one available seat.");
    }
  });
  update();
});
