(function () {
  const doc = window.parent?.document || document;
  if (!doc) {
    return;
  }

  const numberFormatter = new Intl.NumberFormat('es-CL', {
    maximumFractionDigits: 2,
    minimumFractionDigits: 0,
  });

  const statusChips = [
    { regex: /(aprobado|completado|cerrado|vigente|activo)/i, tone: 'success' },
    { regex: /(pendiente|en curso|proceso|revisión|observación)/i, tone: 'warning' },
    { regex: /(rechazado|bloqueado|critico|riesgo|vencido)/i, tone: 'danger' },
  ];

  const actionBlueprint = [
    { label: 'Ver', title: 'Ver detalle', action: 'view' },
    { label: 'Editar', title: 'Editar', action: 'edit' },
    { label: 'Más', title: 'Más acciones', action: 'more' },
  ];

  function parseOptions(element) {
    const raw = element.getAttribute('data-andes-options');
    if (!raw) {
      return {};
    }
    try {
      return JSON.parse(raw);
    } catch (error) {
      console.warn('AndesTable: no se pudieron interpretar las opciones', error);
      return {};
    }
  }

  function normaliseNumber(text) {
    const sanitized = text.replace(/\s+/g, '').replace(/%/g, '');
    if (!/[\d]/.test(sanitized)) {
      return null;
    }
    const normalised = sanitized.replace(/\.(?=\d{3}(?:\D|$))/g, '').replace(/,/g, '.');
    const value = Number(normalised);
    if (Number.isNaN(value)) {
      return null;
    }
    return { value, isPercent: /%$/.test(text.trim()) };
  }

  function formatNumber(text) {
    const parsed = normaliseNumber(text);
    if (!parsed) {
      return null;
    }
    const formatted = numberFormatter.format(parsed.value);
    return parsed.isPercent ? `${formatted}%` : formatted;
  }

  function parseDateParts(text) {
    const iso = text.match(/^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$/);
    if (iso) {
      return { year: Number(iso[1]), month: Number(iso[2]) - 1, day: Number(iso[3]) };
    }
    const latam = text.match(/^(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})$/);
    if (latam) {
      const year = latam[3].length === 2 ? Number(`20${latam[3]}`) : Number(latam[3]);
      return { year, month: Number(latam[2]) - 1, day: Number(latam[1]) };
    }
    return null;
  }

  function formatDate(text) {
    const parts = parseDateParts(text.trim());
    if (!parts) {
      return null;
    }
    const candidate = new Date(parts.year, parts.month, parts.day);
    if (Number.isNaN(candidate.getTime())) {
      return null;
    }
    const day = String(candidate.getDate()).padStart(2, '0');
    const month = String(candidate.getMonth() + 1).padStart(2, '0');
    const year = String(candidate.getFullYear());
    return `${day}/${month}/${year}`;
  }

  function buildStatusChip(text) {
    for (const item of statusChips) {
      if (item.regex.test(text)) {
        const chip = doc.createElement('span');
        chip.className = `andes-table__chip andes-table__chip--${item.tone}`;
        chip.textContent = text;
        return chip;
      }
    }
    return null;
  }

  function applyHighlight(rows, count) {
    if (!count || count <= 0) {
      return;
    }
    rows.forEach((row, index) => {
      if (index < count) {
        row.classList.add('andes-table__row--top');
      }
    });
  }

  function enhanceActions(table, columnIndex) {
    const rows = table.querySelectorAll('tbody tr');
    rows.forEach((row) => {
      const cell = row.children[columnIndex];
      if (!cell) {
        return;
      }
      cell.classList.add('andes-table__cell--actions');
      cell.textContent = '';
      actionBlueprint.forEach(({ label, title, action }) => {
        const button = doc.createElement('button');
        button.type = 'button';
        button.className = 'andes-table__action';
        button.dataset.action = action;
        button.setAttribute('title', title);
        button.setAttribute('aria-label', title);
        button.textContent = label;
        cell.appendChild(button);
      });
    });
  }

  function updateSortTooltips(headerCells) {
    headerCells.forEach((header) => {
      const button = header.querySelector('button');
      if (!button) {
        return;
      }
      const ariaLabel = (button.getAttribute('aria-label') || '').toLowerCase();
      if (ariaLabel.includes('asc')) {
        button.setAttribute('title', 'Orden ascendente');
      } else if (ariaLabel.includes('desc')) {
        button.setAttribute('title', 'Orden descendente');
      }
    });
  }

  function decorateCells(table) {
    const cells = table.querySelectorAll('tbody td');
    cells.forEach((cell) => {
      const text = cell.textContent.trim();
      if (!text) {
        return;
      }
      cell.classList.add('andes-table__cell');
      cell.setAttribute('tabindex', '0');
      cell.setAttribute('data-andes-tooltip', text);

      const formattedNumber = formatNumber(text);
      if (formattedNumber !== null) {
        cell.classList.add('andes-table__cell--numeric');
        cell.textContent = formattedNumber;
        return;
      }

      const formattedDate = formatDate(text);
      if (formattedDate) {
        cell.textContent = formattedDate;
        return;
      }

      const chip = buildStatusChip(text);
      if (chip) {
        cell.textContent = '';
        cell.appendChild(chip);
      }
    });
  }

  function ensureShadows(container, scroller) {
    const update = () => {
      const { scrollLeft, scrollWidth, clientWidth } = scroller;
      if (scrollLeft > 2) {
        container.classList.add('andes-table--shadow-left');
      } else {
        container.classList.remove('andes-table--shadow-left');
      }
      if (scrollLeft + clientWidth < scrollWidth - 2) {
        container.classList.add('andes-table--shadow-right');
      } else {
        container.classList.remove('andes-table--shadow-right');
      }
    };
    update();
    scroller.addEventListener('scroll', update, { passive: true });
    window.addEventListener('resize', update);
  }

  function findScroller(container) {
    const candidates = Array.from(container.querySelectorAll('div'));
    return candidates.find((candidate) => {
      const style = window.getComputedStyle(candidate);
      if (!(style.overflowX === 'auto' || style.overflowX === 'scroll')) {
        return false;
      }
      return candidate.scrollWidth > candidate.clientWidth + 2;
    });
  }

  function enhanceTable(container) {
    if (!(container instanceof HTMLElement)) {
      return;
    }
    if (container.dataset.andesReady === 'true') {
      return;
    }
    container.dataset.andesReady = 'true';

    const variant = container.getAttribute('data-andes-variant') || 'andes';
    if (variant === 'unstyled') {
      return;
    }

    const table = container.querySelector('table');
    if (!table) {
      return;
    }

    const options = parseOptions(container);
    const headerCells = table.querySelectorAll('thead th');
    updateSortTooltips(headerCells);

    let actionsColumnIndex = -1;
    headerCells.forEach((header, index) => {
      const text = header.textContent.trim().toLowerCase();
      if (text === 'acciones') {
        actionsColumnIndex = index;
      }
    });

    decorateCells(table);

    if (options.hasActions && actionsColumnIndex >= 0) {
      enhanceActions(table, actionsColumnIndex);
    }

    const rows = table.querySelectorAll('tbody tr');
    applyHighlight(rows, options.highlightTopRows);

    const scroller = findScroller(container);
    if (scroller) {
      ensureShadows(container, scroller);
    }
  }

  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      mutation.addedNodes.forEach((node) => {
        if (!(node instanceof HTMLElement)) {
          return;
        }
        if (
          node.matches('[data-testid="stDataFrameResizable"], [data-testid="stTable"]')
        ) {
          enhanceTable(node);
        } else {
          const nested = node.querySelectorAll?.('[data-testid="stDataFrameResizable"], [data-testid="stTable"]');
          nested?.forEach((element) => enhanceTable(element));
        }
      });
    });
  });

  observer.observe(doc.body, { childList: true, subtree: true });

  doc.querySelectorAll('[data-testid="stDataFrameResizable"], [data-testid="stTable"]').forEach((element) => {
    enhanceTable(element);
  });
})();
