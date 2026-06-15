(() => {
  const LB_TO_KG = 0.45359237;
  const KG_TO_LB = 2.2046226218;
  const PLATES_LB = [55, 45, 35, 25, 10, 5, 2.5];

  function format(value, decimals = 1) {
    const rounded = Number(value).toFixed(decimals);
    return rounded.replace(/\.0+$/, '').replace(/(\.\d*[1-9])0+$/, '$1');
  }

  function trackTool(tool, details = {}) {
    const payload = { tool, ...details };
    if (window.RackMathAnalytics?.track) {
      window.RackMathAnalytics.track('tool_completed', payload);
      return;
    }

    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push({ event: 'tool_completed', ...payload });
    window.dispatchEvent(new CustomEvent('rackmath:tool_completed', { detail: payload }));
  }

  function plateSetup(total, bar = 45) {
    let remaining = Math.max(0, (Number(total) - bar) / 2);
    const plates = [];
    for (const plate of PLATES_LB) {
      while (remaining + 0.001 >= plate) {
        plates.push(plate);
        remaining -= plate;
      }
    }
    return plates.length ? plates.map((plate) => format(plate)).join(' + ') : 'Empty bar';
  }

  function setOutput(root, html) {
    const output = root.querySelector('[data-tool-output]');
    if (output) output.innerHTML = html;
  }

  function numberValue(root, selector, fallback = 0) {
    const value = Number(root.querySelector(selector)?.value);
    return Number.isFinite(value) ? value : fallback;
  }

  function initWarmup(root) {
    const update = () => {
      const weight = numberValue(root, '[name="workingWeight"]', 225);
      const unit = root.querySelector('[name="unit"]')?.value || 'lb';
      const percents = [0.4, 0.55, 0.7, 0.82, 0.92];
      const rows = percents
        .map((percent, index) => {
          const load = Math.round((weight * percent) / 5) * 5;
          const reps = [8, 5, 3, 2, 1][index];
          return `<tr><td>${Math.round(percent * 100)}%</td><td>${format(load, 0)} ${unit}</td><td>${reps}</td></tr>`;
        })
        .join('');
      setOutput(root, `<table><thead><tr><th>Jump</th><th>Load</th><th>Reps</th></tr></thead><tbody>${rows}</tbody></table>`);
      trackTool('warmup_set_calculator', { working_weight: weight, unit });
    };
    root.addEventListener('submit', (event) => {
      event.preventDefault();
      update();
    });
    update();
  }

  function initOneRepMax(root) {
    const update = () => {
      const weight = numberValue(root, '[name="weight"]', 185);
      const reps = Math.max(1, numberValue(root, '[name="reps"]', 5));
      const unit = root.querySelector('[name="unit"]')?.value || 'lb';
      const epley = weight * (1 + reps / 30);
      const brzycki = weight * (36 / (37 - Math.min(reps, 36)));
      const average = (epley + brzycki) / 2;
      setOutput(
        root,
        `<div class="tool-result-number">${format(average, 0)} ${unit}</div><p>Average of Epley and Brzycki estimates. Epley: ${format(epley, 0)} ${unit}. Brzycki: ${format(brzycki, 0)} ${unit}.</p>`
      );
      trackTool('one_rep_max_calculator', { weight, reps, estimated_1rm: Math.round(average), unit });
    };
    root.addEventListener('submit', (event) => {
      event.preventDefault();
      update();
    });
    update();
  }

  function initCommonWeights(root) {
    const weights = [95, 135, 185, 225, 275, 315, 365, 405];
    const rows = weights
      .map((weight) => `<tr><td>${weight} lb</td><td>${plateSetup(weight)}</td></tr>`)
      .join('');
    setOutput(root, `<table><thead><tr><th>Target</th><th>45 lb bar setup</th></tr></thead><tbody>${rows}</tbody></table>`);
  }

  function initConverter(root) {
    const update = () => {
      const pounds = numberValue(root, '[name="pounds"]', 225);
      const kg = pounds * LB_TO_KG;
      const roundedKg = Math.round(kg / 2.5) * 2.5;
      const roundedLb = roundedKg * KG_TO_LB;
      setOutput(
        root,
        `<div class="tool-result-number">${format(kg, 1)} kg</div><p>Nearest practical 2.5 kg jump: ${format(roundedKg, 1)} kg, about ${format(roundedLb, 0)} lb.</p>`
      );
      trackTool('lb_kg_plate_converter', { pounds, kilograms: Number(format(kg, 1)) });
    };
    root.addEventListener('submit', (event) => {
      event.preventDefault();
      update();
    });
    update();
  }

  function initRpe(root) {
    const update = () => {
      const oneRm = numberValue(root, '[name="oneRm"]', 250);
      const reps = Math.max(1, numberValue(root, '[name="reps"]', 5));
      const rpe = Math.min(10, Math.max(6, numberValue(root, '[name="rpe"]', 8)));
      const repsInReserve = Math.max(0, 10 - rpe);
      const effectiveReps = reps + repsInReserve;
      const load = oneRm / (1 + effectiveReps / 30);
      setOutput(
        root,
        `<div class="tool-result-number">${format(load, 0)} lb</div><p>Estimated target for ${reps} reps at RPE ${format(rpe, 1)}. This treats RPE as reps in reserve, so RPE 8 means about 2 reps left.</p>`
      );
      trackTool('rpe_calculator', { one_rep_max: oneRm, reps, rpe, target_load: Math.round(load) });
    };
    root.addEventListener('submit', (event) => {
      event.preventDefault();
      update();
    });
    update();
  }

  function initVolume(root) {
    const update = () => {
      const sets = numberValue(root, '[name="sets"]', 5);
      const reps = numberValue(root, '[name="reps"]', 5);
      const weight = numberValue(root, '[name="weight"]', 225);
      const volume = sets * reps * weight;
      setOutput(root, `<div class="tool-result-number">${format(volume, 0)} lb</div><p>${sets} sets x ${reps} reps x ${weight} lb.</p>`);
      trackTool('training_volume_calculator', { sets, reps, weight, volume });
    };
    root.addEventListener('submit', (event) => {
      event.preventDefault();
      update();
    });
    update();
  }

  function initAttempts(root) {
    const update = () => {
      const max = numberValue(root, '[name="max"]', 315);
      const opener = Math.round((max * 0.9) / 5) * 5;
      const second = Math.round((max * 0.97) / 5) * 5;
      const third = Math.round((max * 1.02) / 5) * 5;
      setOutput(
        root,
        `<table><thead><tr><th>Attempt</th><th>Load</th><th>Intent</th></tr></thead><tbody><tr><td>Opener</td><td>${opener} lb</td><td>Confident make</td></tr><tr><td>Second</td><td>${second} lb</td><td>Build total</td></tr><tr><td>Third</td><td>${third} lb</td><td>PR option</td></tr></tbody></table>`
      );
      trackTool('powerlifting_attempt_calculator', { max, opener, second, third });
    };
    root.addEventListener('submit', (event) => {
      event.preventDefault();
      update();
    });
    update();
  }

  function initPlanPreview(root) {
    root.addEventListener('submit', (event) => {
      event.preventDefault();
      const goal = root.querySelector('[name="goal"]')?.value || 'strength';
      const days = root.querySelector('[name="days"]')?.value || '3';
      setOutput(
        root,
        `<div class="tool-result-number">${days}-day ${goal} plan</div><p>RackMath can turn this into a saved workout flow with exercises, target weights, warmups, and history.</p>`
      );
      trackTool('ai_workout_builder_preview', { goal, days });
    });
  }

  function initImporterPreview(root) {
    root.addEventListener('submit', (event) => {
      event.preventDefault();
      const text = root.querySelector('[name="planText"]')?.value || '';
      const lines = text.split('\n').filter((line) => line.trim()).length;
      setOutput(root, `<div class="tool-result-number">${Math.max(lines, 1)} item preview</div><p>Open RackMath to import, clean up, save, and run this as a trackable workout.</p>`);
      trackTool('workout_plan_importer_preview', { lines: Math.max(lines, 1) });
    });
  }

  const initializers = {
    warmup: initWarmup,
    oneRepMax: initOneRepMax,
    commonWeights: initCommonWeights,
    converter: initConverter,
    rpe: initRpe,
    volume: initVolume,
    attempts: initAttempts,
    aiBuilder: initPlanPreview,
    importer: initImporterPreview,
  };

  function initAll() {
    document.querySelectorAll('[data-rm-tool]').forEach((root) => {
      const initializer = initializers[root.dataset.rmTool];
      if (initializer) initializer(root);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAll);
  } else {
    initAll();
  }
})();
