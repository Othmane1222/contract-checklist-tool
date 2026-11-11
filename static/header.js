// Sticky header: compact with a shadow after scrolling; on phones, hides on scroll down and returns on scroll up.
(function () {
  var header = document.querySelector(".site-header");
  if (!header) return;

  var THRESHOLD = 8;
  var phone = window.matchMedia("(max-width: 719px)");
  var lastY = window.scrollY;
  var ticking = false;

  function update() {
    var y = window.scrollY;
    header.classList.toggle("is-scrolled", y > THRESHOLD);

    var delta = y - lastY;
    if (Math.abs(delta) >= THRESHOLD) {
      var hide = phone.matches && delta > 0 && y > header.offsetHeight && !header.contains(document.activeElement);
      header.classList.toggle("is-hidden", hide);
      lastY = y;
    }
    if (y <= THRESHOLD) header.classList.remove("is-hidden");
    ticking = false;
  }

  window.addEventListener(
    "scroll",
    function () {
      if (!ticking) {
        ticking = true;
        window.requestAnimationFrame(update);
      }
    },
    { passive: true },
  );

  header.addEventListener("focusin", function () {
    header.classList.remove("is-hidden");
  });

  if (phone.addEventListener) {
    phone.addEventListener("change", function () {
      header.classList.remove("is-hidden");
    });
  }

  update();
})();