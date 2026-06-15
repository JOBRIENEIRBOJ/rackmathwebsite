const header = document.querySelector(".site-header");
const navToggle = document.querySelector(".nav-toggle");

if (header && navToggle) {
  navToggle.addEventListener("click", () => {
    const isOpen = header.classList.toggle("is-open");
    navToggle.setAttribute("aria-expanded", String(isOpen));
  });
}

document.querySelectorAll(".nav-dropdown").forEach((dropdown) => {
  const trigger = dropdown.querySelector(".nav-dropdown-trigger");
  if (!trigger) return;

  trigger.setAttribute("aria-haspopup", "true");
  trigger.setAttribute("aria-expanded", "false");

  trigger.addEventListener("click", (event) => {
    event.stopPropagation();
    const isOpen = dropdown.classList.toggle("is-open");
    trigger.setAttribute("aria-expanded", String(isOpen));
  });
});

document.addEventListener("click", (event) => {
  document.querySelectorAll(".nav-dropdown.is-open").forEach((dropdown) => {
    if (dropdown.contains(event.target)) return;
    dropdown.classList.remove("is-open");
    dropdown.querySelector(".nav-dropdown-trigger")?.setAttribute("aria-expanded", "false");
  });
});

document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape") return;
  document.querySelectorAll(".nav-dropdown.is-open").forEach((dropdown) => {
    dropdown.classList.remove("is-open");
    dropdown.querySelector(".nav-dropdown-trigger")?.setAttribute("aria-expanded", "false");
  });
});

function rackMathContentGroup(pathname) {
  const firstSegment = pathname.split("/").filter(Boolean)[0] || "home";
  return firstSegment.replace(/\.html$/, "");
}

function rackMathLinkPayload(link) {
  const url = new URL(link.href, window.location.href);
  return {
    destination: url.href,
    destination_path: url.pathname,
    label: link.textContent.trim(),
    source_page: window.location.pathname,
    content_group: rackMathContentGroup(window.location.pathname),
    seo_source: url.searchParams.get("source") || "",
    seo_tool: url.searchParams.get("tool") || "",
    seo_template: url.searchParams.get("template") || "",
    seo_program: url.searchParams.get("program") || "",
    seo_persona: url.searchParams.get("persona") || "",
    seo_feature: url.searchParams.get("feature") || "",
  };
}

function trackRackMathEvent(eventName, payload = {}) {
  const eventPayload = {
    event: eventName,
    source_page: window.location.pathname,
    content_group: rackMathContentGroup(window.location.pathname),
    timestamp: new Date().toISOString(),
    ...payload,
  };

  window.dataLayer = window.dataLayer || [];
  window.dataLayer.push(eventPayload);
  window.dispatchEvent(new CustomEvent(`rackmath:${eventName}`, { detail: eventPayload }));

  if (typeof window.gtag === "function") {
    const { event, ...gtagPayload } = eventPayload;
    window.gtag("event", event, gtagPayload);
  }

  if (typeof window.plausible === "function") {
    window.plausible(eventName, { props: eventPayload });
  }

  return eventPayload;
}

window.RackMathAnalytics = {
  track: trackRackMathEvent,
  contentGroup: rackMathContentGroup,
};

document.querySelectorAll('a[href^="https://www.rackmath.app"], [data-rm-app-link]').forEach((link) => {
  link.addEventListener("click", () => {
    const payload = rackMathLinkPayload(link);
    const primaryEvent = link.dataset.rmEvent || (link.textContent.toLowerCase().includes("try free") ? "signup_started" : "app_deeplink_clicked");

    if (primaryEvent !== "app_deeplink_clicked") {
      trackRackMathEvent(primaryEvent, payload);
    }

    trackRackMathEvent("app_deeplink_clicked", {
      ...payload,
      primary_event: primaryEvent,
    });
  });
});
