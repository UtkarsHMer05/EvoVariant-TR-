/**
 * Run `build` or `dev` with `SKIP_ENV_VALIDATION` to skip env validation. This is especially useful
 * for Docker builds.
 */
import "./src/env.js";

/** @type {import("next").NextConfig} */
const config = {
  reactStrictMode: false,
  eslint: {
    // ESLint runs as an explicit pre-build step in the repository Makefile.
    // Next skips duplicate build-time linting so production builds stay focused
    // on compilation and type validity.
    ignoreDuringBuilds: true,
  },
};

export default config;
