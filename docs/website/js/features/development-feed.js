async function initDevelopmentFeed() {
  if (!DocsElements.repoHealth && !DocsElements.commitFeed && !DocsElements.releaseFeed) {
    return;
  }

  const base = `https://api.github.com/repos/${DocsData.github.owner}/${DocsData.github.repo}`;

  try {
    const [repoResponse, commitsResponse, releasesResponse] = await Promise.all([
      fetch(base),
      fetch(`${base}/commits?per_page=4`),
      fetch(`${base}/releases?per_page=3`)
    ]);

    if (!repoResponse.ok || !commitsResponse.ok || !releasesResponse.ok) {
      throw new Error("GitHub API request failed");
    }

    const repo = await repoResponse.json();
    const commits = await commitsResponse.json();
    const releases = await releasesResponse.json();

    if (DocsElements.repoHealth) {
      DocsElements.repoHealth.innerHTML = `
        <div class="dev-status-grid">
          <div class="dev-status-item"><span class="dev-status-label">Default Branch</span><span class="dev-status-value">${escapeHtml(repo.default_branch || "main")}</span></div>
          <div class="dev-status-item"><span class="dev-status-label">Open Issues</span><span class="dev-status-value">${escapeHtml(String(repo.open_issues_count ?? "n/a"))}</span></div>
          <div class="dev-status-item"><span class="dev-status-label">Stars</span><span class="dev-status-value">${escapeHtml(String(repo.stargazers_count ?? "n/a"))}</span></div>
          <div class="dev-status-item"><span class="dev-status-label">Watchers</span><span class="dev-status-value">${escapeHtml(String(repo.subscribers_count ?? "n/a"))}</span></div>
        </div>
      `;
    }

    if (DocsElements.commitFeed) {
      DocsElements.commitFeed.innerHTML = `
        <div class="feed-list">
          ${commits
            .map((commit) => {
              const message = commit.commit?.message?.split("\n")[0] || "Commit";
              const author = commit.commit?.author?.name || "unknown";
              const date = commit.commit?.author?.date ? new Date(commit.commit.author.date).toLocaleString() : "n/a";
              return `
                <article class="feed-item">
                  <a href="${escapeHtml(commit.html_url)}" target="_blank" rel="noreferrer">${escapeHtml(message)}</a>
                  <div class="feed-meta">${escapeHtml(author)} · ${escapeHtml(date)}</div>
                </article>
              `;
            })
            .join("")}
        </div>
      `;
    }

    if (DocsElements.releaseFeed) {
      const content = releases.length
        ? releases
            .map((release) => {
              return `
                <article class="feed-item">
                  <a href="${escapeHtml(release.html_url)}" target="_blank" rel="noreferrer">${escapeHtml(release.name || release.tag_name || "Release")}</a>
                  <div class="feed-meta">${escapeHtml(release.tag_name || "untagged")} · ${escapeHtml(release.published_at ? new Date(release.published_at).toLocaleDateString() : "draft")}</div>
                </article>
              `;
            })
            .join("")
        : '<div class="empty-state">No published GitHub releases yet. The project currently signals release state through repository docs and tags.</div>';

      DocsElements.releaseFeed.innerHTML = `<div class="feed-list">${content}</div>`;
    }
  } catch (error) {
    const fallback = '<div class="empty-state">Live GitHub data could not be loaded right now. Use the repository links on this page for raw signals.</div>';
    if (DocsElements.repoHealth) {
      DocsElements.repoHealth.innerHTML = fallback;
    }
    if (DocsElements.commitFeed) {
      DocsElements.commitFeed.innerHTML = fallback;
    }
    if (DocsElements.releaseFeed) {
      DocsElements.releaseFeed.innerHTML = fallback;
    }
  }
}

