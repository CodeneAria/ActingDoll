/**
 * Copyright(c) Live2D Inc. All rights reserved.
 *
 * Use of this source code is governed by the Live2D Open Software license
 * that can be found at https://www.live2d.com/eula/live2d-open-software-license-agreement_en.html.
 */

"use strict";
const fs = require('fs');
const publicResources = [
  { src: '../resources', dst: './../public/Resources' },
 // { src: '../Samples/Samples/Resources', dst: './public/Resources' },
  { src: '../controller', dst: './src' },
  { src: '../../Cubism/Core', dst: './../public/Core' }
];

publicResources.forEach((e)=>{if (fs.existsSync(e.dst)) fs.rmSync(e.dst, { recursive: true })});
publicResources.forEach((e)=>fs.cpSync(e.src, e.dst, {recursive: true}));
