const RawPopup = (() => {
  let backdrop = null;
  let titleNode = null;
  let metaNode = null;
  let bodyNode = null;
  let rawLinkNode = null;
  let repoLinkNode = null;
  let bound = false;

  function ensureViewer() {
    if (backdrop) {
      return;
    }

    backdrop = document.createElement("div");
    backdrop.className = "raw-viewer-backdrop";
    backdrop.hidden = true;
    backdrop.innerHTML = `
      <div class="raw-viewer-window" role="dialog" aria-modal="true" aria-label="Repository file preview">
        <div class="raw-viewer-head">
          <div>
            <div class="raw-viewer-title">Repository File</div>
            <div class="raw-viewer-meta"></div>
          </div>
          <button class="raw-viewer-close" type="button" aria-label="Close repository file preview">Close</button>
        </div>
        <div class="raw-viewer-actions">
          <a class="raw-viewer-link" data-role="raw" href="#" target="_blank" rel="noreferrer">Open Raw</a>
          <a class="raw-viewer-link" data-role="repo" href="#" target="_blank" rel="noreferrer">View On GitHub</a>
        </div>
        <div class="raw-viewer-body is-plain">Loading...</div>
      </div>
    `;

    document.body.appendChild(backdrop);
    titleNode = backdrop.querySelector(".raw-viewer-title");
    metaNode = backdrop.querySelector(".raw-viewer-meta");
    bodyNode = backdrop.querySelector(".raw-viewer-body");
    rawLinkNode = backdrop.querySelector('[data-role="raw"]');
    repoLinkNode = backdrop.querySelector('[data-role="repo"]');

    backdrop.addEventListener("click", (event) => {
      if (event.target === backdrop) {
        close();
      }
    });

    backdrop.querySelector(".raw-viewer-close")?.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      close();
    });
  }

  function close() {
    if (!backdrop) {
      return;
    }

    document.body.classList.remove("raw-viewer-open");
    backdrop.hidden = true;
  }

  function renderPlain(text) {
    bodyNode.className = "raw-viewer-body is-plain";
    bodyNode.textContent = text;
  }

  async function renderMarkdown(text) {
    try {
      const response = await fetch("https://api.github.com/markdown", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/vnd.github+json"
        },
        body: JSON.stringify({
          text,
          mode: "gfm",
          context: `${DocsData.github.owner}/${DocsData.github.repo}`
        })
      });

      if (!response.ok) {
        throw new Error(`GitHub markdown API returned ${response.status}`);
      }

      return await response.text();
    } catch (error) {
      return renderMarkdownFallback(text);
    }
  }

  function renderMarkdownFallback(text) {
    const codeBlocks = [];
    const source = text.replace(/```([\w-]*)\n([\s\S]*?)```/g, (_match, language, code) => {
      const token = `__RAW_CODE_BLOCK_${codeBlocks.length}__`;
      codeBlocks.push(
        `<pre class="raw-md-code"><code${language ? ` data-lang="${escapeHtml(language)}"` : ""}>${escapeHtml(code.trimEnd())}</code></pre>`
      );
      return token;
    });

    const lines = source.split(/\r?\n/);
    const blocks = [];

    for (let index = 0; index < lines.length; ) {
      const line = lines[index];

      if (!line.trim()) {
        index += 1;
        continue;
      }

      const heading = line.match(/^(#{1,6})\s+(.*)$/);
      if (heading) {
        const level = heading[1].length;
        blocks.push(`<h${level}>${applyInlineMarkdown(heading[2])}</h${level}>`);
        index += 1;
        continue;
      }

      if (/^\s*[-*+]\s+/.test(line)) {
        const items = [];
        while (index < lines.length && /^\s*[-*+]\s+/.test(lines[index])) {
          items.push(`<li>${applyInlineMarkdown(lines[index].replace(/^\s*[-*+]\s+/, ""))}</li>`);
          index += 1;
        }
        blocks.push(`<ul>${items.join("")}</ul>`);
        continue;
      }

      if (/^\s*\d+\.\s+/.test(line)) {
        const items = [];
        while (index < lines.length && /^\s*\d+\.\s+/.test(lines[index])) {
          items.push(`<li>${applyInlineMarkdown(lines[index].replace(/^\s*\d+\.\s+/, ""))}</li>`);
          index += 1;
        }
        blocks.push(`<ol>${items.join("")}</ol>`);
        continue;
      }

      if (/^>\s?/.test(line)) {
        const quoteLines = [];
        while (index < lines.length && /^>\s?/.test(lines[index])) {
          quoteLines.push(applyInlineMarkdown(lines[index].replace(/^>\s?/, "")));
          index += 1;
        }
        blocks.push(`<blockquote><p>${quoteLines.join("<br>")}</p></blockquote>`);
        continue;
      }

      const paragraph = [];
      while (
        index < lines.length &&
        lines[index].trim() &&
        !/^(#{1,6})\s+/.test(lines[index]) &&
        !/^\s*[-*+]\s+/.test(lines[index]) &&
        !/^\s*\d+\.\s+/.test(lines[index]) &&
        !/^>\s?/.test(lines[index])
      ) {
        paragraph.push(lines[index]);
        index += 1;
      }
      blocks.push(`<p>${applyInlineMarkdown(paragraph.join(" "))}</p>`);
    }

    let html = blocks.join("");
    for (let index = 0; index < codeBlocks.length; index += 1) {
      html = html.replace(`__RAW_CODE_BLOCK_${index}__`, codeBlocks[index]);
    }
    return html;
  }

  function applyInlineMarkdown(text) {
    return escapeHtml(text)
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_match, label, href) => {
        const url = /^(https?:|mailto:)/i.test(href) ? href : githubBlob(href);
        return `<a href="${escapeHtml(url)}" target="_blank" rel="noreferrer">${escapeHtml(label)}</a>`;
      })
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/\*([^*]+)\*/g, "<em>$1</em>");
  }

  async function open(link) {
    ensureViewer();

    const rawHref = link.getAttribute("href") || "";
    const repoHref = link.dataset.repoHref || rawHref;
    const title = link.dataset.rawTitle || "Repository File";
    const pathLabel = link.dataset.rawPath || rawHref;
    const isMarkdown = /\.md(?:own)?$/i.test(pathLabel);

    titleNode.textContent = title;
    metaNode.textContent = `${pathLabel} | fetching raw file`;
    renderPlain("Loading file preview...");
    rawLinkNode.href = rawHref;
    repoLinkNode.href = repoHref;
    document.body.classList.add("raw-viewer-open");
    backdrop.hidden = false;

    try {
      const response = await fetch(rawHref);
      if (!response.ok) {
        throw new Error(`GitHub returned ${response.status}`);
      }

      const text = await response.text();
      metaNode.textContent = `${pathLabel} | inline preview`;

      if (isMarkdown) {
        bodyNode.className = "raw-viewer-body is-markdown";
        bodyNode.innerHTML = await renderMarkdown(text);
      } else {
        renderPlain(text.trimEnd());
      }

      bodyNode.scrollTop = 0;
    } catch (error) {
      metaNode.textContent = `${pathLabel} | preview unavailable`;
      renderPlain(`Unable to load this file preview.\n\n${error.message || "Unknown error."}`);
    }
  }

  function bind() {
    if (bound) {
      return;
    }

    document.addEventListener("click", (event) => {
      const link = event.target.closest("a[data-raw-viewer]");
      if (!link) {
        return;
      }

      event.preventDefault();
      void open(link);
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        close();
      }
    });

    bound = true;
  }

  return { bind, close };
})();
