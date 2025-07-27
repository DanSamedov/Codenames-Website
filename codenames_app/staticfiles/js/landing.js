const modalButtons = document.querySelectorAll("[data-open]");
const closeButtons = document.querySelectorAll(".modal-btn-close");

const toggleModal = (modalId) => {
  document.getElementById(modalId).classList.toggle("is-hidden");
};

modalButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const modalId = button.getAttribute("data-open");
    toggleModal(modalId);
  });
});

closeButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const modalId = button.getAttribute("data-modal");
    toggleModal(modalId);
  });
});
