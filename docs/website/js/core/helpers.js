function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function pageLink(page, id = "") {
  return id ? `${page}#${id}` : page;
}

function groupedEntries() {
  const grouped = {};

  for (const group of DocsData.groups) {
    grouped[group] = [];
  }

  for (const entry of DocsData.entries) {
    if (!grouped[entry.group]) {
      grouped[entry.group] = [];
    }
    grouped[entry.group].push(entry);
  }

  return grouped;
}

function setNavOpen(nextState) {
  DocsState.navOpen = Boolean(nextState);
  DocsElements.body.classList.toggle("nav-open", DocsState.navOpen);
}

function currentHashId() {
  return window.location.hash ? window.location.hash.slice(1) : "";
}

function activeEntryId() {
  return currentHashId() || DocsState.currentSection || "";
}

function renderSidebarTabs() {
  if (!DocsElements.sidebarTabs) {
    return;
  }

  const filters = ["All", ...DocsData.groups];
  DocsElements.sidebarTabs.innerHTML = filters
    .map((group) => {
      const activeClass = DocsState.navGroupFilter === group ? " is-active" : "";
      return `<button class="sidebar-tab${activeClass}" type="button" data-group="${escapeHtml(group)}">${escapeHtml(group)}</button>`;
    })
    .join("");
}

function renderSidebarNav() {
  if (!DocsElements.sidebarNav) {
    return;
  }

  const groups = groupedEntries();
  const currentSectionId = activeEntryId();
  const filter = DocsState.navGroupFilter;
  const selectedGroups = filter === "All" ? Object.keys(groups) : [filter];

  DocsElements.sidebarNav.innerHTML = selectedGroups
    .filter((group) => groups[group] && groups[group].length)
    .map((group) => {
      const links = groups[group]
        .map((entry) => {
          const currentPageMatch = DocsState.currentPage === entry.page;
          const currentIdMatch = currentSectionId === entry.id;
          const activeClass = currentPageMatch && currentIdMatch ? " is-current" : "";
          return `
            <a class="sidebar-link${activeClass}" href="${pageLink(entry.page, entry.id)}">
              <span class="sidebar-link-title">${escapeHtml(entry.title)}</span>
              <span class="sidebar-link-hint">${escapeHtml(entry.hint)}</span>
            </a>
          `;
        })
        .join("");

      return `
        <section class="sidebar-group">
          <div class="sidebar-group-title">${escapeHtml(group)}</div>
          ${links}
        </section>
      `;
    })
    .join("");
}

function updateSidebar() {
  renderSidebarTabs();
  renderSidebarNav();
}

function initContactPopover() {
  if (!DocsElements.contactToggle || !DocsElements.contactPopover) {
    return;
  }

  const close = () => {
    DocsElements.contactToggle.setAttribute("aria-expanded", "false");
    DocsElements.contactPopover.hidden = true;
  };

  const open = () => {
    DocsElements.contactToggle.setAttribute("aria-expanded", "true");
    DocsElements.contactPopover.hidden = false;
  };

  DocsElements.contactToggle.addEventListener("click", () => {
    const isOpen = DocsElements.contactToggle.getAttribute("aria-expanded") === "true";
    if (isOpen) {
      close();
      return;
    }
    open();
  });

  document.addEventListener("click", (event) => {
    if (!DocsElements.contactPopover.contains(event.target) && !DocsElements.contactToggle.contains(event.target)) {
      close();
    }
  });
}

