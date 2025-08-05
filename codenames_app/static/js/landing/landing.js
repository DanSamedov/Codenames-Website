document.querySelectorAll("[data-open]").forEach((btn) => {
  btn.addEventListener("click", (e) => {
    e.preventDefault();
    const modalId = btn.getAttribute("data-open");
    const modal = document.getElementById(modalId);
    if (!modal) return;
    modal.classList.remove("hidden");
    modal.classList.add("flex");
  });
});

document.querySelectorAll("[data-close]").forEach((btn) => {
  btn.addEventListener("click", () => {
    const modalId = btn.getAttribute("data-close");
    const modal = document.getElementById(modalId);
    if (!modal) return;
    modal.classList.remove("flex");
    modal.classList.add("hidden");
  });
});

document.querySelectorAll(".modal-backdrop").forEach((backdrop) => {
  backdrop.addEventListener("click", (e) => {
    if (e.target === backdrop) {
      backdrop.classList.remove("flex");
      backdrop.classList.add("hidden");
    }
  });
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    const visibleModal = document.querySelector(".modal-backdrop:not(.hidden)");
    if (visibleModal) {
      visibleModal.classList.remove("flex");
      visibleModal.classList.add("hidden");
    }
  }
});
