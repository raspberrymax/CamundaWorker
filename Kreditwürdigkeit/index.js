import express from 'express';
import jsonServer from 'json-server';
import { randomIntFromInterval, slowDown } from './slow.utils.js';
import commandLineArgs from 'command-line-args';
import { fileURLToPath } from 'url';
import path from 'path';

const server = express();

const optionDefinitions = [
  { name: 'port', alias: 'v', type: Number, multiple: false, defaultValue: 3000 },
  { name: 'data', alias: 'd', type: String, multiple: false, defaultValue: './server/db.json' },
  { name: 'minRequestTime', type: Number, multiple: false, defaultValue: 200 },
  { name: 'maxRequestTime', type: Number, multiple: false, defaultValue: 2000 },
];

const options = commandLineArgs(optionDefinitions);

server.use(async (req, res, next) => {
  const delay = randomIntFromInterval(options.minRequestTime, options.maxRequestTime);
  await slowDown(delay);
  next();
});

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

server.use(jsonServer.router(path.join(__dirname, options.data)));

server.listen(options.port, () => {
  console.log(`JSON Server is running on Port ${options.port}`);
});
