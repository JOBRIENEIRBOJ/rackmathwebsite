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
    navToggle.setAttribute("aria-label", isOpen ? "Close navigation" : "Open navigation");
    if (document.body.classList.contains("home-page")) {
      document.body.classList.toggle("rm-nav-open", isOpen);
    }
  });

  header.querySelectorAll(".site-nav a, .header-cta").forEach((link) => {
    link.addEventListener("click", () => {
      header.classList.remove("is-open");
      navToggle.setAttribute("aria-expanded", "false");
      navToggle.setAttribute("aria-label", "Open navigation");
      document.body.classList.remove("rm-nav-open");
    });
  });
}

function initRackMathAnchorNavigation() {
  if (!document.body.classList.contains("home-page")) return;

  document.addEventListener("click", (event) => {
    if (
      event.defaultPrevented ||
      event.button !== 0 ||
      event.metaKey ||
      event.ctrlKey ||
      event.shiftKey ||
      event.altKey
    ) {
      return;
    }

    const link = event.target instanceof Element ? event.target.closest("a[href]") : null;
    if (!link) return;

    const url = new URL(link.href, window.location.href);
    if (
      !url.hash ||
      url.origin !== window.location.origin ||
      url.pathname !== window.location.pathname ||
      url.search !== window.location.search
    ) {
      return;
    }

    const target = document.getElementById(decodeURIComponent(url.hash.slice(1)));
    if (!target) return;

    const flowTrigger = window.ScrollTrigger?.getById("rm-flow-pin");
    if (
      !flowTrigger ||
      !Number.isFinite(flowTrigger.start) ||
      !Number.isFinite(flowTrigger.end)
    ) {
      return;
    }

    const currentY = window.scrollY;
    const scrollMargin = Number.parseFloat(window.getComputedStyle(target).scrollMarginTop) || 0;
    const targetY = currentY + target.getBoundingClientRect().top - scrollMargin;
    const edgeTolerance = 2;
    const movingPastPin =
      targetY >= flowTrigger.end - edgeTolerance &&
      currentY < flowTrigger.end - edgeTolerance;
    const movingBeforePin =
      targetY <= flowTrigger.start + edgeTolerance &&
      currentY > flowTrigger.start + edgeTolerance;

    if (!movingPastPin && !movingBeforePin) return;

    event.preventDefault();

    const root = document.documentElement;
    const previousScrollBehavior = root.style.scrollBehavior;
    const targetScrollTop = () =>
      Math.max(0, window.scrollY + target.getBoundingClientRect().top - scrollMargin);
    const syncScrollTrigger = () => window.ScrollTrigger?.update(true);
    const pinBoundary = movingPastPin
      ? Math.ceil(flowTrigger.end + edgeTolerance)
      : Math.max(0, Math.floor(flowTrigger.start - edgeTolerance));

    root.style.scrollBehavior = "auto";
    window.scrollTo({ top: pinBoundary, behavior: "auto" });
    syncScrollTrigger();
    window.scrollTo({ top: targetScrollTop(), behavior: "auto" });
    syncScrollTrigger();

    if (window.location.hash === url.hash) {
      window.history.replaceState(null, "", url.hash);
    } else {
      window.history.pushState(null, "", url.hash);
    }

    window.requestAnimationFrame(() => {
      window.scrollTo({ top: targetScrollTop(), behavior: "auto" });
      syncScrollTrigger();
      root.style.scrollBehavior = previousScrollBehavior;

      const focusTarget = target.querySelector("h1, h2, h3") || target;
      if (!focusTarget.hasAttribute("tabindex")) {
        focusTarget.setAttribute("tabindex", "-1");
      }
      focusTarget.focus({ preventScroll: true });
    });
  });
}

initRackMathAnchorNavigation();

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

  if (header?.classList.contains("is-open") && navToggle) {
    header.classList.remove("is-open");
    navToggle.setAttribute("aria-expanded", "false");
    navToggle.setAttribute("aria-label", "Open navigation");
    document.body.classList.remove("rm-nav-open");
    navToggle.focus();
  }
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

const rackMathRemoteEventNames = Object.freeze({
  page_viewed: "seo_page_viewed",
  tool_completed: "seo_tool_completed",
  app_deeplink_clicked: "seo_app_link_clicked",
  template_started: "seo_template_link_clicked",
  signup_started: "seo_signup_link_clicked",
});

