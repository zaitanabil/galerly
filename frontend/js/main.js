// Header Animation
let lastScrollY = window.scrollY;
const header = document.querySelector(".section-7");

window.addEventListener("scroll", () => {
  const currentScrollY = window.scrollY;

  if (currentScrollY <= 0) {
    // At the top, always grid-7
    header.classList.add("grid-7");
    header.classList.remove("undocked");
  } else if (currentScrollY > lastScrollY) {
    // Scrolling down
    header.classList.remove("grid-7");
    header.classList.add("undocked");
  } else {
    // Scrolling up
    header.classList.add("grid-7");
    header.classList.remove("undocked");
  }

  lastScrollY = currentScrollY;
});

//  image hover effect
document.querySelectorAll(".link-9").forEach((container) => {
  const circle = container.querySelector(".input-9");

  container.addEventListener("mousemove", (e) => {
    const rect = container.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    circle.style.left = `${x}px`;
    circle.style.top = `${y}px`;
    circle.style.opacity = 1;
  });

  container.addEventListener("mouseleave", () => {
    circle.style.opacity = 0;
  });
});

// Toggle mobile navigation
document.querySelectorAll(".main-10").forEach((toggleBtn) => {
  toggleBtn.addEventListener("click", () => {
    const nav = document.querySelector(".hero-6");
    if (nav) {
      nav.style.display = "block";
    }
  });
});

// Hide mobile nav on close button click
document.querySelectorAll(".text-6").forEach((closeBtn) => {
  closeBtn.addEventListener("click", () => {
    const nav = document.querySelector(".hero-6");
    if (nav) {
      nav.style.display = "none";
    }
  });
});

document.querySelectorAll(".item-9").forEach((switcher) => {
  switcher.addEventListener("click", () => {
    const target = document.querySelector(".section-6");

    if (target) {
      const isHidden =
        target.style.display === "none" ||
        getComputedStyle(target).display === "none";

      // Toggle display
      target.style.display = isHidden ? "block" : "none";

      // Toggle class
      switcher.classList.toggle("iqGQGM");
    }
  });
});




document.addEventListener("DOMContentLoaded", function () {
    const buttons = document.querySelectorAll('button.item-3[data-target]');

    function closeAllMenus() {
      buttons.forEach((btn) => {
        const targetSelector = btn.getAttribute("data-target");
        const target = document.querySelector(targetSelector);
        if (target) {
          target.style.display = "none";
          target.style.opacity = "0";
        }
        btn.setAttribute("data-state", "closed");
      });
    }

    buttons.forEach((button) => {
      const targetSelector = button.getAttribute("data-target");
      const target = document.querySelector(targetSelector);

      if (!target) return;

      button.addEventListener("click", function (event) {
        event.stopPropagation();

        const isOpen = button.getAttribute("data-state") === "open";
        closeAllMenus();

        if (!isOpen) {
          button.setAttribute("data-state", "open");
          target.style.display = "block";
          target.style.opacity = "1";
        }
      });
    });

    document.addEventListener("click", function (event) {
      const clickedInside = [...buttons].some((button) => {
        const targetSelector = button.getAttribute("data-target");
        const target = document.querySelector(targetSelector);
        return button.contains(event.target) || (target && target.contains(event.target));
      });

      if (!clickedInside) {
        closeAllMenus();
      }
    });
  });



  document.addEventListener("DOMContentLoaded", function () {
  const menuItems = document.querySelectorAll(".mobile-menu-item");

  menuItems.forEach((item) => {
    item.addEventListener("click", function (e) {
      e.stopPropagation();

      const subMenu = item.querySelector(".mobile-sub-menu");
      if (!subMenu) return;

      const isHidden = subMenu.classList.contains('d-none');

      // Close all submenus
      document.querySelectorAll(".mobile-sub-menu").forEach((menu) => {
        menu.classList.add('d-none');
      });

      // Toggle current submenu if it was hidden
      if (isHidden) {
        subMenu.classList.remove('d-none');
      }
    });
  });

  // Optional: close all when clicking outside
  document.addEventListener("click", function () {
    document.querySelectorAll(".mobile-sub-menu").forEach((menu) => {
      menu.classList.add('d-none');
    });
  });
});
