import { createEnv } from "@t3-oss/env-nextjs";
import { z } from "zod";

export const env = createEnv({
  /**
   * Specify your server-side environment variables schema here. This way you can ensure the app
   * isn't built with invalid env vars.
   */
  server: {
    NODE_ENV: z.enum(["development", "test", "production"]),
    /**
     * Server-only scorer URL. Preferred over the legacy NEXT_PUBLIC_ variable
     * because the value is never needed in the browser bundle. Read at
     * runtime, so `next start` honours an override without a rebuild.
     */
    EVOVARIANT_SCORER_URL: z.string().url().optional(),
  },

  /**
   * Specify your client-side environment variables schema here. This way you can ensure the app
   * isn't built with invalid env vars. To expose them to the client, prefix them with
   * `NEXT_PUBLIC_`.
   */
  client: {
    /**
     * Legacy name, retained for existing local `.env.local` files and for
     * deployments that already bake this value at build time. Optional so a
     * build without a configured scorer still succeeds; routes answer 503.
     */
    NEXT_PUBLIC_ANALYZE_SINGLE_VARIANT_BASE_URL: z.string().url().optional(),
  },

  /**
   * You can't destruct `process.env` as a regular object in the Next.js edge runtimes (e.g.
   * middlewares) or client-side so we need to destruct manually.
   */
  runtimeEnv: {
    NODE_ENV: process.env.NODE_ENV,
    EVOVARIANT_SCORER_URL: process.env.EVOVARIANT_SCORER_URL,
    NEXT_PUBLIC_ANALYZE_SINGLE_VARIANT_BASE_URL:
      process.env.NEXT_PUBLIC_ANALYZE_SINGLE_VARIANT_BASE_URL,
  },
  /**
   * Run `build` or `dev` with `SKIP_ENV_VALIDATION` to skip env validation. This is especially
   * useful for Docker builds.
   */
  skipValidation: !!process.env.SKIP_ENV_VALIDATION,
  /**
   * Makes it so that empty strings are treated as undefined. `SOME_VAR: z.string()` and
   * `SOME_VAR=''` will throw an error.
   */
  emptyStringAsUndefined: true,
});
