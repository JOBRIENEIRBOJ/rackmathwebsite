const header = document.querySelector(".site-header");
const navToggle = document.querySelector(".nav-toggle");
const rackMathScriptUrl = new URL(
  document.currentScript?.getAttribute("src") || "script.js",
  window.location.href,
);
const rackMathRootUrl = new URL(".", rackMathScriptUrl);

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
    seo_intent: url.searchParams.get("intent") || "",
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

function shouldUseRackMathMotion() {
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  return !reduceMotion.matches;
}

function loadRackMathScript(src) {
  return new Promise((resolve, reject) => {
    const existingScript = Array.from(document.scripts).find((script) => script.src === src);

    if (existingScript?.dataset.rmLoaded === "true") {
      resolve();
      return;
    }

    if (existingScript) {
      existingScript.addEventListener("load", resolve, { once: true });
      existingScript.addEventListener("error", reject, { once: true });
      return;
    }

    const script = document.createElement("script");
    script.src = src;
    script.defer = true;
    script.dataset.rmMotionScript = "true";
    script.addEventListener(
      "load",
      () => {
        script.dataset.rmLoaded = "true";
        resolve();
      },
      { once: true },
    );
    script.addEventListener("error", reject, { once: true });
    document.head.append(script);
  });
}

function loadRackMathMotionScripts() {
  if (window.gsap && window.ScrollTrigger) {
    return Promise.resolve();
  }

  const gsapSrc = new URL("assets/vendor/gsap/gsap.min.js", rackMathRootUrl).href;
  const scrollTriggerSrc = new URL(
    "assets/vendor/gsap/ScrollTrigger.min.js",
    rackMathRootUrl,
  ).href;

  return loadRackMathScript(gsapSrc).then(() => loadRackMathScript(scrollTriggerSrc));
}

function initRackMathMotion() {
  if (!window.gsap || !window.ScrollTrigger || !shouldUseRackMathMotion()) return;

  const { gsap } = window;
  gsap.registerPlugin(window.ScrollTrigger);

  document.documentElement.classList.add("has-rm-motion");

  let scrollMeter = document.querySelector(".scroll-meter");

  if (!scrollMeter) {
    scrollMeter = document.createElement("div");
    scrollMeter.className = "scroll-meter";
    scrollMeter.setAttribute("aria-hidden", "true");
    document.body.prepend(scrollMeter);
  }

  const fromIfAny = (selector, vars, position, timeline) => {
    const targets = gsap.utils.toArray(selector);
    if (!targets.length) return timeline;

    if (timeline) {
      timeline.from(targets, vars, position);
      return timeline;
    }

    gsap.from(targets, vars);
    return null;
  };

  const toIfAny = (selector, vars) => {
    const targets = gsap.utils.toArray(selector);
    if (!targets.length) return;
    gsap.to(targets, vars);
  };

  gsap.to(scrollMeter, {
    scaleX: 1,
    ease: "none",
    scrollTrigger: {
      trigger: document.documentElement,
      start: "top top",
      end: "bottom bottom",
      scrub: 0.2,
    },
  });

  if (header) {
    window.ScrollTrigger.create({
      start: "top -72px",
      end: 99999,
      toggleClass: {
        targets: header,
        className: "is-scrolled",
      },
    });
  }

  const heroTimeline = gsap.timeline({
    defaults: {
      duration: 0.78,
      ease: "power3.out",
    },
  });

  fromIfAny(
    ".site-header",
    {
      autoAlpha: 0,
      y: -18,
      duration: 0.56,
    },
    undefined,
    heroTimeline,
  );
  fromIfAny(
    ".hero-copy > *, .page-hero > *",
    {
      autoAlpha: 0,
      y: 34,
      stagger: 0.08,
    },
    "-=0.18",
    heroTimeline,
  );
  fromIfAny(
    ".hero-app-frame-shell",
    {
      autoAlpha: 0,
      y: 42,
      rotate: 1.2,
    },
    "-=0.56",
    heroTimeline,
  );
  fromIfAny(
    ".trust-row span",
    {
      autoAlpha: 0,
      y: 12,
      stagger: 0.06,
      duration: 0.44,
    },
    "-=0.42",
    heroTimeline,
  );

  toIfAny(".hero-app-frame-shell", {
    y: -26,
    ease: "none",
    scrollTrigger: {
      trigger: ".hero",
      start: "top top",
      end: "bottom top",
      scrub: true,
    },
  });

  const revealSelector = [
    ".section-heading",
    ".section-copy",
    ".stat-grid > div",
    ".feature-card",
    ".price-card",
    ".faq-list details",
    ".final-cta > *",
    ".detail-row",
    ".about-card",
    ".about-post > *",
    ".story-band > *",
    ".blog-post-content > *",
    ".blog-post-nav a",
    ".archive-list > *",
    ".tool-workspace > *",
    ".tool-panel",
    ".tool-context",
    ".rm-free-calculator-heading",
    ".rm-free-calculator-grid > *",
    ".seo-content-grid > *",
    ".program-roadmap > *",
    ".program-builder-list > *",
    ".evidence-section > *",
    ".workout-day",
    ".exercise-guide-panel > *",
    ".exercise-meta-list > *",
    ".exercise-cue-list > *",
    ".feature-list li",
    ".table-section table",
  ].join(", ");

  gsap.utils.toArray(revealSelector).forEach((element) => {
    gsap.from(element, {
      autoAlpha: 0,
      y: 34,
      duration: 0.72,
      ease: "power3.out",
      scrollTrigger: {
        trigger: element,
        start: "top 84%",
        toggleActions: "play none none reverse",
      },
    });
  });

  gsap.utils.toArray(".tool-grid, .related-pages, .exercise-summary-grid").forEach((grid) => {
    const items = grid.children;
    if (!items.length) return;

    gsap.from(items, {
      autoAlpha: 0,
      y: 28,
      duration: 0.62,
      ease: "power3.out",
      stagger: 0.055,
      scrollTrigger: {
        trigger: grid,
        start: "top 82%",
      },
    });
  });

  gsap.utils.toArray(".workflow-list li").forEach((item, index) => {
    const shot = item.querySelector(".workflow-shot");

    gsap.from(item, {
      autoAlpha: 0,
      x: index % 2 === 0 ? -34 : 34,
      duration: 0.74,
      ease: "power3.out",
      scrollTrigger: {
        trigger: item,
        start: "top 82%",
      },
    });

    window.ScrollTrigger.create({
      trigger: item,
      start: "top 58%",
      end: "bottom 46%",
      toggleClass: {
        targets: item,
        className: "is-current",
      },
    });

    if (shot) {
      gsap.to(shot, {
        y: index % 2 === 0 ? -14 : 14,
        rotate: index % 2 === 0 ? 0.8 : -0.8,
        ease: "none",
        scrollTrigger: {
          trigger: item,
          start: "top bottom",
          end: "bottom top",
          scrub: true,
        },
      });
    }
  });

  toIfAny(".final-cta", {
    backgroundPosition: "100% 50%",
    ease: "none",
    scrollTrigger: {
      trigger: ".final-cta",
      start: "top bottom",
      end: "bottom top",
      scrub: true,
    },
  });

  window.addEventListener("load", () => {
    window.ScrollTrigger.refresh();
  });
}

if (shouldUseRackMathMotion()) {
  loadRackMathMotionScripts().then(initRackMathMotion).catch(() => {});
}
