document.querySelectorAll("[data-open]").forEach((btn) => {
  btn.addEventListener("click", (e) => {
    e.preventDefault();
    const modalId = btn.getAttribute("data-open");
    const modal = document.getElementById(modalId);
    if (!modal) return;
    modal.classList.remove("hidden");
    modal.classList.add("visible");
  });
});

document.querySelectorAll("[data-close]").forEach((btn) => {
  btn.addEventListener("click", () => {
    const modalId = btn.getAttribute("data-close");
    const modal = document.getElementById(modalId);
    if (!modal) return;
    modal.classList.remove("visible");
    modal.classList.add("hidden");
  });
});

document.querySelectorAll(".modal-backdrop").forEach((backdrop) => {
  backdrop.addEventListener("click", (e) => {
    if (e.target === backdrop) {
      backdrop.classList.remove("visible");
      backdrop.classList.add("hidden");
    }
  });
});
