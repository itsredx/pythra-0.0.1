// js/pathGeneratorUI.js
import { generateRoundedPath } from './pathGenerator.js';
import { ResponsiveClipPath } from './clipPathUtils.js';

export function setupPathGeneratorUI() {
    const pointsInput = document.getElementById('points-input');
    const radiusInput = document.getElementById('radius');
    const radiusValue = document.getElementById('radius-value');
    const cssOutput = document.getElementById('css-output');
    const responsiveOutput = document.getElementById('responsive-output');
    const previewDiv = document.getElementById('preview');
    const canvas = document.getElementById('visualizer');
    const ctx = canvas.getContext('2d');

    let rc = null;

    radiusInput.oninput = () => {
        radiusValue.textContent = radiusInput.value;
        runGenerator();
    };
    pointsInput.oninput = runGenerator;

    document.getElementById('generate').addEventListener('click', runGenerator);


    function runGenerator() {
        try {
            const points = pointsInput.value.trim().split('\n').map(line => {
                const [x, y] = line.split(',').map(Number);
                return { x, y };
            }).filter(p => !isNaN(p.x) && !isNaN(p.y));

            if (points.length < 3) throw new Error("Please provide at least 3 valid points.");

            const radius = parseFloat(radiusInput.value);
            const pathString = generateRoundedPath(points, radius);
            const clipPathValue = `path('${pathString}')`;

            cssOutput.value = clipPathValue;
            // cssOutput.select();
            previewDiv.style.clipPath = clipPathValue;

            // Make it responsive:
            if (!rc) {
                rc = new ResponsiveClipPath(previewDiv, pathString, 300, 300);
                // Later, get the responsive path:
                // console.log(rc.getResponsivePath());
                
            } else {
                rc.orig = pathString;

                rc.update();
                responsiveOutput.value = rc.getResponsivePath();
            }

            drawVisualizer(points, pathString);
        } catch (e) {
            cssOutput.value = e.message;
            previewDiv.style.clipPath = 'none';
        }
    }

    function drawVisualizer(points, pathString) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.beginPath();
        ctx.moveTo(points[0].x, points[0].y);
        points.slice(1).forEach(p => ctx.lineTo(p.x, p.y));
        ctx.closePath();
        ctx.strokeStyle = 'rgba(255, 0, 0, 0.5)';
        ctx.lineWidth = 1;
        ctx.stroke();

        const path2d = new Path2D(pathString);
        ctx.strokeStyle = 'blue';
        ctx.lineWidth = 2;
        ctx.stroke(path2d);
    }

    window.onload = runGenerator;
}
