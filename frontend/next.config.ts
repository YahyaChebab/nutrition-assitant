import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  // Note: Next.js may show a warning about multiple lockfiles if package-lock.json
  // exists in parent directories. This warning is harmless and doesn't affect functionality.
  // Next.js will correctly use the lockfile in the frontend directory.
  // The turbopack.root option is not available in Next.js 16.0.1, so we can't suppress
  // this warning via config. It's safe to ignore.

  turbopack: {
    root: __dirname,
  },
};

export default nextConfig;
