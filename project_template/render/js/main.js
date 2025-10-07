import { ResponsiveClipPath } from './clipPathUtils.js';


// List of 10 test paths (reference coordinate space is 200×200)
// Make sure each string is trimmed and matches absolute M/L/A/Z commands for a 200x200 design.
const paths = [
  // `M 0,0 L 200,0 L 200,200 L 0,200 Z`,
  // `M 20,0 L 180,0 A 20,20 0 0,1 200,20 L 200,180 A 20,20 0 0,1 180,200 L 20,200 A 20,20 0 0,1 0,180 L 0,20 A 20,20 0 0,1 20,0 Z`,
  // `M 50,0 L 150,0 L 200,100 L 150,200 L 50,200 L 0,100 Z`,
  // `M 100,0 A 100,100 0 0,1 0,100 A 100,100 0 0,1 100,200 A 100,100 0 0,1 200,100 A 100,100 0 0,1 100,0 Z`,
  // `M 0,100 A 100,100 0 0,1 100,200 L 200,200 L 200,0 L 100,0 A 100,100 0 0,1 0,100 Z`,
  // `M 10,50 L 90,50 A 10,10 0,0,0 100,40 L 100,10 A 10,10 0,0,1 110,0 L 190,0 A 10,10 0,0,1 200,10 L 200,190 A 10,10 0,0,1 190,200 L 10,200 A 10,10 0,0,1 0,190 L 0,60 A 10,10 0,0,1 10,50 Z`,
  // `M 0,20 A 20,20 0 0,1 20,0 L 180,0 A 20,20 0 0,1 200,20 L 200,180 A 20,20 0 0,1 180,200 L 20,200 A 20,20 0 0,1 0,180 Z`,
  // `M 50,0 L 150,0 A 25,25 0 0,1 175,25 L 175,175 A 25,25 0 0,1 150,200 L 50,200 A 25,25 0 0,1 25,175 L 25,25 A 25,25 0 0,1 50,0 Z`,
  // `M 0,0 L 200,0 L 200,200 A 20,20 0 0,1 180,180 L 20,180 A 20,20 0 0,1 0,200 Z`,
  // `M 30,0 L 170,0 A 30,30 0 0,1 200,30 L 200,170 A 30,30 0 0,1 170,200 L 30,200 A 30,30 0 0,1 0,170 L 0,30 A 30,30 0 0,1 30,0 Z`,
  // `M 20 0 L346 0 A20 20 0 0 1 366 20 L366 272 A20 20 0 0 1 346 292 L20 292 A20 20 0 0 1 0 272 L0 20 A20 20 0 0 1 20 0 Z`,
  `M 100 83 L 100 67 A 17 17 0 0 1 117 50 L 183 50 A 17 17 0 0 1 200 67 L 200 83 A 17 17 0 0 0 217 100 L 233 100 A 17 17 0 0 1 250 117 L 250 183 A 17 17 0 0 1 233 200 L 217 200 A 17 17 0 0 0 200 217 L 200 233 A 17 17 0 0 1 183 250 L 117 250 A 17 17 0 0 1 100 233 L 100 217 A 17 17 0 0 0 83 200 L 67 200 A 17 17 0 0 1 50 183 L 50 117 A 17 17 0 0 1 67 100 L 83 100 A 17 17 0 0 0 100 83 Z`,
].map(str => str.trim());

const refW = 400;
const refH = 400;

const box = document.querySelector('.box');

// Instantiate with the first path:
let currentIndex = 0;
const options = { uniformArc: false, decimalPlaces: 2 };
const rc = new ResponsiveClipPath(box, paths[currentIndex], refW, refH, options);

// Swap to next path every 2 seconds:
setInterval(() => {
  currentIndex = (currentIndex + 1) % paths.length;
  // Update the ResponsiveClipPath instance:
  rc.orig = paths[currentIndex];  // override the stored original path
  rc.update();                    // re-calculate & apply new clip-path
}, 2000);
