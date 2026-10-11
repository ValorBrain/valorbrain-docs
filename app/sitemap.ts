import { execFileSync, type ExecFileSyncOptionsWithStringEncoding } from 'node:child_process';
import type { MetadataRoute } from 'next';
import { getPageAlternates, getPageSourcePath, source } from '@/lib/source';
import { SITE_URL } from '@/lib/shared';

export const dynamic = 'force-static';

const HOME_SOURCE = 'app/(home)/page.tsx';
const GIT_PATHS = ['--', 'content/docs', HOME_SOURCE];
const GIT_OPTIONS: ExecFileSyncOptionsWithStringEncoding = { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] };

/**
 * Last commit date per file, from one `git log` walk (newest first, so the
 * first date seen for a path is its last change). Files the build rewrote
 * (generated reference pages differ from HEAD) get the build time instead.
 * Outside a git checkout the map is empty and `lastModified` is omitted.
 */
function lastModifiedByFile(): Map<string, Date> {
  const dates = new Map<string, Date>();
  try {
    const log = execFileSync('git', ['log', '--format=%x00%cI', '--name-only', ...GIT_PATHS], GIT_OPTIONS);
    let current: Date | undefined;
    for (const line of log.split('\n')) {
      if (line.startsWith('\0')) current = new Date(line.slice(1));
      else if (line && current && !dates.has(line)) dates.set(line, current);
    }
    const built = new Date();
    const status = execFileSync('git', ['status', '--porcelain', ...GIT_PATHS], GIT_OPTIONS);
    for (const line of status.split('\n')) {
      if (line.length > 3) dates.set(line.slice(3), built);
    }
  } catch {
    dates.clear();
  }
  return dates;
}

export default function sitemap(): MetadataRoute.Sitemap {
  const modified = lastModifiedByFile();
  const pages = source.getLanguages().flatMap(({ pages: localePages }) =>
    localePages.map((page) => ({
      url: SITE_URL + page.url,
      lastModified: modified.get(getPageSourcePath(page)),
      alternates: {
        languages: Object.fromEntries(
          Object.entries(getPageAlternates(page)).map(([lang, url]) => [lang, SITE_URL + url]),
        ),
      },
    })),
  );
  pages.sort((a, b) => a.url.localeCompare(b.url));
  return [{ url: `${SITE_URL}/`, lastModified: modified.get(HOME_SOURCE) }, ...pages];
}
