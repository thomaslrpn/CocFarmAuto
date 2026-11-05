import type { ReactNode } from "react";

/**
 * Affiche du Markdown simple (CHANGELOG.md, notes de version) : titres ## / ###,
 * listes « - », paragraphes. Pas de bibliothèque : le contenu est simple et maîtrisé.
 */
export function Changelog({ markdown }: { markdown: string }) {
  const blocks: ReactNode[] = [];
  let list: string[] = [];
  let paragraph: string[] = []; // lignes de texte consécutives = un seul paragraphe
  const flush = () => {
    if (paragraph.length) {
      blocks.push(<p key={`p${blocks.length}`} className="mb-2 text-sm text-ink-muted">{paragraph.join(" ")}</p>);
      paragraph = [];
    }
    if (list.length) {
      blocks.push(
        <ul key={`l${blocks.length}`} className="mb-3 list-disc space-y-1 pl-5 text-sm text-ink-secondary">
          {list.map((item) => <li key={item}>{item}</li>)}
        </ul>,
      );
      list = [];
    }
  };
  for (const raw of markdown.split(/\r?\n/)) {
    const line = raw.trim();
    if (line.startsWith("- ")) { list.push(line.slice(2)); continue; }
    if (line && !line.startsWith("#")) { paragraph.push(line); continue; }
    flush();
    if (!line || line.startsWith("# ")) continue; // le titre principal est déjà celui de la carte
    if (line.startsWith("## ")) blocks.push(<h3 key={blocks.length} className="mb-2 mt-4 text-base font-semibold first:mt-0">{line.slice(3)}</h3>);
    else if (line.startsWith("### ")) blocks.push(<h4 key={blocks.length} className="mb-1 mt-3 text-sm font-medium">{line.slice(4)}</h4>);
  }
  flush();
  return <div>{blocks}</div>;
}
