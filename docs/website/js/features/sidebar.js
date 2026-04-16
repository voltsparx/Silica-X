function initSidebar() {
  updateSidebar();

  DocsElements.sidebarTabs?.addEventListener("click", (event) => {
    const button = event.target.closest("[data-group]");
    if (!button) {
      return;
    }

    DocsState.navGroupFilter = button.dataset.group || "All";
    updateSidebar();
  });

  DocsElements.menuToggle?.addEventListener("click", () => {
    setNavOpen(!DocsState.navOpen);
  });

  DocsElements.sidebarBackdrop?.addEventListener("click", () => {
    setNavOpen(false);
  });

  window.addEventListener("hashchange", () => {
    updateSidebar();
  });

  document.addEventListener("click", (event) => {
    const link = event.target.closest(".sidebar-link");
    if (!link) {
      return;
    }
    setNavOpen(false);
  });
}

