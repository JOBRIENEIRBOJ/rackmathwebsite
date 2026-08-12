(() => {
  const DEFAULT_TARGET = { lbs: 135, kg: 60 };
  const KG_PER_LB = 0.45359237;
  const SETTINGS = {
    lbs: {
      label: 'lbs',
      bars: [
        { id: 'olympic_mens', label: 'Olympic barbell, 45 lb', value: 45 },
        { id: 'olympic_womens', label: "Women's Olympic barbell, 33 lb", value: 33 },
        { id: 'standard', label: 'Standard barbell, 20 lb', value: 20 },
        { id: 'ez_curl', label: 'EZ curl bar, 20 lb', value: 20 },
        { id: 'trap_hex_45', label: 'Trap / hex bar, 45 lb', value: 45 },
        { id: 'trap_hex_55', label: 'Trap / hex bar, 55 lb', value: 55 },
        { id: 'trap_hex_60', label: 'Trap / hex bar, 60 lb', value: 60 },
        { id: 'safety_squat', label: 'Safety squat bar, 65 lb', value: 65 },
        { id: 'swiss', label: 'Swiss / football bar, 40 lb', value: 40 },
        { id: 'cambered', label: 'Cambered bar, 65 lb', value: 65 },
        { id: 'technique', label: 'Technique / training bar, 25 lb', value: 25 },
        { id: 'junior', label: 'Junior / youth bar, 10 lb', value: 10 },
        { id: 'axle', label: 'Axle bar, 29 lb', value: 29 },
        { id: 'buffalo', label: 'Buffalo / bow bar, 50 lb', value: 50 },
      ],
      plates: [55, 45, 35, 25, 10, 5, 2.5],
      defaults: [45, 35, 25, 10, 5, 2.5],
    },
    kg: {
      label: 'kg',
      bars: [
        { id: 'olympic_mens', label: 'Olympic barbell, 20 kg', value: 20 },
        { id: 'olympic_womens', label: "Women's Olympic barbell, 15 kg", value: 15 },
        { id: 'standard', label: 'Standard barbell, 9 kg', value: 9 },
        { id: 'ez_curl', label: 'EZ curl bar, 9 kg', value: 9 },
        { id: 'trap_hex_45', label: 'Trap / hex bar, 20 kg', value: 20 },
        { id: 'trap_hex_55', label: 'Trap / hex bar, 25 kg', value: 25 },
        { id: 'trap_hex_60', label: 'Trap / hex bar, 27 kg', value: 27 },
        { id: 'safety_squat', label: 'Safety squat bar, 29 kg', value: 29 },
        { id: 'swiss', label: 'Swiss / football bar, 18 kg', value: 18 },
        { id: 'cambered', label: 'Cambered bar, 29 kg', value: 29 },
        { id: 'technique', label: 'Technique / training bar, 11 kg', value: 11 },
        { id: 'junior', label: 'Junior / youth bar, 5 kg', value: 5 },
        { id: 'axle', label: 'Axle bar, 13 kg', value: 13 },
        { id: 'buffalo', label: 'Buffalo / bow bar, 23 kg', value: 23 },
      ],
      plates: [25, 20, 15, 10, 5, 2.5, 1.25],
      defaults: [25, 20, 15, 10, 5, 2.5, 1.25],
    },
  };
  const PLATE_META = {
    lbs: {
      55: { height: 130, width: 32, font: 16, mobileHeight: 110, mobileWidth: 28, mobileFont: 14 },
      45: { height: 130, width: 28, font: 16, mobileHeight: 110, mobileWidth: 24, mobileFont: 14 },
      35: { height: 115, width: 24, font: 15, mobileHeight: 95, mobileWidth: 20, mobileFont: 13 },
      25: { height: 100, width: 22, font: 14, mobileHeight: 85, mobileWidth: 18, mobileFont: 12 },
      10: { height: 85, width: 18, font: 13, mobileHeight: 70, mobileWidth: 14, mobileFont: 11 },
      5: { height: 70, width: 14, font: 12, mobileHeight: 58, mobileWidth: 12, mobileFont: 11 },
      2.5: { height: 58, width: 12, font: 9, mobileHeight: 48, mobileWidth: 10, mobileFont: 10 },
    },
    kg: {
      25: { height: 130, width: 28, font: 16, mobileHeight: 110, mobileWidth: 24, mobileFont: 14 },
      20: { height: 115, width: 24, font: 15, mobileHeight: 95, mobileWidth: 20, mobileFont: 13 },
      15: { height: 100, width: 22, font: 14, mobileHeight: 85, mobileWidth: 18, mobileFont: 12 },
      10: { height: 85, width: 18, font: 13, mobileHeight: 70, mobileWidth: 14, mobileFont: 11 },
      5: { height: 70, width: 14, font: 12, mobileHeight: 58, mobileWidth: 12, mobileFont: 11 },
      2.5: { height: 58, width: 12, font: 9, mobileHeight: 48, mobileWidth: 10, mobileFont: 10, borderWidth: 1, borderColor: '#999' },
      1.25: { height: 50, width: 10, font: 8, mobileHeight: 42, mobileWidth: 8, mobileFont: 9, borderWidth: 1, borderColor: '#999' },
    },
  };

  function track(eventName, payload = {}) {
    if (window.RackMathAnalytics?.track) {
      window.RackMathAnalytics.track(eventName, payload);
      return;
    }

    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push({ event: eventName, ...payload });
    window.dispatchEvent(new CustomEvent(`rackmath:${eventName}`, { detail: payload }));
  }

  function formatWeight(value) {
    const normalized = Number(value);
    if (!Number.isFinite(normalized)) return '0';
    return Number.isInteger(normalized)
      ? String(normalized)
      : normalized.toFixed(2).replace(/\.?0+$/, '');
  }

  function roundWeight(value) {
    return Math.round(value * 100) / 100;
  }

  function getOrdinalSuffix(day) {
    const remainder = day % 100;
    if (remainder >= 11 && remainder <= 13) return 'th';
    if (day % 10 === 1) return 'st';
    if (day % 10 === 2) return 'nd';
    if (day % 10 === 3) return 'rd';
    return 'th';
  }

  function renderSessionDate(root) {
    const date = new Date();
    const day = date.getDate();
    const suffix = getOrdinalSuffix(day);
    const locale = document.documentElement.lang || navigator.language || 'en-US';
    const dayElement = root.querySelector('[data-rm-date-day]');
    const suffixElement = root.querySelector('[data-rm-date-suffix]');
    const labelElement = root.querySelector('[data-rm-date-label]');
    if (dayElement) dayElement.textContent = String(day);
    if (suffixElement) suffixElement.textContent = suffix;
    if (labelElement) {
      labelElement.setAttribute('aria-label', date.toLocaleDateString(locale, {
        month: 'long',
        day: 'numeric',
        year: 'numeric',
      }));
    }
  }

  function getUnit(root) {
    return root.querySelector('[data-rm-unit]:checked')?.value === 'kg' ? 'kg' : 'lbs';
  }

  function getSelectedPlates(root) {
    return Array.from(root.querySelectorAll('[data-rm-plate-option]:checked'))
      .map((input) => Number(input.value))
      .filter((value) => Number.isFinite(value) && value > 0)
      .sort((a, b) => b - a);
  }

  function renderBarOptions(root, unit, previousBarId) {
    const select = root.querySelector('[data-rm-bar-select]');
    if (!select) return;

    const settings = SETTINGS[unit];
    const matchingBar = settings.bars.find((bar) => bar.id === previousBarId);
    const selectedId = matchingBar ? matchingBar.id : settings.bars[0].id;

    select.innerHTML = settings.bars
      .map(
        (bar) =>
          `<option value="${bar.id}" data-bar-weight="${bar.value}"${bar.id === selectedId ? ' selected' : ''}>${bar.label}</option>`
      )
      .concat('<option value="custom">Custom bar weight</option>')
      .join('');
  }

  function renderPlateControls(root, unit, selectedPlates) {
    const controls = root.querySelector('[data-rm-plate-controls]');
    if (!controls) return;

    const settings = SETTINGS[unit];
    const selected = selectedPlates?.length ? selectedPlates : settings.defaults;
    controls.innerHTML = settings.plates
      .map((plate) => {
        const checked = selected.includes(plate) ? ' checked' : '';
        return `<label><input type="checkbox" value="${plate}" data-rm-plate-option${checked}><span>${formatWeight(
          plate
        )}</span></label>`;
      })
      .join('');
  }

  function calculatePlates(targetWeight, barWeight, availablePlates, unit) {
    const target = Number(targetWeight);
    const bar = Number(barWeight);
    const plates = (Array.isArray(availablePlates) ? availablePlates : [])
      .map((plate) => Number(plate))
      .filter((plate) => Number.isFinite(plate) && plate > 0)
      .sort((a, b) => b - a);

    if (!Number.isFinite(target) || target <= 0) {
      return { status: 'error', message: 'Enter a target weight greater than zero.', plates: [], perSide: 0, total: Number.isFinite(bar) ? bar : 0 };
    }

    if (target > 2000) {
      return { status: 'error', message: 'Enter a target weight of 2,000 or less.', plates: [], perSide: 0, total: Number.isFinite(bar) ? bar : 0 };
    }

    if (!Number.isFinite(bar) || bar < 0 || bar > 200) {
      return { status: 'error', message: 'Choose a valid bar weight.', plates: [], perSide: 0, total: 0 };
    }

    if (!plates.length) {
      return { status: 'error', message: 'Select at least one plate size.', plates: [], perSide: 0, total: bar };
    }

    const perSide = (target - bar) / 2;
    if (perSide < 0) {
      return { status: 'error', message: 'Target weight must be greater than the bar weight.', plates: [], perSide: 0, total: bar };
    }

    if (perSide === 0) {
      return { status: 'ok', message: `The empty bar is ${formatWeight(bar)} ${SETTINGS[unit].label}.`, plates: [], perSide: 0, total: bar };
    }

    const loadedPlates = [];
    let remaining = perSide;
    for (const plate of plates) {
      while (remaining >= plate - 0.001) {
        loadedPlates.push(plate);
        remaining -= plate;
      }
    }

    const loadedPerSide = roundWeight(perSide - Math.max(0, remaining));
    const loadedTotal = roundWeight(bar + loadedPerSide * 2);
    const targetTotal = roundWeight(target);

    if (remaining > 0.01) {
      return {
        status: 'error',
        message: `Cannot achieve ${formatWeight(targetTotal)} ${SETTINGS[unit].label}.`,
        suggestion: `Closest loadable weight: ${formatWeight(loadedTotal)} ${SETTINGS[unit].label}.`,
        achieved: loadedTotal,
        plates: [],
        perSide: roundWeight(perSide),
        total: loadedTotal,
        requestedTotal: targetTotal,
      };
    }

    return {
      status: 'ok',
      message: `${formatWeight(targetTotal)} ${SETTINGS[unit].label} uses ${formatWeight(loadedPerSide)} ${SETTINGS[unit].label} per side.`,
      plates: loadedPlates,
      perSide: loadedPerSide,
      total: targetTotal,
    };
  }

  function createPlateElement(weight, unit) {
    const meta = PLATE_META[unit][weight] || {
      height: 85,
      width: 18,
      font: 13,
      mobileHeight: 70,
      mobileWidth: 14,
      mobileFont: 11,
    };
    const plate = document.createElement('span');
    plate.className = 'rm-plate';
    if (weight <= 2.5) {
      plate.classList.add('rm-plate-small');
    }
    if (weight === 2.5 || weight === 1.25) {
      plate.textContent = formatWeight(weight);
    } else {
      const label = document.createElement('span');
      label.className = 'rm-plate-num';
      label.textContent = String(Math.floor(weight));
      plate.append(label);
    }
    plate.style.setProperty('--rm-plate-height', `${meta.height}px`);
    plate.style.setProperty('--rm-plate-width', `${meta.width}px`);
    plate.style.setProperty('--rm-plate-font-size', `${meta.font}px`);
    plate.style.setProperty('--rm-plate-mobile-height', `${meta.mobileHeight}px`);
    plate.style.setProperty('--rm-plate-mobile-width', `${meta.mobileWidth}px`);
    plate.style.setProperty('--rm-plate-mobile-font-size', `${meta.mobileFont}px`);
    plate.style.setProperty('--rm-plate-border-width', `${meta.borderWidth || 2}px`);
    plate.style.setProperty('--rm-plate-border-color', meta.borderColor || '#111');
    plate.setAttribute('aria-label', `${formatWeight(weight)} ${SETTINGS[unit].label} plate`);
    return plate;
  }

  function renderPlateStack(stack, plates, unit) {
    if (!stack) return;
    stack.replaceChildren(...plates.map((plate) => createPlateElement(plate, unit)));
  }

  function renderResult(root, result, unit, barWeight) {
    const label = SETTINGS[unit].label;
    const message = root.querySelector('[data-rm-result-message]');
    const visualizer = root.querySelector('[data-rm-visualizer]');
    const barLabel = root.querySelector('[data-rm-bar-label]');
    const perSide = root.querySelector('[data-rm-per-side]');
    const total = root.querySelector('[data-rm-total]');
    const plateList = root.querySelector('[data-rm-plate-list]');
    const resultMessage = [result.message, result.suggestion].filter(Boolean).join(' ');
    const platesCopy = result.status !== 'ok'
      ? 'No exact plate match'
      : result.plates.length
      ? result.plates.map((plate) => formatWeight(plate)).join(' + ')
      : 'Empty bar';

    if (message) {
      message.textContent = resultMessage;
      message.classList.toggle('is-error', result.status === 'error');
      message.classList.toggle('is-warning', result.status === 'warning');
    }

    renderPlateStack(root.querySelector('[data-rm-left-stack]'), result.plates, unit);
    renderPlateStack(root.querySelector('[data-rm-right-stack]'), result.plates, unit);

    if (barLabel) barLabel.textContent = `${formatWeight(barWeight)} ${label}`;
    if (perSide) perSide.textContent = `${formatWeight(result.perSide)} ${label}`;
    if (total) total.textContent = `${formatWeight(result.total)} ${label}`;
    if (plateList) plateList.textContent = platesCopy;

    if (visualizer) {
      visualizer.classList.toggle('is-error', result.status === 'error');
      visualizer.classList.toggle('is-warning', result.status === 'warning');
      visualizer.setAttribute(
        'aria-label',
        result.status !== 'ok'
          ? resultMessage
          : result.plates.length
          ? `Barbell visualizer showing ${platesCopy} ${label} per side`
          : `Barbell visualizer showing an empty ${formatWeight(barWeight)} ${label} bar`
      );
    }
  }

  function updateAppLinks(targetWeight, unit) {
    if (!Number.isFinite(targetWeight)) return;
    document.querySelectorAll('[data-rm-app-link]').forEach((link) => {
      try {
        const url = new URL(link.href, window.location.href);
        url.searchParams.set('weight', formatWeight(targetWeight));
        url.searchParams.set('unit', SETTINGS[unit].label);
        link.href = url.toString();
      } catch {
        // Keep the server-rendered fallback if the URL cannot be parsed.
      }
    });
  }

  function initSettingsDetails(root) {
    const toggle = root.querySelector('[data-rm-settings-toggle]');
    const panel = root.querySelector('[data-rm-settings-panel]');
    const details = toggle?.closest('details') || panel?.closest('details');
    if (!toggle || !details) return { close: () => false };

    const closedLabel = /^open\b/i.test(toggle.getAttribute('aria-label') || '')
      ? toggle.getAttribute('aria-label')
      : 'Open calculator settings';
    const expandedLabel = closedLabel.replace(/^open\b/i, 'Close');

    if (panel) {
      if (!panel.id) {
        const panelIndex = Array.from(document.querySelectorAll('[data-rm-settings-panel]')).indexOf(panel);
        panel.id = `rm-calculator-settings-${panelIndex + 1}`;
      }
      toggle.setAttribute('aria-controls', panel.id);
    }

    const syncState = () => {
      const isOpen = details.open;
      toggle.setAttribute('aria-expanded', String(isOpen));
      toggle.setAttribute('aria-label', isOpen ? expandedLabel : closedLabel);
      toggle.setAttribute('title', isOpen ? expandedLabel : closedLabel);
      if (panel) panel.setAttribute('aria-hidden', String(!isOpen));
    };

    const close = ({ restoreFocus = false } = {}) => {
      if (!details.open) return false;
      details.open = false;
      syncState();
      if (restoreFocus) toggle.focus();
      return true;
    };

    details.addEventListener('toggle', syncState);
    details.addEventListener('keydown', (event) => {
      if (event.key !== 'Escape' || !details.open) return;
      event.preventDefault();
      event.stopPropagation();
      close({ restoreFocus: true });
    });
    document.addEventListener('click', (event) => {
      if (details.open && !details.contains(event.target)) close();
    });

    syncState();
    return { close };
  }

  function initCalculator(root) {
    const form = root.querySelector('[data-rm-calculator-form]');
    const targetInput = root.querySelector('[data-rm-target-weight]');
    const barSelect = root.querySelector('[data-rm-bar-select]');
    const customBarField = root.querySelector('[data-rm-custom-bar-field]');
    const customBarInput = root.querySelector('[data-rm-custom-bar-weight]');
    const customBarUnit = root.querySelector('[data-rm-custom-bar-unit]');
    const unitLabel = root.querySelector('[data-rm-unit-label]');
    const exerciseLabel = root.querySelector('[data-rm-exercise-label]');
    let activeUnit = getUnit(root);
    let lastResult = null;
    const settingsDetails = initSettingsDetails(root);

    renderSessionDate(root);
    renderBarOptions(root, activeUnit, barSelect?.value || 'olympic_mens');
    renderPlateControls(root, activeUnit, getSelectedPlates(root));

    const getBarWeight = (unit) => {
      if (barSelect?.value === 'custom') {
        return Number(customBarInput?.value);
      }
      return Number(barSelect?.selectedOptions?.[0]?.dataset.barWeight || SETTINGS[unit].bars[0].value);
    };

    const updateCustomBarField = (unit) => {
      const isCustom = barSelect?.value === 'custom';
      if (customBarField) customBarField.hidden = !isCustom;
      if (customBarUnit) customBarUnit.textContent = SETTINGS[unit].label;
    };

    const update = () => {
      const unit = getUnit(root);
      const label = SETTINGS[unit].label;
      const barWeight = getBarWeight(unit);
      const result = calculatePlates(targetInput?.value, barWeight, getSelectedPlates(root), unit);
      if (unitLabel) unitLabel.textContent = label;
      updateCustomBarField(unit);
      renderResult(root, result, unit, barWeight);
      const targetWeight = Number(targetInput?.value);
      updateAppLinks(targetWeight, unit);
      lastResult = { result, unit, targetWeight, barWeight };
    };

    form?.addEventListener('submit', (event) => {
      event.preventDefault();
      update();
      settingsDetails.close();
      if (lastResult?.result?.status !== 'error') {
        track('tool_completed', {
          tool: 'barbell_plate_calculator',
          unit: lastResult.unit,
          target_weight: lastResult.targetWeight,
          loaded_weight: lastResult.result.total,
        });
      }
    });

    root.addEventListener('input', (event) => {
      if (event.target.matches('[data-rm-target-weight], [data-rm-custom-bar-weight], [data-rm-plate-option]')) update();
    });

    root.addEventListener('change', (event) => {
      if (event.target.matches('[data-rm-unit]')) {
        const nextUnit = getUnit(root);
        const targetValue = Number(targetInput?.value);
        const wasCustomBar = barSelect?.value === 'custom';
        const previousBarId = wasCustomBar ? null : barSelect?.value;
        const customBarValue = Number(customBarInput?.value);

        if (targetInput && Number.isFinite(targetValue)) {
          const converted = nextUnit === 'kg'
            ? targetValue * KG_PER_LB
            : targetValue / KG_PER_LB;
          targetInput.value = nextUnit === 'kg'
            ? formatWeight(roundWeight(converted))
            : String(Math.round(converted));
        } else if (targetInput) {
          targetInput.value = DEFAULT_TARGET[nextUnit];
        }

        activeUnit = nextUnit;
        renderBarOptions(root, nextUnit, previousBarId || 'olympic_mens');
        renderPlateControls(root, nextUnit);
        if (wasCustomBar && barSelect) barSelect.value = 'custom';
        if (customBarInput) {
          const convertedBar = Number.isFinite(customBarValue)
            ? nextUnit === 'kg'
              ? customBarValue * KG_PER_LB
              : customBarValue / KG_PER_LB
            : SETTINGS[nextUnit].bars[0].value;
          customBarInput.value = nextUnit === 'kg'
            ? formatWeight(roundWeight(convertedBar))
            : String(Math.round(convertedBar));
        }
        update();
        return;
      }

      if (event.target.matches('[data-rm-bar-select]')) {
        if (event.target.value === 'custom' && customBarInput) {
          customBarInput.value = SETTINGS[getUnit(root)].bars[0].value;
        }
        update();
        if (event.target.value === 'custom') customBarInput?.focus();
      }

      if (event.target.matches('[data-rm-exercise]')) {
        const exercise = root.querySelector('[data-rm-exercise]:checked')?.value || 'Deadlift';
        if (exerciseLabel) exerciseLabel.textContent = exercise;
      }
    });

    update();
  }

  function initAll() {
    document.querySelectorAll('[data-rm-calculator]').forEach(initCalculator);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAll);
  } else {
    initAll();
  }
})();
