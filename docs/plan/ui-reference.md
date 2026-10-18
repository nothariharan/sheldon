# UI reference

Fetched 18 Oct 2026 from the live pages and their stylesheets. This note is layout and motion, not a copy of either site. Do not reuse their sentences, counts, quotes, images, or code.

## t3.codes

Astro page. The document title is the product name.

The page is near-black. The stylesheet sets the page background to `#09090b`, a raised surface to `#0c0c0e`, cards to `#111113`, text to `#fafafa`, muted text to `#a1a1aa`, and dim text to `#71717a`. Borders are white at a low alpha. The accent is an `oklch` color with hue 250. A green (`oklch` hue 150) and an amber (`oklch` hue 75) sit beside it. UI type is DM Sans. The terminal mock uses JetBrains Mono.

The nav is a brand mark, a Download link, and a GitHub link that shows a star badge. It sticks, and a scrolled class changes it.

The hero is one short centered headline (`clamp` from 38px to 76px, about 20 characters wide) and a muted subtitle capped near 640px. The primary button is a macOS download. A second action links to the source. iOS and Android are smaller links under that. A large desktop screenshot sits under the headline (webp, srcset up to 2880 wide). On a narrow viewport the screenshot is not requested. Floating cards for harness names drift around the hero.

Motion in the stylesheet: fade-in, rise, a mark that enters and then drifts, a long marquee, and a caret that blinks. `prefers-reduced-motion: reduce` turns the float animation off.

Sections after the hero, in order: a moving strip of short endorsements, a list of harness names with the login command for each, a fake commit card (branch line, files, added and removed counts), one section about a single commit-and-PR action, a terminal mock, and a closing download. The terminal mock has traffic-light dots, a title bar, a prompt line, dim check lines, an accent-colored URL, and a blinking caret. The download button appears again at the bottom. Footer links include the source, Discord, download, the phone apps, terms, privacy, and security.

What makes it feel like a product: one job in the hero, the product UI immediately under that sentence, motion that shows the product rather than decoration alone, the same download action repeated, and the source repo in the nav.

## usewsp.com

Tailwind page. The document title is one sentence about the product.

The palette is warm, not pure gray. Background `#121110`, foreground `#ece6dc`, muted text `#9c9288`, border `#2a2623`. The primary button uses the cream foreground on a near-black fill. Green `#8fbf87` and amber `#f59e0b` appear in the stylesheet. Type is Inter Variable. Mono is Geist Mono Variable.

The nav is 64px tall, capped at 1200px. The logo is an inline SVG wordmark. Links: Docs, Compare (hidden when the viewport is narrow), GitHub, and Download. Link color moves from muted to foreground over about 150ms.

The hero preloads a product screenshot (srcset 800, 1440, and 2880) over a wall image. The headline is one sentence. A short line names the agents the product runs, then a Mac download and a Linux download. The secondary action is styled like a keycap.

The product is shown as screenshots of the app, one behavior per section: agents handing work across computers, a computer added over SSH with the setup coming along, a small app beside the thread, then separate panes for a terminal (using the person's own terminal colors), an editor, a pull request, an agent list, and a browser. A compare section links to other products. A questions section follows. The closing line repeats the download. The footer has Docs, Compare, GitHub, X, privacy, terms, security, and an email.

Motion: a stroke-dash `trace` and a `rise` (opacity plus a 10px upward move). `prefers-reduced-motion: reduce` turns `rise` off. Floating panels use a large shadow (`0 30px 80px`).

What makes it feel like a product: the app is the hero image, each section states one behavior and shows that behavior, Docs is a nav item, and the download is repeated. Copy stays short.

## What we borrow for Sheldon

- A dark page and one-sentence hero. The sentence is the README lock line, not a new slogan.
- Show the product working on the opening screen. For Sheldon that is an animated replay of CLI output recorded against the seed, not a terminal with invented commands.
- Short sections. Each one is one behavior: the retry block, the evidence gate, the refute plus stale cascade.
- Repeat the install command and the public repo link. Put the spec, or the repo, in the nav.
- Mono for command output. One accent for the page, and separate colors for blocked, passed, and stale.
- Honor `prefers-reduced-motion`: show the finished transcript instead of typing it out.
- Do not add a compare page. Do not use their quotes, counts, assets, or sentences.
