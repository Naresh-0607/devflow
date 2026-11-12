// @ts-nocheck
import fs from 'fs';
import path from 'path';
import adapter from '@sveltejs/adapter-cloudflare';
import { sveltekit } from '@sveltejs/kit/vite';
import { Scanner } from '@tailwindcss/oxide';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';

// When Windows Application Control or WASI blocks Oxide from walking the filesystem,
// fall back to reading source files via Node fs and passing contents to Scanner.scanFiles().
const originalScan = Scanner.prototype.scan;
Scanner.prototype.scan = function () {
	const result = originalScan.call(this);
	if (result.length > 0) return result;

	const candidates = new Set<string>();
	const root = path.resolve('src');
	function walk(this: any, dir: string) {
		for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
			const full = path.join(dir, entry.name);
			if (entry.isDirectory()) {
				walk.call(this, full);
			} else if (/\.(svelte|html|ts|js)$/.test(entry.name)) {
				const content = fs.readFileSync(full, 'utf8');
				const ext = path.extname(entry.name).slice(1);
				for (const c of this.scanFiles([{ content, extension: ext }])) {
					candidates.add(c);
				}
			}
		}
	}
	walk.call(this, root);
	return Array.from(candidates);
};

export default defineConfig(({ command }) => ({
	plugins: [
		tailwindcss(),
		sveltekit({
			compilerOptions: {
				// Force runes mode for the project, except for libraries.
				runes: ({ filename }) =>
					filename.split(/[/\\]/).includes('node_modules') ? undefined : true
			},
			// The Cloudflare adapter's dev integration spawns workerd.exe (via wrangler/
			// miniflare), which Windows Application Control blocks on this machine.
			// The app talks to the FastAPI backend over HTTP and needs no Cloudflare
			// bindings in dev, so the adapter is only loaded for actual builds.
			adapter: command === 'build' ? adapter() : undefined
		})
	]
}));
