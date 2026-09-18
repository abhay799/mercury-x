const toggle = document.querySelector(".nav-toggle");
const navigation = document.querySelector(".site-nav");
const header = document.querySelector("[data-header]");

function setMenu(open) {
  toggle?.setAttribute("aria-expanded", String(open));
  navigation?.classList.toggle("is-open", open);
}

toggle?.addEventListener("click", () => {
  setMenu(toggle.getAttribute("aria-expanded") !== "true");
});

navigation?.addEventListener("click", (event) => {
  if (event.target.closest("a")) setMenu(false);
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") setMenu(false);
});

const observer = new IntersectionObserver(
  ([entry]) => header?.classList.toggle("is-condensed", !entry.isIntersecting),
  { threshold: 0.05 },
);

const hero = document.querySelector(".hero");
if (hero) observer.observe(hero);
