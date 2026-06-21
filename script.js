const header = document.querySelector(".site-header");
const navToggle = document.querySelector(".nav-toggle");
const rackMathScriptUrl = new URL(
  document.currentScript?.getAttribute("src") || "script.js",
  window.location.href,
);
const rackMathRootUrl = new URL(".", rackMathScriptUrl);
const rackMathDropdownTimelines = new WeakMap();

function closeRackMathDropdown(dropdown, immediate = false) {
  const trigger = dropdown.querySelector(".nav-dropdown-trigger");
  const timeline = rackMathDropdownTimelines.get(dropdown);

  trigger?.setAttribute("aria-expanded", "false");

  if (timeline && !immediate && timeline.progress() > 0) {
    timeline.timeScale(1.2).reverse();
    return;
  }

  timeline?.progress(0).pause();
  dropdown.classList.remove("is-open");
}

function closeRackMathDropdowns(exceptDropdown = null, immediate = false) {
  document.querySelectorAll(".nav-dropdown.is-open").forEach((dropdown) => {
    if (dropdown === exceptDropdown) return;
    closeRackMathDropdown(dropdown, immediate);
  });
}

function openRackMathDropdown(dropdown) {
  const trigger = dropdown.querySelector(".nav-dropdown-trigger");
  const timeline = rackMathDropdownTimelines.get(dropdown);

  closeRackMathDropdowns(dropdown);
  dropdown.classList.add("is-open");
  trigger?.setAttribute("aria-expanded", "true");

  if (timeline) {
    timeline.timeScale(1).play();
  }
}

function toggleRackMathDropdown(dropdown) {
  if (dropdown.classList.contains("is-open")) {
    closeRackMathDropdown(dropdown);
    return;
  }

  openRackMathDropdown(dropdown);
}

if (header && navToggle) {
  navToggle.addEventListener("click", () => {
    const isOpen = header.classList.toggle("is-open");
    navToggle.setAttribute("aria-expanded", String(isOpen));
  });
}

document.querySelectorAll(".nav-dropdown").forEach((dropdown) => {
  const trigger = dropdown.querySelector(".nav-dropdown-trigger");
  if (!trigger) return;

  dropdown.dataset.rmMenu = trigger.textContent.trim().toLowerCase().replace(/\s+/g, "-");
  trigger.setAttribute("aria-haspopup", "true");
  trigger.setAttribute("aria-expanded", "false");

  trigger.addEventListener("click", (event) => {
    event.stopPropagation();
    if (
      rackMathDropdownTimelines.has(dropdown) &&
      window.matchMedia("(min-width: 901px)").matches
    ) {
      openRackMathDropdown(dropdown);
      return;
    }

    toggleRackMathDropdown(dropdown);
  });
});

document.addEventListener("click", (event) => {
  document.querySelectorAll(".nav-dropdown.is-open").forEach((dropdown) => {
    if (dropdown.contains(event.target)) return;
    closeRackMathDropdown(dropdown);
  });
});

document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape") return;
  closeRackMathDropdowns(null, true);
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

function prepareRackMathHeroMasks() {
  document.querySelectorAll(".hero h1, .page-hero h1").forEach((heading) => {
    if (heading.dataset.rmTextMasked === "true") return;

    const maskFragment = document.createDocumentFragment();

    const appendMaskedWords = (text, target) => {
      text.split(/(\s+)/).forEach((token) => {
        if (!token) return;

        if (/^\s+$/.test(token)) {
          target.append(document.createTextNode(token));
          return;
        }

        const wordMask = document.createElement("span");
        const wordInner = document.createElement("span");
        wordMask.className = "rm-text-mask-word";
        wordInner.className = "rm-text-mask-inner";
        wordInner.textContent = token;
        wordMask.append(wordInner);
        target.append(wordMask);
      });
    };

    Array.from(heading.childNodes).forEach((node) => {
      if (node.nodeType === Node.TEXT_NODE) {
        appendMaskedWords(node.textContent || "", maskFragment);
        return;
      }

      if (node.nodeType !== Node.ELEMENT_NODE) return;

      const element = node;
      const clone = document.createElement(element.tagName.toLowerCase());

      Array.from(element.attributes).forEach((attribute) => {
        clone.setAttribute(attribute.name, attribute.value);
      });

      appendMaskedWords(element.textContent || "", clone);
      maskFragment.append(clone);
    });

    heading.replaceChildren(maskFragment);
    heading.dataset.rmTextMasked = "true";
  });
}

