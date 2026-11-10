/**
 * Small, dependency-free markdown renderer for chat answers.
 *
 * Everything is HTML-escaped before formatting is applied, so model output
 * (and the untrusted commit messages it may quote) can never inject markup.
 */

function escapeHtml(value: string): string {
	return value
		.replaceAll('&', '&amp;')
		.replaceAll('<', '&lt;')
		.replaceAll('>', '&gt;')
		.replaceAll('"', '&quot;')
		.replaceAll("'", '&#39;');
}

function renderInline(value: string): string {
	const codes: string[] = [];
	let text = value.replace(/`([^`\n]+)`/g, (_match, code: string) => {
		codes.push(`<code>${code}</code>`);
		return `\u0000${codes.length - 1}\u0000`;
	});

	text = text
		.replace(/\*\*([^*\n]+)\*\*/g, '<strong>$1</strong>')
		.replace(/(^|[^*])\*([^*\n]+)\*/g, '$1<em>$2</em>')
		.replace(/_([^_\n]+)_/g, '<em>$1</em>')
		.replace(
			/\[([^\]]+)\]\((https?:\/\/[^\s)]+|\/[^\s)]*)\)/g,
			'<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>'
		);

	return text.replace(/\u0000(\d+)\u0000/g, (_match, index: string) => codes[Number(index)] ?? '');
}

function renderBlocks(text: string): string {
	const lines = text.split('\n');
	const out: string[] = [];
	let paragraph: string[] = [];
	let list: { type: 'ul' | 'ol'; items: string[] } | null = null;

	const flushParagraph = () => {
		if (!paragraph.length) return;
		out.push(`<p>${paragraph.map(renderInline).join('<br>')}</p>`);
		paragraph = [];
	};
	const flushList = () => {
		if (!list) return;
		out.push(
			`<${list.type}>${list.items.map((item) => `<li>${renderInline(item)}</li>`).join('')}</${list.type}>`
		);
		list = null;
	};

	for (const line of lines) {
		const trimmed = line.trim();

		if (!trimmed) {
			flushParagraph();
			flushList();
			continue;
		}

		const heading = /^(#{1,3})\s+(.*)$/.exec(trimmed);
		if (heading) {
			flushParagraph();
			flushList();
			const level = heading[1].length;
			out.push(`<h${level}>${renderInline(heading[2])}</h${level}>`);
			continue;
		}

		if (/^(-{3,}|\*{3,})$/.test(trimmed)) {
			flushParagraph();
			flushList();
			out.push('<hr>');
			continue;
		}

		const quote = /^>\s?(.*)$/.exec(trimmed);
		if (quote) {
			flushParagraph();
			flushList();
			out.push(`<blockquote>${renderInline(quote[1])}</blockquote>`);
			continue;
		}

		const bullet = /^[-*+]\s+(.*)$/.exec(trimmed);
		if (bullet) {
			flushParagraph();
			if (list?.type !== 'ul') {
				flushList();
				list = { type: 'ul', items: [] };
			}
			list.items.push(bullet[1]);
			continue;
		}

		const ordered = /^\d+[.)]\s+(.*)$/.exec(trimmed);
		if (ordered) {
			flushParagraph();
			if (list?.type !== 'ol') {
				flushList();
				list = { type: 'ol', items: [] };
			}
			list.items.push(ordered[1]);
			continue;
		}

		flushList();
		paragraph.push(line);
	}

	flushParagraph();
	flushList();
	return out.join('');
}

export function renderMarkdown(source: string): string {
	const escaped = escapeHtml(source.replace(/\r\n?/g, '\n'));
	const parts = escaped.split('```');

	return parts
		.map((part, index) => {
			if (index % 2 === 1) {
				const body = part.replace(/^[a-zA-Z0-9_+-]*\n?/, '');
				return `<pre><code>${body.replace(/\n$/, '')}</code></pre>`;
			}
			return renderBlocks(part);
		})
		.join('');
}
