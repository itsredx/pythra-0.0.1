// js/pathGenerator.js

// --- Vector Math Helper Functions ---
const vec = (p1, p2) => ({ x: p2.x - p1.x, y: p2.y - p1.y });
const magnitude = (v) => Math.sqrt(v.x ** 2 + v.y ** 2);
const dot = (v1, v2) => v1.x * v2.x + v1.y * v2.y;
const cross = (v1, v2) => v1.x * v2.y - v1.y * v2.x;
const round = (val) => Math.round(val * 100) / 100; // Round to 2 decimal places

export function generateRoundedPath(points, radius) {
    const numPoints = points.length;
    const cornerData = [];

    console.log(`>>>>>> Generator Initiated <<<<<<`)

    for (let i = 0; i < numPoints; i++) {
        const p_prev = points[(i + numPoints - 1) % numPoints];
        const p_curr = points[i];
        const p_next = points[(i + 1) % numPoints];

        const v1 = vec(p_curr, p_prev);
        const v2 = vec(p_curr, p_next);
        const v1_mag = magnitude(v1);
        const v2_mag = magnitude(v2);

        if (v1_mag === 0 || v2_mag === 0) {
            cornerData.push({ t1: p_curr, t2: p_curr, radius: 0 });
            continue;
        }

        const angle = Math.acos(Math.max(-1, Math.min(1, dot(v1, v2) / (v1_mag * v2_mag))));
        let tangentDist = radius / Math.tan(angle / 2);
        tangentDist = Math.min(tangentDist, v1_mag / 2, v2_mag / 2);
        const clampedRadius = Math.abs(tangentDist * Math.tan(angle / 2));

        const t1 = { x: p_curr.x + (v1.x / v1_mag) * tangentDist, y: p_curr.y + (v1.y / v1_mag) * tangentDist };
        const t2 = { x: p_curr.x + (v2.x / v2_mag) * tangentDist, y: p_curr.y + (v2.y / v2_mag) * tangentDist };

        const sweepFlag = cross(v1, v2) < 0 ? 1 : 0;

        cornerData.push({ t1, t2, radius: clampedRadius, sweepFlag });
    }

    const pathCommands = [];
    pathCommands.push(`M ${round(cornerData[numPoints - 1].t2.x)} ${round(cornerData[numPoints - 1].t2.y)}`);
    for (let i = 0; i < numPoints; i++) {
        const corner = cornerData[i];
        pathCommands.push(`L ${round(corner.t1.x)} ${round(corner.t1.y)}`);
        pathCommands.push(`A ${round(corner.radius)} ${round(corner.radius)} 0 0 ${corner.sweepFlag} ${round(corner.t2.x)} ${round(corner.t2.y)}`);
    }
    pathCommands.push('Z');
    console.log(pathCommands.join(' '));
    return pathCommands.join(' ');
}
