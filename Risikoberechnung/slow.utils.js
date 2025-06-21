export const randomIntFromInterval = (min, max) => Math.floor(Math.random() * (max - min + 1) + min);

export const slowDown = async (delayInMilliSeconds) =>
  new Promise((resolve) => setTimeout(resolve, delayInMilliSeconds));