function initRackMathDropdownMotion(gsap) {
  if (!window.matchMedia("(min-width: 901px)").matches) return;

  gsap.utils.toArray(".nav-dropdown").forEach((dropdown) => {
    const menu = dropdown.querySelector(".nav-dropdown-menu");
    const trigger = dropdown.querySelector(".nav-dropdown-trigger");
    const links = menu ? gsap.utils.toArray("a", menu) : [];

    if (!menu || !trigger || rackMathDropdownTimelines.has(dropdown)) return;

    gsap.set(menu, {
      autoAlpha: 0,
      y: -10,
      clipPath: "inset(0% 0% 100% 0%)",
      transformOrigin: "top center",
    });
    gsap.set(links, {
      autoAlpha: 0,
      y: -8,
    });

    const timeline = gsap
      .timeline({
        paused: true,
        defaults: {
          ease: "expo.out",
        },
        onReverseComplete: () => {
          dropdown.classList.remove("is-open");
        },
      })
      .to(menu, {
        autoAlpha: 1,
        y: 0,
        clipPath: "inset(0% 0% 0% 0%)",
        duration: 0.34,
      })
      .to(
        links,
        {
          autoAlpha: 1,
          y: 0,
          duration: 0.2,
          ease: "power2.out",
          stagger: 0.018,
        },
        "-=0.2",
      );

    rackMathDropdownTimelines.set(dropdown, timeline);

    dropdown.addEventListener("mouseenter", () => openRackMathDropdown(dropdown));
    dropdown.addEventListener("mouseleave", () => closeRackMathDropdown(dropdown));
    dropdown.addEventListener("focusout", (event) => {
      if (event.relatedTarget instanceof Node && dropdown.contains(event.relatedTarget)) return;
      closeRackMathDropdown(dropdown);
    });
  });
}

function initRackMathMotion() {
  if (!window.gsap || !window.ScrollTrigger || !shouldUseRackMathMotion()) return;

  const { gsap } = window;
  gsap.registerPlugin(window.ScrollTrigger);

  document.documentElement.classList.add("has-rm-motion");
  prepareRackMathHeroMasks();
  initRackMathDropdownMotion(gsap);

  const heroMaskTargets = gsap.utils.toArray(
    ".hero h1 .rm-text-mask-inner, .page-hero h1 .rm-text-mask-inner",
  );

  document.documentElement.classList.remove("has-rm-hero-mask");
  if (heroMaskTargets.length) {
    gsap.set(heroMaskTargets, { clearProps: "transform" });
    gsap.set(heroMaskTargets, {
      yPercent: 112,
      y: 0,
      rotate: 1.6,
      transformOrigin: "left bottom",
    });
  }

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
    ".hero-copy > :not(h1), .page-hero > :not(h1)",
    {
      autoAlpha: 0,
      y: 34,
      stagger: 0.08,
    },
    "-=0.18",
    heroTimeline,
  );
  if (heroMaskTargets.length) {
    heroTimeline.to(
      heroMaskTargets,
      {
        yPercent: 0,
        rotate: 0,
        duration: 0.92,
        ease: "power4.out",
        stagger: 0.035,
      },
      "-=0.5",
    );
  }
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
  prepareRackMathHeroMasks();
  document.documentElement.classList.add("has-rm-hero-mask");
  loadRackMathMotionScripts()
    .then(initRackMathMotion)
    .catch(() => {
      document.documentElement.classList.remove("has-rm-hero-mask");
    });
}
