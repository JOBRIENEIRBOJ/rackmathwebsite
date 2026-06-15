(() => {
  const SCALE = 100;
  const DEFAULT_TARGET = { lbs: 225, kg: 100 };
  const SETTINGS = {
    lbs: {
      label: 'lb',
      bars: [
        { label: 'Olympic barbell, 45 lb', value: 45 },
        { label: "Women's Olympic barbell, 33 lb", value: 33 },
        { label: 'Training bar, 20 lb', value: 20 },
      ],
      plates: [55, 45, 35, 25, 10, 5, 2.5],
      defaults: [45, 35, 25, 10, 5, 2.5],
    },
    kg: {
      label: 'kg',
      bars: [
        { label: 'Olympic barbell, 20 kg', value: 20 },
        { label: "Women's Olympic barbell, 15 kg", value: 15 },
        { label: 'Training bar, 10 kg', value: 10 },
      ],
      plates: [25, 20, 15, 10, 5, 2.5, 1.25],
      defaults: [25, 20, 15, 10, 5, 2.5, 1.25],
    },
  };
  const PLATE_META = {
    lbs: {
      55: { height: 134, width: 34 },
      45: { height: 128, width: 34 },
      35: { height: 116, width: 30 },
      25: { height: 104, width: 28 },
      10: { height: 86, width: 24 },
      5: { height: 70, width: 20 },
      2.5: { height: 56, width: 18 },
    },
    kg: {
      25: { height: 132, width: 34 },
      20: { height: 122, width: 32 },
      15: { height: 108, width: 28 },
      10: { height: 92, width: 24 },
      5: { height: 74, width: 20 },
      2.5: { height: 60, width: 18 },
      1.25: { height: 50, width: 16 },
    },
  };

  function track(eventName, payload = {}) {
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

  function getUnit(root) {
    return root.querySelector('[data-rm-unit]:checked')?.value === 'kg' ? 'kg' : 'lbs';
  }

  function getSelectedPlates(root) {
    return Array.from(root.querySelectorAll('[data-rm-plate-option]:checked'))
      .map((input) => Number(input.value))
      .filter((value) => Number.isFinite(value) && value > 0)
      .sort((a, b) => b - a);
  }

  function renderBarOptions(root, unit, previousBar) {
    const select = root.querySelector('[data-rm-bar-select]');
    if (!select) return;

    const settings = SETTINGS[unit];
    const requestedBar = Number(previousBar);
    const matchingBar = settings.bars.find((bar) => bar.value === requestedBar);
    const selectedValue = matchingBar ? requestedBar : settings.bars[0].value;

    select.innerHTML = settings.bars
      .map(
        (bar) =>
          `<option value="${bar.value}"${bar.value === selectedValue ? ' selected' : ''}>${bar.label}</option>`
      )
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
    const plates = Array.isArray(availablePlates) ? availablePlates : [];

    if (!Number.isFinite(target) || target <= 0) {
      return { status: 'error', message: 'Enter a target weight greater than zero.', plates: [], perSide: 0, total: Number.isFinite(bar) ? bar : 0 };
    }

    if (!Number.isFinite(bar) || bar < 0) {
      return { status: 'error', message: 'Choose a valid bar weight.', plates: [], perSide: 0, total: 0 };
    }

    if (!plates.length) {
      return { status: 'error', message: 'Select at least one plate size.', plates: [], perSide: 0, total: bar };
    }

    const perSide = (target - bar) / 2;
    if (perSide < -0.001) {
      return { status: 'error', message: 'Target weight must be greater than the bar weight.', plates: [], perSide: 0, total: bar };
    }

    if (Math.abs(perSide) < 0.001) {
      return { status: 'ok', message: `The empty bar is ${formatWeight(bar)} ${SETTINGS[unit].label}.`, plates: [], perSide: 0, total: bar };
    }

    const targetUnits = Math.round(perSide * SCALE);
    const plateUnits = plates
      .map((plate) => ({ plate, units: Math.round(plate * SCALE) }))
      .filter((plate) => plate.units > 0)
      .sort((a, b) => b.units - a.units);
    const previous = Array(targetUnits + 1).fill(null);
    previous[0] = { previousAmount: -1, plate: 0 };

    for (let amount = 1; amount <= targetUnits; amount += 1) {
      for (const candidate of plateUnits) {
        const priorAmount = amount - candidate.units;
        if (priorAmount >= 0 && previous[priorAmount]) {
          previous[amount] = { previousAmount: priorAmount, plate: candidate.plate };
          break;
        }
      }
    }

    let bestAmount = targetUnits;
    while (bestAmount > 0 && !previous[bestAmount]) bestAmount -= 1;

    const loadedPlates = [];
    let cursor = bestAmount;
    while (cursor > 0 && previous[cursor]) {
      loadedPlates.push(previous[cursor].plate);
      cursor = previous[cursor].previousAmount;
    }
    loadedPlates.sort((a, b) => b - a);

    const loadedPerSide = roundWeight(bestAmount / SCALE);
    const loadedTotal = roundWeight(bar + loadedPerSide * 2);
    const targetTotal = roundWeight(target);

    if (bestAmount < targetUnits) {
      return {
        status: 'warning',
        message: `Closest loadable weight: ${formatWeight(loadedTotal)} ${SETTINGS[unit].label}.`,
        plates: loadedPlates,
        perSide: loadedPerSide,
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
    const meta = PLATE_META[unit][weight] || { height: 72, width: 18 };
    const plate = document.createElement('span');
    plate.className = 'rm-plate';
    if (weight <= 2.5) {
      plate.classList.add('rm-plate-small');
    }
    plate.textContent = formatWeight(weight);
    plate.style.setProperty('--rm-plate-height', `${meta.height}px`);
    plate.style.setProperty('--rm-plate-width', `${meta.width}px`);
    plate.setAttribute('aria-label', `${formatWeight(weight)} ${SETTINGS[unit].label} plate`);
    return plate;
  }

  function renderPlateStack(stack, plates, unit, side) {
    if (!stack) return;
    const orderedPlates = side === 'left' ? [...plates].reverse() : plates;
    stack.replaceChildren(...orderedPlates.map((plate) => createPlateElement(plate, unit)));
  }

  function renderResult(root, result, unit, barWeight) {
    const label = SETTINGS[unit].label;
    const message = root.querySelector('[data-rm-result-message]');
    const visualizer = root.querySelector('[data-rm-visualizer]');
    const barLabel = root.querySelector('[data-rm-bar-label]');
    const perSide = root.querySelector('[data-rm-per-side]');
    const total = root.querySelector('[data-rm-total]');
    const plateList = root.querySelector('[data-rm-plate-list]');
    const platesCopy = result.plates.length
      ? result.plates.map((plate) => formatWeight(plate)).join(' + ')
      : 'Empty bar';

    if (message) {
      message.textContent = result.message;
      message.classList.toggle('is-error', result.status === 'error');
      message.classList.toggle('is-warning', result.status === 'warning');
    }

    renderPlateStack(root.querySelector('[data-rm-left-stack]'), result.plates, unit, 'left');
    renderPlateStack(root.querySelector('[data-rm-right-stack]'), result.plates, unit, 'right');

    if (barLabel) barLabel.textContent = `${formatWeight(barWeight)} ${label} bar`;
    if (perSide) perSide.textContent = `${formatWeight(result.perSide)} ${label}`;
    if (total) total.textContent = `${formatWeight(result.total)} ${label}`;
    if (plateList) plateList.textContent = platesCopy;

    if (visualizer) {
      visualizer.setAttribute(
        'aria-label',
        result.plates.length
          ? `Barbell visualizer showing ${platesCopy} ${label} per side`
          : `Barbell visualizer showing an empty ${formatWeight(barWeight)} ${label} bar`
      );
    }
  }

  function initCalculator(root) {
    const targetInput = root.querySelector('[data-rm-target-weight]');
    const barSelect = root.querySelector('[data-rm-bar-select]');
    const unitLabel = root.querySelector('[data-rm-unit-label]');
    let activeUnit = getUnit(root);
    let lastResult = null;

    renderBarOptions(root, activeUnit, barSelect?.value);
    renderPlateControls(root, activeUnit, getSelectedPlates(root));

    const update = () => {
      const unit = getUnit(root);
      const label = SETTINGS[unit].label;
      const barWeight = Number(barSelect?.value || SETTINGS[unit].bars[0].value);
      const result = calculatePlates(targetInput?.value, barWeight, getSelectedPlates(root), unit);
      if (unitLabel) unitLabel.textContent = label;
      renderResult(root, result, unit, barWeight);
      lastResult = { result, unit, targetWeight: Number(targetInput?.value), barWeight };
    };

    root.addEventListener('submit', (event) => {
      event.preventDefault();
      update();
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
      if (event.target.matches('[data-rm-target-weight], [data-rm-plate-option]')) update();
    });

    root.addEventListener('change', (event) => {
      if (event.target.matches('[data-rm-unit]')) {
        const nextUnit = getUnit(root);
        const previousDefault = DEFAULT_TARGET[activeUnit];
        const targetValue = Number(targetInput?.value);

        if (targetInput && (!targetInput.value || Math.abs(targetValue - previousDefault) < 0.001)) {
          targetInput.value = DEFAULT_TARGET[nextUnit];
        }

        activeUnit = nextUnit;
        renderBarOptions(root, nextUnit);
        renderPlateControls(root, nextUnit);
        update();
        return;
      }

      if (event.target.matches('[data-rm-bar-select]')) update();
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
