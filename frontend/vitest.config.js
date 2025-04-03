/// <reference types="vitest" />
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'jsdom', // or 'node' depending on your needs
    setupFiles: ['./vitest.setup.js'], // if you have any global setup
  },
});
