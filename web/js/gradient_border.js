/**
 * PythraGradientClipPath: Client-side engine for creating an animated
 * gradient border around a complex clip-path shape.
 */
import { generateRoundedPath } from './pathGenerator.js';

// Helper function for basic vector math
const vec_gradient_border = (p1, p2) => ({ x: p2.x - p1.x, y: p2.y - p1.y });
const magnitude_gradient_border = (v) => Math.sqrt(v.x * v.x + v.y * v.y);
const normalize_gradient_border = (v) => {
    const mag = magnitude_gradient_border(v);
    return mag > 0 ? { x: v.x / mag, y: v.y / mag } : { x: 0, y: 0 };
};
const dot_gradient_border = (v1, v2) => v1.x * v2.x + v1.y * v2.y;
// const cross = (v1, v2) => v1.x * v2.y - v1.y * v2.x;



/**
 * Calculates a new set of points offset outwards from the original polygon.
 * @param {Array<Object>} points - The original points, e.g., [{x: 0, y: 0}, ...].
 * @param {number} offset - The distance to offset the points outwards.
 * @returns {Array<Object>} The new, offset points.
 */
function offsetPoints(points, offset) {
    const numPoints = points.length;
    if (numPoints < 3) return points;

    const offsetPoints = [];

    for (let i = 0; i < numPoints; i++) {
        const p_prev = points[(i + numPoints - 1) % numPoints];
        const p_curr = points[i];
        const p_next = points[(i + 1) % numPoints];

        const v1 = normalize_gradient_border(vec_gradient_border(p_curr, p_prev));
        const v2 = normalize_gradient_border(vec_gradient_border(p_curr, p_next));

        // Calculate the angle bisector vector (points outwards for convex shapes)
        const bisector = normalize_gradient_border({ x: v1.x + v2.x, y: v1.y + v2.y });

        // Calculate the angle between the two edge vectors
        const angle = Math.acos(dot_gradient_border(v1, v2));

        // Use trigonometry to find the length to move along the bisector
        // to achieve the desired perpendicular offset distance.
        const distance = offset / Math.sin(angle / 2);

        if (isNaN(distance) || !isFinite(distance)) {
             // Handle collinear points (angle is ~PI), just move along the normal
             const normal = { x: -v1.y, y: v1.x };
             offsetPoints.push({ x: p_curr.x + normal.x * offset, y: p_curr.y + normal.y * offset });
        } else {
             offsetPoints.push({ x: p_curr.x + bisector.x * distance, y: p_curr.y + bisector.y * distance });
        }
    }
    return offsetPoints;
}


export class PythraGradientClipPath {
    constructor(elementId, options) {
        this.container = document.getElementById(elementId);
        if (!this.container) {
            console.error(`GradientClipPath container with ID #${elementId} not found.`);
            return;
        }

        console.log(`✅ PythraGradientClipPath engine is initializing for #${elementId}`);
        
        // --- Setup DOM Structure ---
        // The reconciler placed the child widget inside our container.
        // We need to wrap it and add a background element.
        this.backgroundEl = document.createElement('div');
        this.backgroundEl.className = 'gradient-clip-background';
        
        this.contentHost = document.createElement('div');
        this.contentHost.className = 'gradient-clip-content-host';

        // Move the original child from the container into the new host
        while (this.container.firstChild) {
            this.contentHost.appendChild(this.container.firstChild);
        }
        
        this.container.appendChild(this.backgroundEl);
        this.container.appendChild(this.contentHost);
        
        // --- Generate and Apply Paths ---
        this.options = options;
        this.update = this.update.bind(this);
        
        // Use a ResizeObserver to make it fully responsive
        this.ro = new ResizeObserver(this.update);
        this.ro.observe(this.container);
        
        // Initial update
        this.update();
    }

    update() {
        const rect = this.container.getBoundingClientRect();
        if (rect.width === 0 || rect.height === 0) return;

        const { points, radius, viewBox, borderWidth } = this.options;
        const jsPoints = points.map(p => ({ x: p[0], y: p[1] }));

        // 1. Generate the inner path for the content
        const innerPathStr = generateRoundedPath(jsPoints, radius);
        const innerClipPath = `path("${innerPathStr}")`;

        // 2. Calculate offset points and a larger radius for the outer path
        const offset_points = offsetPoints(jsPoints, borderWidth);
        const outerRadius = radius + borderWidth;
        const outerPathStr = generateRoundedPath(offset_points, outerRadius);
        const outerClipPath = `path("${outerPathStr}")`;

        // 3. Apply the responsive clip-paths to the elements
        // We don't need ResponsiveClipPath class here because we update on every resize.
        this.contentHost.style.clipPath = innerClipPath;
        this.contentHost.style.webkitClipPath = innerClipPath;
        
        this.backgroundEl.style.clipPath = outerClipPath;
        this.backgroundEl.style.webkitClipPath = outerClipPath;
    }

    destroy() {
        if (this.ro && this.container) {
            this.ro.unobserve(this.container);
        }
    }
}