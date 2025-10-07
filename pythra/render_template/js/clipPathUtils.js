// clipPathUtils.js

/**
 * Parse an SVG path string containing absolute commands (M, L, A, H, V, Z),
 * and scale coordinates from reference dimensions to target dimensions.
 * 
 * @param {string} pathStr - Original SVG path string (absolute commands only)
 * @param {number} refW - reference width
 * @param {number} refH - reference height
 * @param {number} targetW - actual element width
 * @param {number} targetH - actual element height
 * @param {Object} [options] - optional settings:
 *    - {boolean} uniformArc
 *    - {number} decimalPlaces
 *    - {boolean} percentOutput
 * @returns {string} - scaled path string
 */
// clipPathUtils.js

export function scalePathAbsoluteMLA(pathStr, refW, refH, targetW, targetH, options = {}) {
  const rw = targetW / refW;
  const rh = targetH / refH;
  const uniformArc = !!options.uniformArc;
  const decimalPlaces = typeof options.decimalPlaces === 'number' ? options.decimalPlaces : null;
  const rScale = uniformArc ? Math.min(rw, rh) : null;

  const fmt = (num) => {
    return decimalPlaces !== null
      ? Number(num.toFixed(decimalPlaces)).toString()
      : Number(num).toString();
  };

  // Normalize the string
  const s = pathStr
    .replace(/,/g, ' ')
    .replace(/([0-9])-/g, '$1 -')
    .replace(/\s+/g, ' ')
    .trim();

  const tokenRegex = /([MLAZHV])|(-?\d*\.?\d+(?:e[-+]?\d+)?)/gi;
  const tokens = [];
  let match;
  while ((match = tokenRegex.exec(s)) !== null) {
    tokens.push(match[1] || match[2]);
  }

  const out = [];
  let i = 0;
  while (i < tokens.length) {
    const cmd = tokens[i++];
    out.push(cmd);

    switch (cmd) {
      case 'M':
      case 'L':
        while (i + 1 < tokens.length && !/^[MLAZHV]$/.test(tokens[i])) {
          const x = parseFloat(tokens[i++]) * rw;
          const y = parseFloat(tokens[i++]) * rh;
          out.push(fmt(x), fmt(y));
        }
        break;

      case 'A':
        while (i + 6 < tokens.length && !/^[MLAZHV]$/.test(tokens[i])) {
          const rx = parseFloat(tokens[i++]);
          const ry = parseFloat(tokens[i++]);
          const rot = tokens[i++];
          const laf = tokens[i++];
          const sf = tokens[i++];
          const x = parseFloat(tokens[i++]);
          const y = parseFloat(tokens[i++]);

          out.push(
            fmt(uniformArc ? rx * rScale : rx * rw),
            fmt(uniformArc ? ry * rScale : ry * rh),
            rot,
            laf,
            sf,
            fmt(x * rw),
            fmt(y * rh)
          );
        }
        break;

      case 'H':
        while (i < tokens.length && !/^[MLAZHV]$/.test(tokens[i])) {
          const x = parseFloat(tokens[i++]) * rw;
          out.push(fmt(x));
        }
        break;

      case 'V':
        while (i < tokens.length && !/^[MLAZHV]$/.test(tokens[i])) {
          const y = parseFloat(tokens[i++]) * rh;
          out.push(fmt(y));
        }
        break;

      case 'Z':
        // No coordinates to scale
        break;

      default:
        console.warn('Unsupported or unexpected token:', cmd);
    }
  }

  return out.join(' ');
}

export class ResponsiveClipPath {
  constructor(target, originalPath, refW, refH, options = {}) {
    this.elements = [];
    this.orig = originalPath.trim();
    this.refW = refW;
    this.refH = refH;
    this.options = options;
    this.currentPath = "";  // ⬅️ Store last computed path string
    this.update = this.update.bind(this);
    this.roList = [];

    if (typeof target === 'string') {
      let selector = target;
      if (!selector.startsWith('#') && !selector.startsWith('.')) {
        const byId = document.getElementById(selector);
        selector = byId ? `#${selector}` : `.${selector}`;
      }
      const nodeList = document.querySelectorAll(selector);
      if (nodeList.length === 0) {
        console.warn(`ResponsiveClipPath: no elements found for selector "${selector}"`);
      }
      nodeList.forEach(el => this.elements.push(el));
    } else if (target instanceof HTMLElement) {
      this.elements.push(target);
    } else {
      console.warn('ResponsiveClipPath: invalid target', target);
    }

    this.elements.forEach(el => this.initElement(el));
  }

  initElement(el) {
    this.applyClip(el);
    if (window.ResizeObserver) {
      const ro = new ResizeObserver(() => this.applyClip(el));
      ro.observe(el);
      this.roList.push({ el, ro });
    } else {
      window.addEventListener('resize', this.update);
    }
  }

  applyClip(el) {
    const rect = el.getBoundingClientRect();
    const newPath = scalePathAbsoluteMLA(
      this.orig,
      this.refW,
      this.refH,
      rect.width,
      rect.height,
      this.options
    );
    this.currentPath = `path("${newPath}")`;  // ⬅️ Save it
    el.style.clipPath = this.currentPath;
    el.style.webkitClipPath = this.currentPath;
  }

  update() {
    this.elements.forEach(el => this.applyClip(el));
  }

  disconnect() {
    this.roList.forEach(({ el, ro }) => ro.unobserve(el));
    this.roList = [];
    window.removeEventListener('resize', this.update);
  }

  // ✅ Your new method
  getResponsivePath() {
    return this.currentPath;
  }
}
