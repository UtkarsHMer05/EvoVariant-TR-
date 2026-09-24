/**
 * Run `build` or `dev` with `SKIP_ENV_VALIDATION` to skip env validation. This is especially useful
 * for Docker builds.
 */
import "./src/env.js";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "../..",
);

/** @type {import("next").NextConfig} */
const config = {
  reactStrictMode: false,
  // Pin the workspace root so a stray lockfile outside the repository cannot
  // change Turbopack's root inference.
  turbopack: {
    root: repoRoot,
  },
};

export default config;
