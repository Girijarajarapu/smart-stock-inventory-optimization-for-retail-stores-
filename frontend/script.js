window.addEventListener("DOMContentLoaded", () => {

  /* ---------------- Sidebar Toggle ---------------- */
  function toggleSidebar() {
    const sidebar = document.getElementById("sidebar");
    const main = document.getElementById("main");
    const curLeft = window.getComputedStyle(sidebar).left;
    if (curLeft === "0px") {
      sidebar.style.left = "-260px";
      main.style.marginLeft = "0px";
    } else {
      sidebar.style.left = "0px";
      main.style.marginLeft = "260px";
    }
  }
  window.toggleSidebar = toggleSidebar;

  /* ---------------- Section Switching ---------------- */
  function showSection(pageID) {
    document.querySelectorAll(".page").forEach(sec => sec.classList.remove("active"));
    document.getElementById(pageID).classList.add("active");
  }
  window.showSection = showSection;

  /* ---------------- Search Filter ---------------- */
  const searchInput = document.getElementById("globalSearch");
  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      const q = e.target.value.trim().toLowerCase();
      document.querySelectorAll(".product").forEach(it => {
        const name = (it.dataset.name || it.textContent || "").toLowerCase();
        it.style.display = name.includes(q) ? "" : "none";
      });
    });
  }

  /* ---------------- Notifications ---------------- */
  const notifCountEl = document.getElementById("notifCount");
  const notifBtn = document.getElementById("notifBtn");
  let demoNotifCount = 3;

  function updateNotif() {
    if (!notifCountEl) return;
    if (demoNotifCount > 0) {
      notifCountEl.textContent = demoNotifCount;
      notifCountEl.classList.remove("hidden");
    } else {
      notifCountEl.classList.add("hidden");
    }
  }

  if (notifBtn) {
    notifBtn.addEventListener("click", () => {
      alert("You have " + demoNotifCount + " demo notifications.");
      demoNotifCount = 0;
      updateNotif();
    });
  }
  updateNotif();

  /* ---------------- Theme Toggle ---------------- */
  const themeBtn = document.getElementById("themeBtn");
  const THEME_KEY = "si_theme";

  function applyTheme(theme) {
    if (theme === "dark") document.documentElement.setAttribute("data-theme", "dark");
    else document.documentElement.setAttribute("data-theme", "light");
    localStorage.setItem(THEME_KEY, theme);
  }
  applyTheme(localStorage.getItem(THEME_KEY) || "light");

  if (themeBtn) {
    themeBtn.addEventListener("click", () => {
      const current = document.documentElement.getAttribute("data-theme");
      const newTheme = current === "dark" ? "light" : "dark";
      applyTheme(newTheme);
    });
  }

  /* ---------------- Product Click ---------------- */
  document.addEventListener('click', (ev) => {
    const p = ev.target.closest && ev.target.closest('.product');
    if (p) alert("Open product: " + (p.dataset.name || p.textContent));
  });

  /* ---------------- Fetch & Render Train Data ---------------- */
  async function fetchTrainData() {
    try {
      const response = await fetch("http://127.0.0.1:5000/api/train");
      const data = await response.json();

      const productList = document.getElementById("productList");
      const lowStockList = document.getElementById("lowStockList");
      if (!productList) return;

      productList.innerHTML = "";
      if (lowStockList) lowStockList.innerHTML = "";

      const LOW_THRESHOLD = 5;
      const BATCH_SIZE = 50;
      let index = 0;

      function renderBatch() {
        const batch = data.slice(index, index + BATCH_SIZE);
        batch.forEach(item => {
          const name = item.family || "Unnamed";
          const stock = item.sales || 0;

          const card = document.createElement("div");
          card.className = "card product";
          if (stock <= LOW_THRESHOLD) card.classList.add("low");
          card.dataset.name = name;
          card.innerText = `${name} — Sales: ${stock}`;
          productList.appendChild(card);

          if (stock <= LOW_THRESHOLD && lowStockList) {
            const lowCard = document.createElement("div");
            lowCard.className = "card product low";
            lowCard.dataset.name = name;
            lowCard.innerText = `${name} — Sales: ${stock} (low)`;
            lowStockList.appendChild(lowCard);
          }
        });

        index += BATCH_SIZE;
        if (index < data.length) setTimeout(renderBatch, 0);
      }

      renderBatch();

      // ---------------- Update Dashboard ----------------
      const totalProductsEl = document.querySelector("#dashboard .card:nth-child(1) .stat");
      const lowStockEl = document.querySelector("#dashboard .card:nth-child(2) .stat");
      const predictedOrdersEl = document.querySelector("#dashboard .card:nth-child(3) .stat");

      if (totalProductsEl) totalProductsEl.innerText = data.length;
      if (lowStockEl) lowStockEl.innerText = data.filter(item => (item.sales || 0) <= LOW_THRESHOLD).length;
      if (predictedOrdersEl) predictedOrdersEl.innerText = data.reduce((sum, item) => sum + (item.sales || 0), 0);

    } catch (err) {
      console.error("Error fetching train data:", err);
    }
  }

  /* ---------------- Fetch Test Data (optional) ---------------- */
  async function fetchTestData() {
    try {
      const response = await fetch("http://127.0.0.1:5000/api/test");
      const data = await response.json();
      console.log("Test Data (first 5 rows):", data.slice(0,5));
    } catch (err) {
      console.error("Error fetching test data:", err);
    }
  }

  fetchTrainData();
  fetchTestData();

});
