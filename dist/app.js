const DEMO_CODE = "271846";

const memories = [
  {
    title: "The light you carry",
    description: "I remember watching you step into your own light. The room felt brighter simply because you were in it.",
    note: "You have always been my brightest reflection.",
    type: "image",
    src: "assets/auditorium.jpg",
    alt: "A young woman at an event in an auditorium"
  },
  {
    title: "The joy you share",
    description: "The people around you are part of your story, too. I love seeing how easily you make a moment feel warm and unforgettable.",
    note: "May you always be surrounded by this kind of joy.",
    type: "image",
    src: "assets/friends.jpg",
    alt: "Three friends sharing a moment together"
  },
  {
    title: "Every tomorrow",
    description: "A celebration to hold close, and a reminder that there is so much more light ahead of you.",
    note: "Wherever life takes you, my love goes with you.",
    type: "video",
    src: "assets/celebration.mp4",
    poster: "assets/celebration-poster.jpg"
  }
];

const gate = document.getElementById("gate");
const experience = document.getElementById("experience");
const accessForm = document.getElementById("access-form");
const codeInput = document.getElementById("access-code");
const codeError = document.getElementById("code-error");
const fillCodeButton = document.getElementById("fill-code");
const overlay = document.getElementById("memory-overlay");
const dialog = overlay.querySelector(".memory-dialog");
const closeButton = overlay.querySelector(".dialog-close");
const memoryImage = document.getElementById("memory-image");
const memoryVideo = document.getElementById("memory-video");
const memoryTitle = document.getElementById("memory-title");
const memoryDescription = document.getElementById("memory-description");
const memoryNote = document.getElementById("memory-note");
const memoryProgress = document.getElementById("memory-progress");
const memoryAnnouncement = document.getElementById("memory-announcement");
const previousButton = document.getElementById("previous-memory");
const nextButton = document.getElementById("next-memory");
const jewelWrap = document.querySelector(".jewel-wrap");
const jewelCaption = document.querySelector(".jewel-caption");
const backgroundRegions = [document.querySelector(".site-header"), document.querySelector("main"), document.querySelector(".site-footer")];

let activeMemory = 0;
let returnFocus = null;
let touchStartX = null;
const revealedMemories = new Set();

function unlockExperience() {
  gate.hidden = true;
  experience.hidden = false;
  document.body.classList.remove("is-locked");
  codeError.textContent = "";
  try { sessionStorage.setItem("your-reflection-unlocked", "yes"); } catch (_) {}
  document.getElementById("experience-title").setAttribute("tabindex", "-1");
  document.getElementById("experience-title").focus({ preventScroll: true });
  window.scrollTo(0, 0);
  requestAnimationFrame(() => window.scrollTo(0, 0));
}

accessForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const value = codeInput.value.replace(/\D/g, "");
  if (value === DEMO_CODE) {
    unlockExperience();
  } else {
    codeError.textContent = value.length < 6 ? "Please enter all six digits." : "That code doesn't match. Please try again.";
    codeInput.setAttribute("aria-invalid", "true");
    codeInput.focus();
  }
});

codeInput.addEventListener("input", () => {
  codeInput.value = codeInput.value.replace(/\D/g, "").slice(0, 6);
  codeError.textContent = "";
  codeInput.removeAttribute("aria-invalid");
});

fillCodeButton.addEventListener("click", () => {
  codeInput.value = DEMO_CODE;
  codeInput.focus();
  codeError.textContent = "";
  codeInput.removeAttribute("aria-invalid");
});

try {
  if (sessionStorage.getItem("your-reflection-unlocked") === "yes") {
    gate.hidden = true;
    experience.hidden = false;
    document.body.classList.remove("is-locked");
  }
} catch (_) {}

