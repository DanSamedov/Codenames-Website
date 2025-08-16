(() => {
  const MOBILE_ID = "modal-mobile-menu";

  const isHidden = (el) => el.classList.contains("hidden");
  const qs = (sel, root = document) => root.querySelector(sel);

  function openStandardModal(id) {
    const m = document.getElementById(id);
    if (!m) return;
    m.classList.remove("hidden");
    m.classList.remove("block");
    m.classList.add("flex");
  }
  function closeStandardModal(target) {
    const m =
      typeof target === "string" ? document.getElementById(target) : target;
    if (!m) return;
    m.classList.remove("flex");
    m.classList.remove("block");
    m.classList.add("hidden");
  }

  function getMobileEls() {
    const overlay = document.getElementById(MOBILE_ID);
    return {
      overlay,
      drawer: overlay ? qs(".drawer-panel", overlay) : null,
    };
  }

  function openMobileMenu() {
    const { overlay, drawer } = getMobileEls();
    if (!overlay || !drawer) return;

    overlay.setAttribute("aria-hidden", "false");
    overlay.classList.remove("hidden");
    overlay.classList.add("block");
    document.body.classList.add("overflow-hidden");

    requestAnimationFrame(() => {
      drawer.getBoundingClientRect();
      drawer.classList.remove("translate-x-full");
      drawer.classList.add("translate-x-0");
    });
  }

  function closeMobileMenu() {
    const { overlay, drawer } = getMobileEls();
    if (!overlay || !drawer) return;

    drawer.classList.remove("translate-x-0");
    drawer.classList.add("translate-x-full");

    const done = () => {
      drawer.removeEventListener("transitionend", done);
      overlay.classList.remove("block");
      overlay.classList.add("hidden");
      overlay.setAttribute("aria-hidden", "true");
      document.body.classList.remove("overflow-hidden");
    };
    drawer.addEventListener("transitionend", done, { once: true });
    setTimeout(done, 350);
  }

  document.addEventListener("click", (e) => {
    const openBtn = e.target.closest("[data-open]");
    if (openBtn) {
      const id = openBtn.getAttribute("data-open");
      e.preventDefault();
      if (id === MOBILE_ID) {
        openMobileMenu();
      } else {
        const mobileOverlay = document.getElementById(MOBILE_ID);
        if (mobileOverlay && !isHidden(mobileOverlay)) closeMobileMenu();
        openStandardModal(id);
      }
      return;
    }

    const closeBtn = e.target.closest("[data-close]");
    if (closeBtn) {
      const id = closeBtn.getAttribute("data-close");
      e.preventDefault();
      if (id === MOBILE_ID) closeMobileMenu();
      else closeStandardModal(id);
      return;
    }

    const backdrop = e.target.classList?.contains("modal-backdrop")
      ? e.target
      : null;
    if (backdrop) {
      if (backdrop.id === MOBILE_ID) closeMobileMenu();
      else closeStandardModal(backdrop);
    }
  });

  function initBurger() {
    const burger = document.getElementById("mobile-menu-btn");
    const overlay = document.getElementById(MOBILE_ID);
    if (!burger || !overlay) return;

    burger.addEventListener("click", (e) => {
      e.preventDefault();
      if (isHidden(overlay)) openMobileMenu();
      else closeMobileMenu();
    });

    const internalClose = document.getElementById("mobile-menu-close");
    internalClose?.addEventListener("click", (e) => {
      e.preventDefault();
      closeMobileMenu();
    });
  }

  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    const mobile = document.getElementById(MOBILE_ID);
    if (mobile && !isHidden(mobile)) {
      closeMobileMenu();
      return;
    }
    const visible = Array.from(document.querySelectorAll(".modal-backdrop"))
      .reverse()
      .find((el) => !isHidden(el) && el.id !== MOBILE_ID);
    if (visible) closeStandardModal(visible);
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initBurger);
  } else {
    initBurger();
  }
})();
