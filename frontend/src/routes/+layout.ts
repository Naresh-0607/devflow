// The app is a private, token-authenticated SPA on top of static assets.
// Rendering on the client avoids shipping an empty shell and lets route loads
// read the stale-while-revalidate cache before the network responds.
export const ssr = false;
export const prerender = false;
