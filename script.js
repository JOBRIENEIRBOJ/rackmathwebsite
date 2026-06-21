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

function initRackMathMotion() {
  if (!window.gsap || !window.ScrollTrigger) return;

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  if (reduceMotion.matches) return;

  const { gsap } = window;
  gsap.registerPlugin(window.ScrollTrigger);

  document.documentElement.classList.add("has-rm-motion");

  const scrollMeter = document.createElement("div");
  scrollMeter.className = "scroll-meter";
  scrollMeter.setAttribute("aria-hidden", "true");
  document.body.prepend(scrollMeter);

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

  heroTimeline
    .from(".site-header", {
      autoAlpha: 0,
      y: -18,
      duration: 0.56,
    })
    .from(
      ".hero-copy > *",
      {
        autoAlpha: 0,
        y: 34,
        stagger: 0.08,
      },
      "-=0.18",
    )
    .from(
      ".hero-app-frame-shell",
      {
        autoAlpha: 0,
        y: 42,
        rotate: 1.2,
      },
      "-=0.56",
    )
    .from(
      ".trust-row span",
      {
        autoAlpha: 0,
        y: 12,
        stagger: 0.06,
        duration: 0.44,
      },
      "-=0.42",
    );

  gsap.to(".hero-app-frame-shell", {
    y: -26,
    ease: "none",
    scrollTrigger: {
      trigger: ".hero",
      start: "top top",
      end: "bottom top",
      scrub: true,
    },
  });

  gsap.utils.toArray(".section-heading, .section-copy, .stat-grid > div, .feature-card, .price-card, .faq-list details, .final-cta > *").forEach((element) => {
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

  gsap.from(".featured-price", {
    y: 24,
    scale: 0.98,
    duration: 0.8,
    ease: "power3.out",
    scrollTrigger: {
      trigger: ".pricing-grid",
      start: "top 76%",
    },
  });

  gsap.to(".final-cta", {
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

initRackMathMotion();