const rackMathRemotePropertyKeys = new Set([
  "source_page",
  "content_group",
  "destination_path",
  "label",
  "primary_event",
  "page_title",
  "tool",
]);

function rackMathAnalyticsConfig() {
  const config = window.RACKMATH_ANALYTICS_CONFIG;
  if (!config?.endpoint || !config?.anonKey) return null;

  try {
    const endpoint = new URL(config.endpoint, window.location.href);
    if (endpoint.protocol !== "https:" && endpoint.hostname !== "localhost") return null;
    return { endpoint: endpoint.href, anonKey: String(config.anonKey) };
  } catch {
    return null;
  }
}

function rackMathAnonymousId() {
  const storageKey = "rackmath_marketing_analytics_id";

  try {
    const stored = window.sessionStorage.getItem(storageKey);
    if (stored) return stored;

    const randomId =
      typeof window.crypto?.randomUUID === "function"
        ? window.crypto.randomUUID()
        : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
    const anonymousId = `web_${randomId}`;
    window.sessionStorage.setItem(storageKey, anonymousId);
    return anonymousId;
  } catch {
    return `web_${Date.now()}-${Math.random().toString(36).slice(2)}`;
  }
}

function rackMathAttribution(payload) {
  const currentParams = new URLSearchParams(window.location.search);
  const candidates = {
    source: payload.seo_source || currentParams.get("source") || "organic_or_direct",
    intent: payload.seo_intent || currentParams.get("intent"),
    tool: payload.seo_tool || payload.tool || currentParams.get("tool"),
    template: payload.seo_template || currentParams.get("template"),
    program: payload.seo_program || currentParams.get("program"),
    persona: payload.seo_persona || currentParams.get("persona"),
    feature: payload.seo_feature || currentParams.get("feature"),
  };

  return Object.fromEntries(
    Object.entries(candidates)
      .filter(([, value]) => value !== null && value !== undefined && String(value).trim())
      .map(([key, value]) => [key, String(value).slice(0, 160)]),
  );
}

function rackMathRemoteProperties(payload) {
  return Object.fromEntries(
    Object.entries(payload)
      .filter(([key, value]) => rackMathRemotePropertyKeys.has(key) && value !== null && value !== undefined)
      .map(([key, value]) => [key, String(value).slice(0, 160)]),
  );
}

function sendRackMathEvent(eventName, payload) {
  const config = rackMathAnalyticsConfig();
  const remoteEventName = rackMathRemoteEventNames[eventName];
  if (!config || !remoteEventName) return;

  const occurredAt = new Date().toISOString();
  const suffix =
    typeof window.crypto?.randomUUID === "function"
      ? window.crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  const event = {
    id: `${remoteEventName}:${occurredAt}:${suffix}`,
    eventName: remoteEventName,
    occurredAt,
    anonymousId: rackMathAnonymousId(),
    attribution: rackMathAttribution(payload),
    properties: rackMathRemoteProperties(payload),
  };

  void fetch(config.endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      apikey: config.anonKey,
      "x-app-version": "rackmath-marketing",
    },
    body: JSON.stringify({ event }),
    credentials: "omit",
    keepalive: true,
  }).catch(() => {});
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

  sendRackMathEvent(eventName, eventPayload);

  return eventPayload;
}

window.RackMathAnalytics = {
  track: trackRackMathEvent,
  contentGroup: rackMathContentGroup,
};

trackRackMathEvent("page_viewed", {
  page_title: document.title,
});