function renderMemory(index) {
  activeMemory = index;
  const memory = memories[index];

  memoryVideo.pause();
  memoryVideo.hidden = true;
  memoryImage.hidden = true;
  memoryVideo.removeAttribute("src");
  memoryVideo.load();

  if (memory.type === "video") {
    memoryVideo.src = memory.src;
    memoryVideo.poster = memory.poster;
    memoryVideo.hidden = false;
    memoryVideo.load();
  } else {
    memoryImage.src = memory.src;
    memoryImage.alt = memory.alt;
    memoryImage.hidden = false;
  }

  memoryTitle.textContent = memory.title;
  memoryDescription.textContent = memory.description;
  memoryNote.textContent = memory.note;
  memoryAnnouncement.textContent = `Memory ${index + 1} of ${memories.length}: ${memory.title}`;

  memoryProgress.replaceChildren();
  memories.forEach((_, position) => {
    const bar = document.createElement("span");
    if (position <= index) bar.classList.add("active");
    memoryProgress.appendChild(bar);
  });
  memoryProgress.setAttribute("aria-label", `Memory ${index + 1} of ${memories.length}`);

  previousButton.disabled = index === 0;
  nextButton.innerHTML = index === memories.length - 1 ? "Return to bracelet <span aria-hidden=\"true\">→</span>" : "Next memory <span aria-hidden=\"true\">→</span>";

  revealedMemories.add(index);
  document.querySelectorAll(`[data-memory="${index}"]`).forEach((element) => element.classList.add("is-visited"));
  jewelCaption.textContent = revealedMemories.size === memories.length
    ? "ALL THREE MOMENTS ARE YOURS TO REVISIT"
    : `${revealedMemories.size} OF THREE MOMENTS REVEALED`;
}

function openMemory(index) {
  returnFocus = document.activeElement;
  renderMemory(index);
  overlay.hidden = false;
  backgroundRegions.forEach((region) => { region.inert = true; });
  document.body.classList.add("has-dialog");
  closeButton.focus();
}

function closeMemory() {
  memoryVideo.pause();
  overlay.hidden = true;
  backgroundRegions.forEach((region) => { region.inert = false; });
  document.body.classList.remove("has-dialog");
  if (returnFocus && typeof returnFocus.focus === "function") returnFocus.focus();
}

document.querySelectorAll("[data-memory]").forEach((button) => {
  button.addEventListener("click", () => openMemory(Number(button.dataset.memory)));
});
document.getElementById("begin-exploring").addEventListener("click", () => openMemory(0));
overlay.querySelectorAll("[data-close-memory]").forEach((button) => button.addEventListener("click", closeMemory));
previousButton.addEventListener("click", () => { if (activeMemory > 0) renderMemory(activeMemory - 1); });
nextButton.addEventListener("click", () => {
  if (activeMemory === memories.length - 1) closeMemory();
  else renderMemory(activeMemory + 1);
});

document.addEventListener("keydown", (event) => {
  if (overlay.hidden) return;
  if (event.key === "Escape") { closeMemory(); return; }
  if (event.target === memoryVideo || document.activeElement === memoryVideo) return;
  if (event.key === "ArrowRight" && activeMemory < memories.length - 1) { event.preventDefault(); renderMemory(activeMemory + 1); }
  if (event.key === "ArrowLeft" && activeMemory > 0) { event.preventDefault(); renderMemory(activeMemory - 1); }
  if (event.key === "Tab") {
    const focusable = [...dialog.querySelectorAll("button:not([disabled]), video[controls]")].filter((element) => !element.hidden);
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  }
});

const mediaPanel = overlay.querySelector(".memory-media-panel");
mediaPanel.addEventListener("touchstart", (event) => { touchStartX = event.changedTouches[0]?.screenX ?? null; }, { passive: true });
mediaPanel.addEventListener("touchend", (event) => {
  if (touchStartX === null || event.target.closest("video")) return;
  const distance = (event.changedTouches[0]?.screenX ?? touchStartX) - touchStartX;
  touchStartX = null;
  if (Math.abs(distance) < 70) return;
  if (distance < 0 && activeMemory < memories.length - 1) renderMemory(activeMemory + 1);
  if (distance > 0 && activeMemory > 0) renderMemory(activeMemory - 1);
}, { passive: true });

if (window.matchMedia("(hover: hover) and (pointer: fine)").matches) {
  jewelWrap.addEventListener("pointermove", (event) => {
    const bounds = jewelWrap.getBoundingClientRect();
    jewelWrap.style.setProperty("--pointer-x", `${((event.clientX - bounds.left) / bounds.width * 100).toFixed(1)}%`);
    jewelWrap.style.setProperty("--pointer-y", `${((event.clientY - bounds.top) / bounds.height * 100).toFixed(1)}%`);
  });
  jewelWrap.addEventListener("pointerleave", () => {
    jewelWrap.style.setProperty("--pointer-x", "50%");
    jewelWrap.style.setProperty("--pointer-y", "45%");
  });
}
