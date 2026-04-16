function buildWorkflowRail(railElement, detailElement) {
  if (!railElement || !detailElement) {
    return;
  }

  const activate = (key) => {
    const stage = DocsData.workflowStages.find((item) => item.key === key) || DocsData.workflowStages[0];
    const pills = stage.pills.map((pill) => `<span class="pill">${escapeHtml(pill)}</span>`).join("");

    detailElement.innerHTML = `
      <div class="stage-detail">
        <div class="eyebrow">${escapeHtml(stage.label)}</div>
        <h3>${escapeHtml(stage.title)}</h3>
        <p>${escapeHtml(stage.detail)}</p>
        <div class="stage-detail-meta">${pills}</div>
      </div>
    `;

    for (const node of railElement.querySelectorAll(".workflow-stage")) {
      node.classList.toggle("is-active", node.dataset.key === key);
    }
  };

  railElement.innerHTML = DocsData.workflowStages
    .map((stage) => {
      return `
        <button class="workflow-stage" type="button" data-key="${escapeHtml(stage.key)}">
          <div class="workflow-stage-top">
            <span class="workflow-stage-index">${escapeHtml(stage.label)}</span>
            <span class="pill">${escapeHtml(stage.title)}</span>
          </div>
          <div class="workflow-stage-summary">${escapeHtml(stage.summary)}</div>
        </button>
      `;
    })
    .join("");

  railElement.addEventListener("click", (event) => {
    const button = event.target.closest(".workflow-stage");
    if (!button) {
      return;
    }
    activate(button.dataset.key || DocsData.workflowStages[0].key);
  });

  activate(DocsData.workflowStages[0].key);
}

function initWorkflowVisuals() {
  buildWorkflowRail(DocsElements.workflowRail, DocsElements.workflowDetail);
  buildWorkflowRail(DocsElements.homeWorkflowRail, DocsElements.homeWorkflowDetail);
}