document.querySelectorAll('a[href^="https://www.rackmath.app"], [data-rm-app-link]').forEach((link) => {
  const destination = new URL(link.href, window.location.href);
  const source = destination.searchParams.get("source") || "";
  if (!/^[a-z0-9_-]{1,40}$/i.test(source)) {
    destination.searchParams.set("source", window.location.pathname === "/" ? "homepage" : "seo");
  }
  if (!destination.searchParams.get("intent")) {
    destination.searchParams.set("intent", "onboarding");
  }
  link.href = destination.href;

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
    if (heading.hasAttribute("data-rm-kinetic-heading")) return;
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

function initRackMathKineticTitle(gsap) {
  const heading = document.querySelector("[data-rm-kinetic-heading]");
  const word = heading?.querySelector(".rm-kinetic-word");
  const cursor = heading?.querySelector(".rm-kinetic-cursor");
  const toggle = document.querySelector("[data-rm-kinetic-toggle]");

  if (
    !heading ||
    !word ||
    !cursor ||
    !toggle ||
    heading.dataset.rmKineticActive === "true"
  ) {
    return;
  }

  heading.dataset.rmKineticActive = "true";
  heading.classList.add("is-rm-typing");

  const state = { characters: word.textContent.length };
  const timeline = gsap.timeline({ repeat: -1 });
  const erase = (text) => {
    timeline.to(state, {
      characters: 0,
      duration: Math.max(0.24, text.length * 0.05),
      ease: "none",
      onUpdate: () => {
        word.textContent = text.slice(0, Math.round(state.characters));
      },
    });
  };
  const type = (text) => {
    timeline.set(state, { characters: 0 });
    timeline.to(state, {
      characters: text.length,
      duration: Math.max(0.34, text.length * 0.068),
      ease: "none",
      onUpdate: () => {
        word.textContent = text.slice(0, Math.round(state.characters));
      },
    });
  };

  timeline.to({}, { duration: 1.35 });
  erase("math.");
  timeline.to({}, { duration: 0.1 });
  type("confusion.");
  timeline.to({}, { duration: 1.45 });
  erase("confusion.");
  timeline.to({}, { duration: 0.1 });
  type("time.");
  timeline.to({}, { duration: 1.45 });
  erase("time.");
  timeline.to({}, { duration: 0.1 });
  type("math.");

  let userPaused = false;
  const motionPreference = window.matchMedia("(prefers-reduced-motion: reduce)");
  const setPausedState = (paused) => {
    timeline.paused(paused);
    heading.classList.toggle("is-rm-typing", !paused);
    toggle.setAttribute(
      "aria-label",
      paused ? "Resume headline animation" : "Pause headline animation",
    );
    toggle.querySelector(".rm-kinetic-toggle-icon").textContent = paused ? "▶" : "Ⅱ";
    toggle.querySelector(".rm-kinetic-toggle-label").textContent = paused
      ? "Play motion"
      : "Pause motion";
  };

  toggle.addEventListener("click", () => {
    userPaused = !userPaused;
    setPausedState(userPaused);
  });

  const syncAutomaticPause = () => {
    if (document.hidden || motionPreference.matches) {
      timeline.pause();
      heading.classList.remove("is-rm-typing");
      return;
    }

    if (!userPaused) {
      heading.classList.add("is-rm-typing");
      timeline.resume();
    }
  };

  motionPreference.addEventListener("change", (event) => {
    if (event.matches) {
      timeline.pause(0);
      word.textContent = "math.";
    }

    syncAutomaticPause();
  });
  document.addEventListener("visibilitychange", syncAutomaticPause);
  window.addEventListener("pagehide", () => timeline.pause());
  window.addEventListener("pageshow", syncAutomaticPause);
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

function initRackMathFlowZoom(gsap) {
  const section = document.querySelector(".rm-flow-section");
  const grid = section?.querySelector(".rm-flow-grid");
  const stage = section?.querySelector(".rm-flow-stage") || grid;
  const frames = gsap.utils.toArray(".rm-flow-zoom");
  const zoomTargets = frames
    .map((frame) => {
      const image = frame.querySelector("img");
      const card = frame.closest("li");
      const scale = Number.parseFloat(frame.dataset.rmZoomScale || "2");

      if (!image || !card) return null;

      gsap.set(image, {
        scale: 1,
        transformOrigin: frame.dataset.rmZoomOrigin || "50% 50%",
        force3D: true,
      });

      return { card, image, scale };
    })
    .filter(Boolean);

  if (!section || !stage || !grid || zoomTargets.length < 2) return;

  const motionMedia = gsap.matchMedia();

  motionMedia.add("(min-width: 961px) and (min-height: 560px)", () => {
    const [firstStep, secondStep] = zoomTargets;
    const headerBottom = () => {
      const headerRect = document.querySelector(".site-header")?.getBoundingClientRect();
      return Math.ceil((headerRect?.bottom || 78) + 14);
    };

    if (window.ScrollTrigger.isTouch === 1) return;

    const sequence = gsap.timeline({
      scrollTrigger: {
        id: "rm-flow-pin",
        trigger: stage,
        start: () => `top top+=${headerBottom()}`,
        end: () => `+=${Math.max(1450, Math.round(window.innerHeight * 1.9))}`,
        pin: stage,
        pinSpacing: true,
        scrub: 0.65,
        anticipatePin: 1,
        invalidateOnRefresh: true,
        refreshPriority: 1,
        onToggle: (self) => section.classList.toggle("is-rm-flow-pinned", self.isActive),
      },
    });

    sequence
      .to(firstStep.image, {
        scale: firstStep.scale,
        duration: 0.9,
        ease: "none",
      })
      .to({}, { duration: 0.1 })
      .to(firstStep.image, {
        scale: 1,
        duration: 0.3,
        ease: "none",
      })
      .to(secondStep.image, {
        scale: secondStep.scale,
        duration: 0.9,
        ease: "none",
      })
      .to({}, { duration: 0.1 })
      .to(secondStep.image, {
        scale: 1,
        duration: 0.3,
        ease: "none",
      })
      .to({}, { duration: 0.1 });

    return () => {
      section.classList.remove("is-rm-flow-pinned");
    };
  });

  motionMedia.add("(max-width: 960px), (max-height: 559px)", () => {
    zoomTargets.forEach(({ card, image, scale }) => {
      const mobileAdjustment = window.matchMedia("(max-width: 640px)").matches ? 0.25 : 0;

      gsap.to(image, {
        scale: Math.max(1.55, scale - mobileAdjustment),
        ease: "none",
        scrollTrigger: {
          trigger: card,
          start: "top 78%",
          end: "bottom 28%",
          scrub: 0.65,
          invalidateOnRefresh: true,
        },
      });
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
  initRackMathFlowZoom(gsap);

  const heroMaskTargets = gsap.utils.toArray(
    ".hero h1 .rm-text-mask-inner, .page-hero h1 .rm-text-mask-inner",
  );
  const useOpenHeroReveal = document.body.classList.contains("home-page");
  const kineticHeading = document.querySelector("[data-rm-kinetic-heading]");

  if (heroMaskTargets.length) {
    gsap.set(heroMaskTargets, { clearProps: "transform,opacity,visibility" });
    gsap.set(
      heroMaskTargets,
      useOpenHeroReveal
        ? {
            autoAlpha: 0,
            yPercent: 0,
            y: 18,
            rotate: 0,
          }
        : {
            yPercent: 112,
            y: 0,
            rotate: 1.6,
            transformOrigin: "left bottom",
          },
    );
  }
  if (kineticHeading) {
    gsap.set(kineticHeading, { autoAlpha: 0, y: 18 });
  }
  document.documentElement.classList.remove("has-rm-hero-mask");

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
      useOpenHeroReveal
        ? {
            autoAlpha: 1,
            y: 0,
            duration: 0.72,
            ease: "power3.out",
            stagger: 0.035,
          }
        : {
            yPercent: 0,
            rotate: 0,
            duration: 0.92,
            ease: "power4.out",
            stagger: 0.035,
          },
      "-=0.5",
    );
  }
  if (kineticHeading) {
    heroTimeline.to(
      kineticHeading,
      {
        autoAlpha: 1,
        y: 0,
        duration: 0.72,
        ease: "power3.out",
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
    ".rm-status-card",
    {
      autoAlpha: 0,
      y: 18,
      scale: 0.96,
      stagger: 0.07,
      duration: 0.56,
    },
    "-=0.4",
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
  fromIfAny(
    ".hero-signals div",
    {
      autoAlpha: 0,
      y: 16,
      stagger: 0.06,
      duration: 0.44,
    },
    "-=0.36",
    heroTimeline,
  );
  if (kineticHeading) {
    heroTimeline.call(() => initRackMathKineticTitle(gsap));
  }

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
    ".story-rail a",
    ".story-step",
    ".stat-grid > div",
    ".proof-grid > div",
    ".plan-comparison > div",
    ".feature-card",
    ".price-card",
    ".faq-list details",
    ".rm-signal-strip > div",
    ".rm-calculation-dialogue > *",
    ".rm-bento-card",
    ".rm-flow-grid > li",
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
    ".rm-app-calculator-shell",
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

  const keepRevealContentVisible = document.body.classList.contains("home-page");

  gsap.utils.toArray(revealSelector).forEach((element) => {
    gsap.from(element, {
      ...(keepRevealContentVisible ? {} : { autoAlpha: 0 }),
      y: 34,
      duration: 0.72,
      ease: "power3.out",
      scrollTrigger: {
        trigger: element,
        start: "top 84%",
        toggleActions: keepRevealContentVisible
          ? "play none none none"
          : "play none none reverse",
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
      y: 34,
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
